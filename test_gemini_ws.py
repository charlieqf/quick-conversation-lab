
import asyncio
import websockets
import json
import ssl

# The user's key
# REPLACE THIS WITH YOUR KEY IF NEEDED, BUT I WILL PRE-FILL IT
API_KEY = "AIzaSyCTu8zBTYdhyA4bXpRev-tWBtTkz3Zvj5s"

WS_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

async def test_connect():
    url = f"{WS_URL}?key={API_KEY}"
    print(f"Connecting to: {WS_URL}...")
    
    try:
        # Standard SSL context
        ssl_context = ssl.create_default_context()
        
        async with websockets.connect(url, ssl=ssl_context) as ws:
            print("Successfully connected!")
            
            # Send a setup message to be sure
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.5-flash-native-audio-preview-09-2025",
                    "generation_config": {
                       "response_modalities": ["AUDIO"],
                    }
                }
            }
            await ws.send(json.dumps(setup_msg))
            print("Sent setup message.")
            
            # Wait for a response (or just proof it didn't crash)
            print("Waiting 2 seconds...")
            await asyncio.sleep(2)
            print("Connection stable.")
            
    except Exception as e:
        print(f"\n[ERROR] Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connect())
