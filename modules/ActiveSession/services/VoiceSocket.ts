
export class VoiceSocket {
    private ws: WebSocket | null = null;
    private url: string;
    private logCallback: (msg: string, type: 'info' | 'error' | 'stream') => void;
    private onAudioCallback: (b64: string) => void;
    private onTranscriptCallback: (role: 'user' | 'model' | 'system', text: string) => void;
    private onErrorCallback: (err: any) => void;
    private audioSequence: number = 0;

    constructor(
        modelId: string,
        onLog: (msg: string, type: 'info' | 'error' | 'stream') => void,
        onAudio: (b64: string) => void,
        onTranscript: (role: 'user' | 'model' | 'system', text: string) => void,
        onError: (err: any) => void
    ) {
        // Protocol mapping: wss://{host}/ws/{model_id}
        const apiOverride = localStorage.getItem('VITE_API_BASE_URL');

        if (apiOverride) {
            try {
                // Parse override URL to get host
                const urlObj = new URL(apiOverride);
                const protocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:';
                this.url = `${protocol}//${urlObj.host}/ws/${modelId}`;
                console.log(`[VoiceSocket] Using override URL: ${this.url}`);
            } catch (e) {
                console.error("[VoiceSocket] Invalid override URL, falling back to relative.", e);
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                this.url = `${protocol}//${host}/ws/${modelId}`;
            }
        } else {
            // Default logic
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                this.url = `${protocol}//${host}/ws/${modelId}`;
            } else {
                // Production: Use direct Cloud Run URL to bypass Firebase Hosting Proxy (which strips Upgrade headers)
                // This corresponds to voice-model-lab-backend in asia-northeast1
                const CLOUD_RUN_HOST = "voice-model-lab-backend-1067995682638.asia-northeast1.run.app";
                this.url = `wss://${CLOUD_RUN_HOST}/ws/${modelId}`;
            }
        }

        this.logCallback = onLog;
        this.onAudioCallback = onAudio;
        this.onTranscriptCallback = onTranscript;
        this.onErrorCallback = onError;
    }

    connect(config: any, systemInstruction: string) {
        this.logCallback(`Connecting to backend: ${this.url}`, 'info');

        try {
            this.ws = new WebSocket(this.url);
            this.audioSequence = 0;

            this.ws.onopen = () => {
                this.logCallback('WebSocket Connected. Creating Session...', 'info');
                this.sendSessionCreate(config, systemInstruction);
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };

            this.ws.onerror = (err) => {
                this.logCallback(`WebSocket Error: ${err}`, 'error');
                this.onErrorCallback(err);
            };

            this.ws.onclose = (ev) => {
                this.logCallback(`WebSocket Closed: ${ev.code} ${ev.reason}`, 'error');
            };

        } catch (e: any) {
            this.onErrorCallback(e);
        }
    }

    sendSessionCreate(config: any, systemInstruction: string) {
        if (!this.ws) return;

        const msg = {
            type: "session.create",
            timestamp: Date.now(),
            requestId: crypto.randomUUID(),
            payload: {
                session: {
                    systemInstruction: systemInstruction,
                    maxDuration: 600
                },
                audio: {
                    sampleRate: config.audio?.sampleRate || 24000,
                    encoding: config.audio?.encoding || "pcm_s16le",
                    channels: config.audio?.channels || 1
                },
                voice: {
                    voiceId: config.voiceId || "Kore",
                    language: "zh-CN"
                }
            }
        };

        this.ws.send(JSON.stringify(msg));
        this.logCallback('Session Create message sent.', 'info');
    }

    sendAudioChunk(base64Pcm: string) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        this.audioSequence++;

        const msg = {
            type: "audio.input",
            timestamp: Date.now(),
            payload: {
                data: base64Pcm,
                sequence: this.audioSequence
            }
        };

        this.ws.send(JSON.stringify(msg));
    }

    private async handleMessage(event: MessageEvent) {
        let msg: any;
        try {
            if (event.data instanceof Blob) {
                const text = await event.data.text();
                msg = JSON.parse(text);
            } else {
                msg = JSON.parse(event.data);
            }
        } catch (e) {
            console.error("Failed to parse websocket message", e);
            return;
        }

        const type = msg.type;
        const payload = msg.payload;

        if (!type || !payload) return;

        switch (type) {
            case 'session.created':
                this.logCallback(`Session Created: ${payload.sessionId}`, 'info');
                break;

            case 'audio.output':
                if (payload.data) {
                    this.logCallback(`RX Audio (${payload.data.length} chars)`, 'stream');
                    this.onAudioCallback(payload.data);
                }
                break;

            case 'transcription':
                if (payload.text) {
                    this.onTranscriptCallback(payload.role, payload.text);
                }
                break;

            case 'turn.complete':
                this.logCallback('Turn Complete.', 'info');
                this.onTranscriptCallback('system', 'TURN_COMPLETE');
                break;

            case 'error':
                this.logCallback(`Server Error: ${payload.code} ${payload.message}`, 'error');
                this.onErrorCallback(new Error(`[${payload.code}] ${payload.message}`));
                this.disconnect(); // Force disconnect on critical error
                break;

            case 'warning':
                this.logCallback(`Server Warning: ${payload.code} ${payload.message}`, 'error');
                break;
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.send(JSON.stringify({ type: "session.end", timestamp: Date.now() }));
            this.ws.close();
            this.ws = null;
        }
    }
}
