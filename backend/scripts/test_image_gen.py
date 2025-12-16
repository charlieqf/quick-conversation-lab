
import asyncio
import os
import httpx
import base64
import json
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Settings
from app.config import settings

async def test_imagen(api_key):
    print(f"\n--- Testing Imagen 4.0 ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    payload = {
        "instances": [{ "prompt": "A cute cartoon robot doctor" }],
        "parameters": { "sampleCount": 1, "aspectRatio": "1:1" }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            if res.status_code == 200:
                print("✅ Imagen 4.0 Success")
                data = res.json()
                b64 = data["predictions"][0]["bytesBase64Encoded"]
                print(f"Received Image (Base64 length): {len(b64)}")
            else:
                print(f"❌ Imagen 4.0 Failed: {res.status_code}")
                print(res.text)
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_gemini(api_key, model_name="gemini-2.5-flash"):
    print(f"\n--- Testing Gemini ({model_name}) ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    # Payload for image generation via Gemini (if supported)
    # Note: Standard Gemini Flash might interpret this as a request for text description if it doesn't support image output tools natively enabled.
    payload = {
        "contents": [{
            "parts": [{ "text": "Draw a cute cartoon robot doctor" }]
        }],
        "generation_config": {
            "response_mime_type": "image/jpeg"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            if res.status_code == 200:
                print(f"✅ Gemini Request Success")
                data = res.json()
                # Check for image data
                try:
                    part = data["candidates"][0]["content"]["parts"][0]
                    if "inlineData" in part:
                         print(f"✅ Received Inline Image Data! Len: {len(part['inlineData']['data'])}")
                    else:
                         print(f"⚠️ Received Text Response (Expected for pure text models): {part.get('text', 'No text')[:100]}...")
                except:
                    print(f"⚠️ Unexpected structure: {json.dumps(data)[:200]}")
            else:
                print(f"❌ Gemini Failed: {res.status_code}")
                print(res.text)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Try to load from .env file manually if checking locally
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=")[1]
                        break
        except:
            pass
            
    if not api_key:
        print("Skipping test: GEMINI_API_KEY not found in env")
        exit(0)
        
    asyncio.run(test_imagen(api_key))
    # asyncio.run(test_gemini(api_key, "gemini-2.5-flash"))
    # asyncio.run(test_gemini(api_key, "gemini-2.5-flash-image"))
    
    # Test Imagen 3 as alternative
    print("\n--- Testing Imagen 3.0 ---")
    asyncio.run(test_gemini(api_key, "imagen-3.0-generate-001")) # Imagen 3 uses generateContent! Wait, no, it uses predict usually? Or generateContent?
    # Note: Imagen 3 on Vertex AI uses generateContent in some contexts, on AI Studio it uses predict.
    asyncio.run(test_imagen(api_key))
    
async def test_imagen3(api_key):
    print("\n--- Testing Imagen 3.0 ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    payload = {
        "instances": [{ "prompt": "A cute cartoon robot doctor" }],
        "parameters": { "sampleCount": 1, "aspectRatio": "1:1" }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            print(f"Imagen 3.0 Status: {res.status_code}")
            if res.status_code == 200:
                print("✅ Imagen 3.0 Success")
                data = res.json()
                b64 = data["predictions"][0]["bytesBase64Encoded"]
                print(f"Received Image (Base64 length): {len(b64)}")
            else:
                print(f"❌ Imagen 3.0 Failed: {res.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=")[1]
                        break
        except:
            pass
            
    if not api_key:
        print("Skipping test: GEMINI_API_KEY not found in env")
        exit(0)
        
    asyncio.run(test_imagen(api_key))
    # asyncio.run(test_gemini(api_key, "gemini-2.5-flash"))
    # asyncio.run(test_gemini(api_key, "gemini-2.5-flash-image"))
    asyncio.run(test_imagen3(api_key))
