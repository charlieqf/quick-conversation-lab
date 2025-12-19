import asyncio
import os
import json
import websockets
import base64
import wave

# Configuration
API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = "qwen3-omni-flash-realtime"
URL = f"wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model={MODEL}"

def load_env():
    possible_paths = [".env", "backend/.env", "../.env"]
    for p in possible_paths:
        if os.path.exists(p):
            print(f"Loading env from {p}")
            with open(p, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if k == "DASHSCOPE_API_KEY":
                            return v.strip().strip('"')
    return None

async def test_vad():
    api_key_val = load_env()
    if not api_key_val:
        print("Error: DASHSCOPE_API_KEY not found.")
        return

    print(f"Connecting to {URL}...")
    headers = {"Authorization": f"Bearer {api_key_val}"}
    
    async with websockets.connect(URL, additional_headers=headers) as ws:
        print("Connected.")
        
        # 1. Handshake
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"], 
                "voice": "Cherry",
                "instructions": "You are a helpful assistant.",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                }
            }
        }
        await ws.send(json.dumps(session_config))
        
        # Wait for session.created
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data['type'] == 'session.created':
                print("Session created.")
                break
        
        # 2. Stream Audio from file
        wav_file = "test_output_16bit.wav"
        if not os.path.exists(wav_file):
            print(f"Error: {wav_file} not found. Run test_qwen_audio_gen.py first.")
            return

        print(f"Streaming {wav_file} to server...")
        with wave.open(wav_file, "rb") as wf:
            # Read all frames (or stream)
            # 16k mono 16bit
            chunk_size = 1024 * 10 # Send reasonably large chunks
            data = wf.readframes(chunk_size)
            while data:
                b64 = base64.b64encode(data).decode("ascii")
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "data": {"audio": b64}
                }))
                data = wf.readframes(chunk_size)
                await asyncio.sleep(0.05) # Simulate real-time roughly
        
        print("Finished streaming audio. Waiting for events...")
        
        # 3. Listen for events
        turn_detected = False
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(msg)
                event_type = data['type']
                print(f"EVENT: {event_type}")

                if event_type == "input_audio_buffer.speech_started":
                    print(">>> SPEECH STARTED")
                elif event_type == "input_audio_buffer.speech_stopped":
                    print(">>> SPEECH STOPPED")
                elif event_type == "turn_detected": # Checking if this exists
                    print(">>> TURN DETECTED (Exact Match)")
                    turn_detected = True
                
                if event_type == "response.audio.delta":
                    print("Received audio response!")
                    break
                    
        except asyncio.TimeoutError:
            print("Timeout waiting for response.")

if __name__ == "__main__":
    asyncio.run(test_vad())
