
import asyncio
import httpx
import os
import io
import base64
from dotenv import load_dotenv

load_dotenv("backend/.env")

API_KEY = os.getenv("GEMINI_API_KEY")

async def test_gemini_image_gen():
    if not API_KEY:
        print("GEMINI_API_KEY not found")
        return

    # Try using gemini-2.5-flash for image generation
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    
    prompt = "A cute cartoon cat"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        # Try asking for image? Gemini usually needs tool use or specific config to gen images if it's not an Imagen model?
        # But maybe it just works if the model supports it?
        # The original code just sent text.
    }
    
    print(f"Testing {model_name} for image generation...")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            # print(data)
            try:
                # Check for inline data (image)
                part = data["candidates"][0]["content"]["parts"][0]
                if "inlineData" in part:
                     print("SUCCESS: Received inlineData (Image)!")
                     print(f"MimeType: {part['inlineData']['mimeType']}")
                elif "text" in part:
                     print(f"Received Text: {part['text'][:50]}...")
                     print("FAIL: Model returned text, not image.")
            except Exception as e:
                print(f"Error parsing response: {e}")
                print(data)
        else:
            print(f"Error: {response.status_code} {response.text}")

if __name__ == "__main__":
    asyncio.run(test_gemini_image_gen())
