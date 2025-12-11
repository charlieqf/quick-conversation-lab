# Doubao Realtime Voice (Volcengine) – Implementation Cheat Sheet (Dec 2025)

Concise, implementation-ready notes for integrating Doubao realtime voice over WebSocket. ASCII only; remove marketing fluff and mojibake from the prior draft.

## Endpoints & Auth
- Primary WS: `wss://ark.cn-beijing.volcengine.com/api/v3/realtime`
- Alternate WS (intl): e.g. `wss://ark.us-east-1.volcengine.com/api/v3/realtime` (confirm region)
- REST base (for OpenAI-compatible HTTP): `https://ark.cn-beijing.volcengine.com/api/v3`
- Auth: API key from Volcengine Ark. For WS, prefer headers (`Authorization: Bearer <API_KEY>`). If headers are not accepted, query param `authorization=Bearer%20<API_KEY>` is sometimes shown in samples—verify and avoid logging the key.

## Models (common IDs)
- `doubao-seed-realtimevoice` (recommended)
- `doubao-1.5-rtv-pro`
- `doubao-realtime-voice-pro`

## Audio Specs
- Input: 24 kHz, 16-bit, mono PCM (WAV/PCM). Send as base64 if using JSON frames; use small chunks.
- Output: 24 kHz PCM base64 in streaming events.
- Turn control: You generally send a user message, then `response.create` to trigger output. No separate “commit” is required if you wrap text/audio in a conversation item. If streaming raw audio, confirm whether an explicit commit is needed—samples below assume text-driven turns.

## Minimal Native WS Flow
1) Connect with model and auth (query or header).
2) `session.create` with desired voice/params.
3) Send user turn: `conversation.item.create` (role=user, content list of `{"type": "text"}` and/or `{"type": "audio"}` items).
4) Send `response.create` to make the model speak.
5) Stream deltas until `response.done`.

### Message Shapes (simplified)
- `session.create`
```json
{ "type": "session.create", "voice": "zh_female_kailangjiejie_moon", "temperature": 0.85, "max_tokens": 1024 }
```
- `conversation.item.create`
```json
{ "type": "conversation.item.create",
  "item": { "role": "user", "content": [ { "type": "text", "text": "你好，给我讲个故事" } ] }
}
```
- `response.create`
```json
{ "type": "response.create" }
```
- Streaming responses:
  - `response.text.delta` → `delta` text chunk
  - `response.audio.delta` → base64 PCM chunk
  - `response.done` → turn complete
- Errors: `error` object; handle by resetting state/closing.

### OpenAI-Compatible HTTP (if desired)
- Use `openai>=1.40.0` with `base_url="https://ark.cn-beijing.volcengine.com/api/v3"` and `model="doubao-seed-realtimevoice"`.
- Streamed responses include `delta.content` with `type=="text"` or `type=="audio"` (base64).

## Voices (examples)
- `zh_female_kailangjiejie_moon` – upbeat female (popular)
- `zh_female_yuanqi_shaonv_mengmeng` – cute female
- `zh_male_wennan_shuanglang` – warm male
- `en_female_emotional_sarah` – emotional English female
- Full list: https://www.volcengine.com/docs/82379/1527770#voice-list

## Limits (typical; verify current docs)
- Max audio input per turn: ~60 seconds
- Default VAD silence threshold: ~700 ms (if enabled)
- Concurrency: ~200 WS connections per key (raise via support)
- Recommended format: 24 kHz PCM16 mono

## Gotchas
- Do not expose API keys in URLs/logs; prefer headers.
- If you stream raw audio instead of text conversation items, clarify whether a “commit” or “stop” message is required; many samples rely on item+response pattern instead.
- Always listen for `response.done` before resetting per-turn state.
- Handle backpressure on audio output; buffer/queue for playback.

## Quick Implementation Checklist
- [ ] Add adapter with connect/session.create, send conversation.item.create, send response.create.
- [ ] Stream input audio as needed; base64 encode PCM.
+- [ ] Parse `response.text.delta` and `response.audio.delta`; emit `TURN_COMPLETE` on `response.done`.
- [ ] Map errors to app codes (400x/410x).
- [ ] Allow voice selection from known IDs; default to a safe Chinese voice.
- [ ] Include heartbeat/ping if WS idle timeouts occur.
