
import asyncio
import websockets
import json
import os

# API KEY should be loaded from environment
API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not API_KEY:
    print("Error: DASHSCOPE_API_KEY not set")
    exit(1)
# URL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash"
URL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen-omni-turbo-realtime"

async def test_connect():
    print(f"Connecting to {URL}...")
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        async with websockets.connect(URL, additional_headers=headers) as ws:
            print("Connected!")
            
            # 1. Send Session Create (Standard DashScope Reatime WS uses session.create w/ data)
            session_create = {
                "type": "session.create",
                "data": {
                    "modalities": ["text", "audio"],
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "audio_sample_rate": 16000,
                    "turn_detection": {"type": "vad"},
                },
            }
            await ws.send(json.dumps(session_create))
            print("Sent session.create")

            # 2. Receive loop
            async def listen():
                try:
                    async for msg in ws:
                        print(f"Server: {msg[:200]}") # Truncate log
                except Exception as e:
                    print(f"Listen error: {e}")

            asyncio.create_task(listen())
            
            # 3. Send Dummy Audio
            print("Sending audio...")
            import base64
            dummy_pcm = b'\x00' * 6400 # Silence
            
            for i in range(5):
                # Nested data format for standard API
                msg = {
                    "type": "input_audio_buffer.append",
                    "data": {"audio": base64.b64encode(dummy_pcm).decode("ascii")}
                }
                await ws.send(json.dumps(msg))
                await asyncio.sleep(0.2)
            
            print("Audio sent. Waiting...")
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connect())
