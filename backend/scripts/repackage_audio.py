import wave
import os

def repackage_audio():
    if not os.path.exists("raw_audio.bin"):
        print("Error: raw_audio.bin not found.")
        return

    with open("raw_audio.bin", "rb") as f:
        raw_data = f.read()

    print(f"Loaded {len(raw_data)} bytes.")

    # Hypothesis 1: 16-bit, Mono, 24000 Hz
    # If 16k was "slow", maybe it's 24k? (1.5x speedup required)
    with wave.open("debug_output_16bit_24k_mono.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(raw_data)
    print("Saved debug_output_16bit_24k_mono.wav")

    # Hypothesis 2: 16-bit, Stereo, 16000 Hz
    # If 16k mono was "slow", maybe it's stereo? (2x samples -> 2x duration if treated as mono)
    with wave.open("debug_output_16bit_16k_stereo.wav", "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw_data)
    print("Saved debug_output_16bit_16k_stereo.wav")
    
    # Hypothesis 3: 16-bit, Mono, 48000 Hz (3x slow)
    with wave.open("debug_output_16bit_48k_mono.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(raw_data)
    print("Saved debug_output_16bit_48k_mono.wav")

    # Hypothesis 4: 16-bit, Mono, 32000 Hz (2x slow) - Same duration as Stereo 16k but distinct pitch
    with wave.open("debug_output_16bit_32k_mono.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(32000)
        wf.writeframes(raw_data)
    print("Saved debug_output_16bit_32k_mono.wav")

if __name__ == "__main__":
    repackage_audio()
