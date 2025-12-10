
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface SessionConfig {
  sampleRate: 16000 | 24000;
  bufferThreshold: number; // How many chunks before sending (ms approx)
  volumeThreshold: number; // VAD visual threshold
}

export interface StreamMetrics {
  inputVolume: number; // 0-255
  outputVolume: number; // 0-255
  latencyMs: number;
}
