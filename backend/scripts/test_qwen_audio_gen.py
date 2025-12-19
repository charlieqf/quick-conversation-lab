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

async def test_audio_gen():
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
                "instructions": "Say 'Hello, this is a test of the audio system.'",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16", # Server ignores this and sends pcm24 usually
                "turn_detection": {"type": "server_vad"}
            }
        }
        await ws.send(json.dumps(session_config))
        
        # 2. Trigger speech (send a text signal pretending to be user input, or just wait if instructions are enough? 
        # Instructions alone might not trigger speech unless we send an event.
        # Let's send a fake conversation item)
        
        # Wait for session.created
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data['type'] == 'session.created':
                out_fmt = data['session'].get('output_audio_format')
                print(f"Session created. Output format reported by server: {out_fmt}")
                if out_fmt == "pcm16":
                    # If server respects pcm16, we should not convert from pcm24
                    FORCE_PCM16 = True
                else:
                    FORCE_PCM16 = False
                break
        
        # Send text to trigger response
        print("Sending text input...")
        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello, please count to three."}]
            }
        }))
        await ws.send(json.dumps({"type": "response.create"}))

        audio_chunks = []
        
        print("Receiving audio...")
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(msg)
                print(f"DEBUG: {data['type']}") # Debug all events
                
                if data['type'] == 'response.audio.delta':
                    b64 = data['delta']
                    audio_chunks.append(base64.b64decode(b64))
                
                if data['type'] == 'error':
                     print(f"ERROR: {data}")

                if data['type'] == 'response.done':
                    print("Response done.")
                    break
            except asyncio.TimeoutError:
                print("Timeout.")
                break
        
        # Concatenate all PCM24 bytes
        raw_pcm24 = b"".join(audio_chunks)
        print(f"Received {len(raw_pcm24)} bytes of PCM24 data.")
        
        # Final Verification: 16-bit 24kHz
        print("Saving final_check_24k.wav (16-bit, 24000Hz)...")
        with wave.open("final_check_24k.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(raw_pcm24) # Raw data is 16-bit 24k
        print("Saved final_check_24k.wav")

if __name__ == "__main__":
    asyncio.run(test_audio_gen())
