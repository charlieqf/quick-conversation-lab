
import { SessionConfig } from "./types";

export const DEFAULT_SESSION_CONFIG: SessionConfig = {
  sampleRate: 16000, // Gemini Native
  bufferThreshold: 15, // ~100ms buffering (was 3)
  volumeThreshold: 10
};

// PCM16 Linear, 1 channel
export const AUDIO_WORKLET_CODE = `
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = [];
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      const inputChannel = input[0];
      
      // Post raw float32 data to main thread
      // For high performance, we could convert to Int16 here, but doing it in worker is safer for audio thread
      if (inputChannel.length > 0) {
        this.port.postMessage(inputChannel);
      }
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
`;
