
export class GeminiSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private logCallback: (msg: string, type: 'info' | 'error' | 'stream') => void;
  private onAudioCallback: (b64: string) => void;
  private onTranscriptCallback: (role: 'user' | 'model' | 'system', text: string) => void;
  private onErrorCallback: (err: any) => void;

  constructor(
    modelId: string,
    apiKey: string,
    onLog: (msg: string, type: 'info' | 'error' | 'stream') => void,
    onAudio: (b64: string) => void,
    onTranscript: (role: 'user' | 'model' | 'system', text: string) => void,
    onError: (err: any) => void
  ) {
    const host = "generativelanguage.googleapis.com";
    this.url = `wss://${host}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${apiKey}`;
    
    this.logCallback = onLog;
    this.onAudioCallback = onAudio;
    this.onTranscriptCallback = onTranscript;
    this.onErrorCallback = onError;
  }

  connect(config: any, systemInstruction: string) {
    this.logCallback(`Connecting WS to Wanyi...`, 'info');
    
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.logCallback('WebSocket Open. Sending Setup...', 'info');
        this.sendSetup(config, systemInstruction);
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };

      this.ws.onerror = (err) => {
        this.logCallback(`WebSocket Error`, 'error');
        this.onErrorCallback(err);
      };

      this.ws.onclose = (ev) => {
        this.logCallback(`WebSocket Closed: ${ev.code} ${ev.reason}`, 'error');
      };

    } catch (e: any) {
      this.onErrorCallback(e);
    }
  }

  sendSetup(config: any, systemInstruction: string) {
    if (!this.ws) return;
    
    const setupMsg = {
      setup: {
        model: "models/gemini-2.5-flash-native-audio-preview-09-2025",
        generation_config: {
          response_modalities: ["AUDIO"],
          speech_config: {
             voice_config: { prebuilt_voice_config: { voice_name: "Kore" } }
          }
        },
        system_instruction: {
          parts: [
            { text: systemInstruction }
          ]
        },
        // Fix: Send empty objects to enable transcription. 
        // The API does not accept a 'model' field here in the v1alpha Bidi protocol.
        input_audio_transcription: {},
        output_audio_transcription: {}
      }
    };
    this.ws.send(JSON.stringify(setupMsg));
    this.logCallback('Setup message sent (Context Loaded & Transcription Enabled).', 'info');
  }

  sendAudioChunk(base64Pcm: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    
    const msg = {
      realtime_input: {
        media_chunks: [
          {
            mime_type: "audio/pcm",
            data: base64Pcm
          }
        ]
      }
    };
    this.ws.send(JSON.stringify(msg));
  }

  private async handleMessage(event: MessageEvent) {
    let data: any;
    try {
        if (event.data instanceof Blob) {
           const text = await event.data.text();
           data = JSON.parse(text);
        } else {
           data = JSON.parse(event.data);
        }
    } catch(e) {
        console.error("Failed to parse websocket message", e);
        return;
    }

    const content = data.serverContent;
    if (content) {
        // Handle Audio
        if (content.modelTurn?.parts) {
          const parts = content.modelTurn.parts;
          for (const part of parts) {
            if (part.inlineData) {
              this.logCallback(`RX Audio Chunk (${part.inlineData.data.length} chars)`, 'stream');
              this.onAudioCallback(part.inlineData.data);
            }
          }
        }

        // Handle Transcription
        if (content.outputTranscription?.text) {
             this.onTranscriptCallback('model', content.outputTranscription.text);
        }
        if (content.inputTranscription?.text) {
             this.onTranscriptCallback('user', content.inputTranscription.text);
        }

        if (content.turnComplete) {
           this.logCallback('Turn Complete.', 'info');
           this.onTranscriptCallback('system', 'TURN_COMPLETE');
        }

        if (content.interrupted) {
           this.logCallback('Server interrupted model.', 'info');
        }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
