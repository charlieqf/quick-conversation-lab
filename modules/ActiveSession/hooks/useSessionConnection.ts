
import { useState, useRef, useEffect, useCallback } from 'react';
import { SessionConfig, ConnectionState } from '../types';
import { LogEntry, Scenario, Role, SessionReportData, ChatMessage } from '../../../types';
import { DEFAULT_SESSION_CONFIG } from '../constants';
import { AudioStreamer } from '../services/AudioStreamer';
import { VoiceSocket } from '../services/VoiceSocket';

// Helpers
const float32ToInt16 = (float32: Float32Array) => {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return int16;
};

const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
};

export const useSessionConnection = (scenarioId: string, roleId: string) => {
  const [status, setStatus] = useState<ConnectionState>('disconnected');
  // Initialize with 24000 Hz for Gemini
  const [config, setConfig] = useState<SessionConfig>({
    ...DEFAULT_SESSION_CONFIG,
    sampleRate: 24000
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [volume, setVolume] = useState(0);

  // Session Data
  const startTimeRef = useRef<number>(0);
  const sessionDataRef = useRef<{ id: string }>({ id: Date.now().toString() });

  // Transcription Storage
  const transcriptHistoryRef = useRef<ChatMessage[]>([]);
  const currentTurnRef = useRef<{ user: string, model: string }>({ user: '', model: '' });

  // Refs
  const streamerRef = useRef<AudioStreamer | null>(null);
  const socketRef = useRef<VoiceSocket | null>(null);
  const audioBufferQueue = useRef<Int16Array[]>([]);
  const nextPlayTime = useRef<number>(0);

  // Logging Helper
  const log = useCallback((msg: string, type: 'info' | 'error' | 'stream' = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => {
      // Limit to latest 100 entries
      const newLogs = [...prev, { timestamp: time, message: msg, type }];
      if (newLogs.length > 100) {
        return newLogs.slice(newLogs.length - 100);
      }
      return newLogs;
    });
  }, []);

  // Visualizer Loop
  useEffect(() => {
    let interval: any;
    if (status === 'connected') {
      interval = setInterval(() => {
        if (streamerRef.current) {
          const v = streamerRef.current.getVolume();
          setVolume(v);
        }
      }, 50);
    } else {
      setVolume(0);
    }
    return () => clearInterval(interval);
  }, [status]);

  // Data Fetching Helper
  const getContextData = () => {
    try {
      const scenarios: Scenario[] = JSON.parse(localStorage.getItem('quick_scenarios') || '[]');
      const roles: Role[] = JSON.parse(localStorage.getItem('quick_roles') || '[]');
      const scenario = scenarios.find(s => s.id === scenarioId);
      const role = roles.find(r => r.id === roleId);
      return { scenario, role };
    } catch (e) {
      log('Error loading context data from storage', 'error');
      return { scenario: undefined, role: undefined };
    }
  };

  // Connect Logic
  const connect = async () => {
    if (status === 'connected' || status === 'connecting') return;

    setStatus('connecting');
    log('Initializing Session...', 'info');
    startTimeRef.current = Date.now();
    sessionDataRef.current = { id: Date.now().toString() };
    transcriptHistoryRef.current = []; // Clear history
    currentTurnRef.current = { user: '', model: '' };

    // 0. Load Context
    const { scenario, role } = getContextData();
    if (!scenario || !role) {
      setStatus('error');
      log('Failed to load Scenario or Role data.', 'error');
      return;
    }

    const systemInstruction = `
You are ${role.nameCN} (${role.name}), a ${role.title}.
Your description: "${role.description}".
Personality: Hostility=${role.hostility}/100, Verbosity=${role.verbosity}/100, Skepticism=${role.skepticism}/100.
System Addon: ${role.systemPromptAddon || ''}

Current Scenario: ${scenario.subtitle}
Description: ${scenario.description}
Workflow: ${scenario.workflow}
Knowledge Points: ${scenario.knowledgePoints}

Your goal: Act as the patient/colleague in this medical simulation. Interact naturally via voice. 
Do not break character. Speak Chinese.
    `.trim();

    log(`Context Loaded: ${role.nameCN} in ${scenario.subtitle}`, 'info');

    try {
      // 1. Init Streamer
      const streamer = new AudioStreamer(
        (pcmFloat32) => {
          // On Microphone Data
          const int16 = float32ToInt16(pcmFloat32);

          audioBufferQueue.current.push(int16);

          if (audioBufferQueue.current.length >= config.bufferThreshold) {
            if (socketRef.current) {
              const totalLen = audioBufferQueue.current.reduce((acc, b) => acc + b.length, 0);
              const merged = new Int16Array(totalLen);
              let offset = 0;
              for (const b of audioBufferQueue.current) {
                merged.set(b, offset);
                offset += b.length;
              }
              const b64 = arrayBufferToBase64(merged.buffer);
              socketRef.current.sendAudioChunk(b64);
            }
            audioBufferQueue.current = [];
          }
        },
        (msg, type) => log(msg, type as any)
      );

      streamerRef.current = streamer;
      await streamer.start(config.sampleRate);

      // 2. Init Socket
      // API Key is now handled by backend
      // const apiKey = process.env.API_KEY || ''; 

      const socket = new VoiceSocket(
        "gemini", // Hardcoded model ID for now, should come from selection
        (msg, type) => log(msg, type),
        (b64) => playAudioChunk(b64),
        (role, text) => {
          if (role === 'system' && text === 'TURN_COMPLETE') {
            // Flush accumulated text to history
            const { user, model } = currentTurnRef.current;
            const now = Date.now();

            if (user.trim()) {
              transcriptHistoryRef.current.push({
                id: `${now}_u`,
                role: 'user',
                type: 'text',
                content: user.trim()
              });
              log(`Transcript [User]: ${user.substring(0, 30)}...`, 'info');
            }

            if (model.trim()) {
              transcriptHistoryRef.current.push({
                id: `${now}_m`,
                role: 'model',
                type: 'text',
                content: model.trim()
              });
              log(`Transcript [Model]: ${model.substring(0, 30)}...`, 'info');
            }

            currentTurnRef.current = { user: '', model: '' };
          } else if (role === 'user') {
            currentTurnRef.current.user += text;
          } else if (role === 'model') {
            currentTurnRef.current.model += text;
          }
        },
        (err) => {
          setStatus('error');
          log(`Socket Error: ${err}`, 'error');
        }
      );

      socketRef.current = socket;
      socket.connect(config, systemInstruction);

      setStatus('connected');

      // Initialize playback time
      const ctx = streamer.getContext();
      if (ctx) nextPlayTime.current = ctx.currentTime;

    } catch (e: any) {
      setStatus('error');
      log(`Connection Failed: ${e.message}`, 'error');
      disconnect();
    }
  };

  const playAudioChunk = (base64: string) => {
    const streamer = streamerRef.current;
    if (!streamer) return;
    const ctx = streamer.getContext();
    if (!ctx) return;

    try {
      const binaryString = window.atob(base64);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const inputData = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        float32[i] = inputData[i] / 32768.0;
      }

      const buffer = ctx.createBuffer(1, float32.length, config.sampleRate);
      buffer.getChannelData(0).set(float32);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);

      const now = ctx.currentTime;
      const startTime = Math.max(now, nextPlayTime.current);

      source.start(startTime);
      nextPlayTime.current = startTime + buffer.duration;

    } catch (e: any) {
      log(`Playback error: ${e.message}`, 'error');
    }
  };

  const disconnect = () => {
    if (streamerRef.current) streamerRef.current.stop();
    if (socketRef.current) socketRef.current.disconnect();
    setStatus('disconnected');
    log('Session disconnected.', 'info');
  };

  // Generate a report structure. 
  const endSessionAndGetReport = (): SessionReportData => {
    disconnect();
    const endTime = Date.now();
    const durationSeconds = Math.floor((endTime - startTimeRef.current) / 1000);

    // Flush any pending text in currentTurnRef
    const { user, model } = currentTurnRef.current;
    if (user.trim()) {
      transcriptHistoryRef.current.push({
        id: `${endTime}_u_final`,
        role: 'user',
        type: 'text',
        content: user.trim()
      });
    }
    if (model.trim()) {
      transcriptHistoryRef.current.push({
        id: `${endTime}_m_final`,
        role: 'model',
        type: 'text',
        content: model.trim()
      });
    }

    // If no transcriptions were captured (e.g. error), provide fallback
    let finalMessages = [...transcriptHistoryRef.current];
    if (finalMessages.length === 0) {
      finalMessages = [
        {
          id: '1', role: 'system', type: 'text',
          content: '未检测到对话内容或文本转录失败。'
        }
      ];
    }

    return {
      id: sessionDataRef.current.id,
      scenarioId,
      roleId,
      score: 75, // Initial placeholder score
      messages: finalMessages,
      startTime: new Date(startTimeRef.current).toISOString(),
      endTime: new Date(endTime).toISOString(),
      durationSeconds
    };
  };

  const clearLogs = () => setLogs([]);

  return {
    status,
    connect,
    disconnect,
    endSessionAndGetReport,
    config,
    setConfig,
    logs,
    clearLogs,
    volume
  };
};
