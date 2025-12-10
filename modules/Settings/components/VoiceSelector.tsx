import React, { useState } from 'react';
import { AVAILABLE_VOICES } from '../../../constants';
import { VoiceId } from '../../../types';
import { Mic, Play, Volume2, Loader2 } from 'lucide-react';
import { GoogleGenAI, Modality } from "@google/genai";

interface VoiceSelectorProps {
  selectedVoice: VoiceId;
  onSelect: (id: VoiceId) => void;
  apiKeyConfigured: boolean;
}

export const VoiceSelector: React.FC<VoiceSelectorProps> = ({ selectedVoice, onSelect, apiKeyConfigured }) => {
  const [playingVoiceId, setPlayingVoiceId] = useState<VoiceId | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Helper: Decode Base64 string to Uint8Array
  const decodeBase64 = (base64: string) => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
  };

  const playPreview = async (voiceId: VoiceId, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!apiKeyConfigured) {
      alert("请先在上方连接 Google AI Studio 以试听语音。");
      return;
    }

    if (isLoading || playingVoiceId) return;

    setIsLoading(true);
    setPlayingVoiceId(voiceId);

    try {
      // Initialize AI with the key from env (injected by AI Studio)
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const voiceName = voiceId; // The ID matches the API voice name (Zephyr, etc.)
      
      // Generate Speech
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: [{ parts: [{ text: `你好，我是 ${voiceName}。这是我的声音预览。` }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: voiceName },
            },
          },
        },
      });

      const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;

      if (!base64Audio) {
        throw new Error("No audio data returned");
      }

      // Play Audio using Web Audio API
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContextClass();
      
      const audioBytes = decodeBase64(base64Audio);
      
      // Function to decode raw PCM if standard decode fails
      const decodePCM = (data: Uint8Array, ctx: AudioContext) => {
         const inputData = new Int16Array(data.buffer);
         const buffer = ctx.createBuffer(1, inputData.length, 24000); // 24kHz is standard for Gemini
         const channelData = buffer.getChannelData(0);
         for (let i = 0; i < inputData.length; i++) {
            channelData[i] = inputData[i] / 32768.0;
         }
         return buffer;
      }

      let audioBuffer: AudioBuffer;
      try {
         // Attempt standard decoding first
         const bufferCopy = audioBytes.slice(0).buffer;
         audioBuffer = await audioCtx.decodeAudioData(bufferCopy);
      } catch (err) {
         // Fallback to PCM 24kHz Mono if standard decode fails
         audioBuffer = decodePCM(audioBytes, audioCtx);
      }

      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      
      source.onended = () => {
        setPlayingVoiceId(null);
        setIsLoading(false);
        audioCtx.close();
      };

      source.start();

    } catch (err) {
      console.error("TTS Preview failed:", err);
      alert("语音预览生成失败，请检查网络或 API Key。");
      setPlayingVoiceId(null);
      setIsLoading(false);
    }
  };

  return (
    <div className="mb-6">
      <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
        <Mic className="w-4 h-4 mr-2 text-medical-600" />
        语音声线 (Voice)
      </h3>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 divide-y divide-slate-50">
        {AVAILABLE_VOICES.map((voice) => {
          const isSelected = selectedVoice === voice.id;
          const isPlaying = playingVoiceId === voice.id;

          return (
            <div 
              key={voice.id}
              onClick={() => onSelect(voice.id)}
              className={`
                flex items-center justify-between p-3 cursor-pointer transition-colors
                ${isSelected ? 'bg-medical-50/20' : 'hover:bg-slate-50'}
              `}
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-lg">
                  {voice.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${isSelected ? 'text-medical-700' : 'text-slate-700'}`}>
                      {voice.name}
                    </span>
                    <span className={`
                      text-[10px] px-1.5 py-0.5 rounded border
                      ${voice.gender === 'Male' 
                        ? 'bg-blue-50 text-blue-600 border-blue-100' 
                        : 'bg-rose-50 text-rose-600 border-rose-100'}
                    `}>
                      {voice.gender === 'Male' ? '男声' : '女声'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {voice.style}
                  </p>
                </div>
              </div>

              {/* Play Sample Button */}
              <button 
                onClick={(e) => playPreview(voice.id, e)}
                disabled={(isLoading && !isPlaying) || !apiKeyConfigured}
                className={`
                  w-8 h-8 flex items-center justify-center rounded-full transition-all
                  ${!apiKeyConfigured ? 'opacity-30 cursor-not-allowed' : ''}
                  ${isPlaying 
                    ? 'bg-medical-100 text-medical-600 animate-pulse' 
                    : 'text-slate-300 hover:text-medical-600 hover:bg-medical-50'}
                `}
                title="试听 (需连接 API)"
              >
                {isPlaying ? (
                  <Volume2 className="w-4 h-4" />
                ) : (
                  isLoading && playingVoiceId === null && isSelected ? ( 
                     <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                     <Play className="w-4 h-4 fill-current" />
                  )
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};