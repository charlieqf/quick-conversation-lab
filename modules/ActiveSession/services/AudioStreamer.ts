
import { AUDIO_WORKLET_CODE } from "../constants";

export class AudioStreamer {
  private context: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private analyser: AnalyserNode | null = null;

  private onDataCallback: (data: Float32Array) => void;
  private logCallback: (msg: string, type: 'info' | 'error') => void;

  constructor(
    onData: (data: Float32Array) => void,
    onLog: (msg: string, type: 'info' | 'error') => void
  ) {
    this.onDataCallback = onData;
    this.logCallback = onLog;
  }

  async start(sampleRate: number) {
    try {
      this.logCallback(`Initializing AudioContext at ${sampleRate}Hz...`, 'info');

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.context = new AudioContextClass({ sampleRate });
      if (this.context.state === 'suspended') {
        await this.context.resume();
      }

      // 1. Get Microphone
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      this.logCallback('Microphone access granted.', 'info');

      // 2. Load Worklet via Blob URL
      const blob = new Blob([AUDIO_WORKLET_CODE], { type: 'application/javascript' });
      const workletUrl = URL.createObjectURL(blob);
      await this.context.audioWorklet.addModule(workletUrl);
      this.logCallback('AudioWorklet module loaded.', 'info');

      // 3. Create Nodes
      this.sourceNode = this.context.createMediaStreamSource(this.mediaStream);
      this.workletNode = new AudioWorkletNode(this.context, 'pcm-processor');
      this.analyser = this.context.createAnalyser();
      this.analyser.smoothingTimeConstant = 0.3;
      this.analyser.fftSize = 256;

      // 4. Wiring: Source -> Analyser -> Worklet -> Destination (Muted to prevent feedback loop but keep alive)
      // Note: We don't connect Worklet to Destination because we are capturing input, not monitoring it.
      // But browser might garbage collect if not connected. Best practice is to connect to a muted gain.

      this.sourceNode.connect(this.analyser);
      this.analyser.connect(this.workletNode);
      this.workletNode.connect(this.context.destination); // Required for 'process' to fire in Chrome

      // 5. Handle Data from Worklet
      this.workletNode.port.onmessage = (event) => {
        const float32Data = event.data;
        this.onDataCallback(float32Data);
      };

      this.logCallback('Audio Pipeline Started (Full Duplex).', 'info');

    } catch (e: any) {
      this.logCallback(`Streamer Error: ${e.message}`, 'error');
      throw e;
    }
  }

  getVolume(): number {
    if (!this.analyser) return 0;
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
    return sum / dataArray.length;
  }

  async resume() {
    if (this.context && this.context.state === 'suspended') {
      await this.context.resume();
    }
  }

  playBuffer(audioBuffer: AudioBuffer, startTime: number) {
    if (!this.context) return;
    const source = this.context.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.context.destination);
    source.start(startTime);
  }

  getContext() {
    return this.context;
  }

  stop() {
    this.logCallback('Stopping Streamer...', 'info');
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
    }
    if (this.workletNode) this.workletNode.disconnect();
    if (this.sourceNode) this.sourceNode.disconnect();
    if (this.context) this.context.close();

    this.mediaStream = null;
    this.context = null;
  }
}
