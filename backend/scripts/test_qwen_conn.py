import asyncio
import os
import json
import websockets
import base64

# Configuration
API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = "qwen3-omni-flash-realtime"
URL = f"wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model={MODEL}"

async def test_qwen_connection():
    if not API_KEY:
        print("Error: DASHSCOPE_API_KEY not found in environment variables.")
        return

    print(f"Connecting to {URL}...")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        async with websockets.connect(URL, additional_headers=headers) as ws:
            print("Connected!")
            
            # 1. Send Session Update (Handshake)
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "voice": "cherry",
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
            print("Sending session.update...")
            await ws.send(json.dumps(session_config))
            
            # 2. Listen for events
            print("Listening for events...")
            try:
                # wait for session.created or error
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(msg)
                    print(f"Received: {json.dumps(data, indent=2)}")
                    
                    if data.get("type") == "session.created":
                        print("Session Created! Handshake successful.")
                        break
                    if data.get("type") == "error":
                        print("Received Error event.")
                        break
            except asyncio.TimeoutError:
                print("Timeout waiting for response.")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    try:
        # Check current dir and backend/ dir
        possible_paths = [".env", "backend/.env", "../.env"]
        env_path = None
        for p in possible_paths:
            if os.path.exists(p):
                env_path = p
                print(f"Found .env at {p}")
                break
        
        if env_path:
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if k == "DASHSCOPE_API_KEY":
                            os.environ["DASHSCOPE_API_KEY"] = v.strip('"')
                            API_KEY = v.strip('"')
                            print("Loaded API Key from .env")
        else:
            print("Warning: .env not found in standard locations")
    except FileNotFoundError:
        print("Warning: ../.env not found")

    asyncio.run(test_qwen_connection())
