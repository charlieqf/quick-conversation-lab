
# Implementation Plan - Grok Voice Integration

The goal is to integrate the Grok Real-time Voice API as a new model option in the backend.

## User Review Required

> [!IMPORTANT]
> This plan assumes the user has a valid xAI API key and access to the `grok-beta` or relevant voice model. The key should be configured in `.env`.

## Proposed Changes

### Backend Adapter Layer


#### [NEW] `backend/app/adapters/grok.py`
- **Strategy**: Clone `backend/app/adapters/openai.py` and modify.
- **Why**: Grok's API maps almost 1:1 with OpenAI's Realtime API (e.g., `session.update`, `input_audio_buffer.append`).
- Key Modifications:
    - Change WebSocket URL to `wss://api.x.ai/v1/realtime`.
    - Update Header to remove `OpenAI-Beta`.
    - Verify event names (check `response.audio.delta` vs `response.output_audio.delta`).
    - Update supported voices list (Ara, Rex, Sal, Eve, Leo).


#### [MODIFY] `backend/app/registry.py` (Assumed) or `backend/app/adapters/__init__.py`
- Register `GrokAdapter` so it's available for selection.

#### [MODIFY] `backend/app/config.py`
- Add `XAI_API_KEY` to settings.

### Frontend (If necessary)
- Ensure the frontend can select the new model/provider. (Likely dynamic based on backend capabilities).

## Verification Plan

### Automated Tests
- We can't easily auto-test the real WebSocket without a mock server or spending money/usage.
- Will rely on manual verification.

### Manual Verification
1.  **Configure Key**: Add `XAI_API_KEY` to `.env`.
2.  **Select Model**: In the web UI settings, select the Grok model.
3.  **Voice Interaction**:
    -   Connect to the session.
    -   Speak into the microphone.
    -   Verify that Grok responds with audio (both hearing it and seeing the "Assistant Speaking" state).
    -   Check logs for successful connection and message events.
4.  **Interrupt**: Try to interrupt Grok to see if it handles barge-in (might need VAD logic adjustments if Grok doesn't handle it server-side efficiently or if we need local VAD).
