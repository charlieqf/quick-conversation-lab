
import os
import requests

API_KEY = os.getenv("DASHSCOPE_API_KEY") or "sk-ba1f2d1941894ecda33a44b82bc0ea8b"
headers = {"Authorization": f"Bearer {API_KEY}"}

# DashScope Intl List Models (guessing endpoint, or just try a chat completion)
# Trying to just run a basic chat completion with the model to confirm it exists and IS qwen3-omni-flash
url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

data = {
    "model": "qwen3-omni-flash", 
    "messages": [{"role": "user", "content": "hi"}],
    "stream": False
}

try:
    print(f"Testing Model: {data['model']}")
    resp = requests.post(url, headers=headers, json=data)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
