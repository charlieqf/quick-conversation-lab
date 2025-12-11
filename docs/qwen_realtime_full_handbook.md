
# Alibaba Cloud Model Studio + Qwen Realtime Conversation  
# Comprehensive Developer Handbook (Markdown Version)

This document is a complete technical reference for developers using **Alibaba Cloud Model Studio / DashScope** and specifically its **Realtime Conversation (WebSocket) multimodal API**, including **text, audio, and image/video streaming**.

This handbook includes:

1. ModelStudio API concepts  
2. Realtime WebSocket protocol  
3. Qwen multimodal model capabilities  
4. Event schemas  
5. Token cost rules  
6. SDK usage (Python / Java / C++)  
7. Production considerations  

---

## 1. Model Studio Overview

Alibaba Cloud Model Studio is a platform for deploying, managing, and calling Qwen models.  
Key capabilities:

- Supports REST, WebSocket, and SDK-based inference  
- Supports multimodal inputs: text, audio, image, video frames  
- Offers fine-grained quotas, API keys, workspace isolation  
- Provides model publishing and online endpoints  

API access is via **DashScope**.

Main API endpoints:

- China:  
  wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=MODEL_NAME  
- International (Singapore recommended):  
  wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=MODEL_NAME  

Authentication:

Authorization: Bearer YOUR_DASHSCOPE_API_KEY

---

## 2. Qwen Realtime Models

### Supported realtime multimodal models
- qwen3-omni-flash-realtime  
- qwen-omni-turbo-realtime  
- qwen-omni-realtime  

### Typical capabilities:
- Full-duplex WebSocket streaming  
- Text + audio + image (frames) input  
- Synthesized audio output  
- Function calling  
- Session-level memory  
- Optional VAD (turn detection)  
- 65K context window (Flash models)  

---

## 3. Realtime WebSocket Protocol

The Realtime API uses **event-based JSON messages**.  
Two directions:

### Client → Server events:
- session.create  
- session.update  
- input_text  
- input_audio_buffer.append  
- input_audio_buffer.commit  
- input_image  
- input_image_buffer.append  
- input_tool_output  

### Server → Client events:
- session.created  
- session.updated  
- response.output_text.delta  
- response.output_audio.delta  
- response.completed  
- turn_detected  
- response.function_call  
- error  

All messages follow:

type: EVENT_NAME  
id: UUID (optional)  
data: OBJECT  

---

## 4. Session Lifecycle

1. Open WebSocket  
2. Send session.create  
3. Send text / audio / images  
4. Receive streaming deltas  
5. Receive response.completed  
6. Repeat  
7. Close WebSocket  

A session usually has a max lifetime (e.g. 30 minutes).

---

## 5. Session Creation Example (NO CODE FENCES)

type: session.create  
data:  
  modalities: ["text", "audio"]  
  input_audio_format: "pcm16"  
  output_audio_format: "wav"  
  audio_sample_rate: 16000  
  turn_detection:  
    type: "vad"  
  instructions: "You are a helpful assistant."  

---

## 6. Sending Text

type: input_text  
data:  
  text: "Hello, Qwen."  

---

## 7. Sending Audio

Audio must be **base64-encoded PCM16**.

type: input_audio_buffer.append  
data:  
  audio: BASE64_SEGMENT  

When finished:

type: input_audio_buffer.commit

---

## 8. Sending Images

For image understanding or video frames:

type: input_image  
data:  
  image: BASE64_IMAGE  
  mime_type: "image/jpeg"  

Or streaming frames:

type: input_image_buffer.append  
data:  
  image: BASE64_FRAME  

---

## 9. Receiving Text Output

type: response.output_text.delta  
data:  
  text: "Hel"  

Then more deltas, then:

type: response.completed

---

## 10. Receiving Audio Output

type: response.output_audio.delta  
data:  
  audio: BASE64_CHUNK  

You must decode and concatenate.

---

## 11. Function Calling (Tools)

Declare:

tools:  
  - type: "function"  
    name: "search_info"  
    description: "Lookup information"  
    parameters:  
      type: "object"  
      properties:  
        name: { type: "string" }  
      required: ["name"]

When model triggers:

type: response.function_call  
data:  
  name: "search_info"  
  arguments: { ... }  

Developer must respond:

type: input_tool_output  
data:  
  tool_call_id: SAME_ID  
  output: JSON_RESULT_STRING  

---

## 12. Token Costs

### Audio token cost
Approximation:

Qwen-3-Omni-Flash-Realtime:  
tokens = duration_in_seconds × 12.5 (minimum 1 second)

Qwen-Omni-Turbo-Realtime:  
tokens = duration_in_seconds × 25 (minimum 1 second)

### Image token cost
Flash realtime models:  
1 token per 32×32 pixel block  
Minimum: 4 tokens  
Maximum: 1280 tokens per image

Turbo realtime models:  
1 token per 28×28 block  

---

## 13. Model Limits (Examples)

Qwen-3-Omni-Flash-Realtime:  
- Max input tokens: 49,152  
- Output tokens: up to 16,384  
- Context window: 65,536  
- Multilingual  

Qwen-Omni-Turbo-Realtime:  
- Max input: 30,720  
- Output: 2,048  
- Faster, cheaper  

---

## 14. Python Integration (Plain Text)

Pseudocode (no fenced blocks):

import asyncio  
import websockets  
import json  
import base64  

connect to WS_URL with header Authorization  

send session.create  

send input_text  

while true:  
  receive events  
  handle text/audio deltas  

---

## 15. Java Integration (Plain Text)

Use Java WebSocket client:

onOpen → send session.create  
onMessage → parse JSON events  
onClose → cleanup  

---

## 16. C++ SDK (Linux)

Alibaba provides downloadable SDK tar.gz for:  
- x86_64  
- aarch64  

Supports:  
- Realtime multimodal WebSocket  
- Binary audio handling  
- Frame streaming  

---

## 17. Production Checklist

- Reconnect after session expiry  
- Stream audio in small chunks  
- Decode audio immediately  
- Use backpressure if needed  
- Monitor token cost  
- Handle response.function_call  
- Implement heartbeats (ping/pong)  
- Gracefully close session  

---

## 18. Troubleshooting

### Common errors:
- Incorrect API key → error  
- Wrong audio format → error  
- JSON schema mismatch → error  
- Exceeded max context window → error  

### Debugging:
- Log raw JSON events  
- Validate base64 correctness  
- Monitor WS connection state  

---

## 19. Recommended Project Structure

src/  
  client/  
    ws_connection.py  
    audio_encoder.py  
    event_handler.py  
  tools/  
    search_info.py  
  examples/  
    text_only.md  
    audio_text_agent.md  

docs/  
  realtime_protocol.md  
  token_costs.md  

---

## 20. Conclusion

This Markdown handbook provides the full picture of:

- Alibaba Model Studio API  
- DashScope realtime multimodal WebSocket  
- Qwen realtime models  
- Event schemas  
- Token limits & cost  
- SDK paths  
- Production readiness  

You can embed this file directly into:  
- GitHub repositories  
- Documentation portals  
- Internal developer guides  

