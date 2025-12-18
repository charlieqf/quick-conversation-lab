
import asyncio
import websockets
import json
import os

# API KEY should be loaded from environment
API_KEY = os.getenv("XAI_API_KEY")
if not API_KEY:
    print("Error: XAI_API_KEY not set")
    exit(1)
URL = "wss://api.x.ai/v1/realtime"

async def test_connect():
    print(f"Connecting to {URL}...")
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        async with websockets.connect(URL, additional_headers=headers) as ws:
            print("Connected!")
            
            # Wait for conversation.created
            msg = await ws.recv()
            print(f"Received: {msg}")
            
            # Send session update
            update = {
                "type": "session.update",
                "session": {
                    "voice": "ara"
                }
            }
            await ws.send(json.dumps(update))
            print("Sent session.update")
            
            # Wait for response
            msg = await ws.recv()
            print(f"Received: {msg}")
            
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connect())
