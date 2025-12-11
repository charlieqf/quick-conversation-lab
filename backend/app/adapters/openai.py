import os
import json
import asyncio
import base64
import websockets
from typing import Optional
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig
from app.config import settings

class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI Realtime API (GPT-4o Audio) using WebSockets"""
    
    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
    
    @property
    def id(self) -> str:
        return "openai-realtime"
    
    @property
    def name(self) -> str:
        return "OpenAI Realtime (GPT-4o)"
    
    @property
    def provider(self) -> str:
        return "OpenAI"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        api_key = settings.openai_api_key
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=bool(api_key),
            supported_sample_rates=[24000], 
            supported_encodings=["pcm_s16le"], 
            default_sample_rate=24000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "alloy", "name": "Alloy", "gender": "Neutral", "style": "Versatile"},
                {"id": "echo", "name": "Echo", "gender": "Male", "style": "Resonant"},
                {"id": "shimmer", "name": "Shimmer", "gender": "Female", "style": "Clear"},
                {"id": "ash", "name": "Ash", "gender": "Male", "style": "Calm"},
                {"id": "ballad", "name": "Ballad", "gender": "Neutral", "style": "Energetic"},
                {"id": "coral", "name": "Coral", "gender": "Female", "style": "Bright"},
                {"id": "sage", "name": "Sage", "gender": "Neutral", "style": "Authority"},
                {"id": "verse", "name": "Verse", "gender": "Male", "style": "Intense"}
            ],
            default_voice="alloy",
            supports_transcription=True,
            supports_interruption=True
        )

    async def connect(self, config: SessionConfig) -> None:
        api_key = settings.openai_api_key
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "OpenAI API key not configured")
            return
        
        url = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, extra_headers=headers)
            self._status = AdapterStatus.CONNECTED
            
            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # Configure Session
            await self._send_session_update(config)
            
        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect to OpenAI: {str(e)}")
            await self.disconnect()

    async def _send_session_update(self, config: SessionConfig):
        if not self._ws: return

        session_update = {
            "type": "session.update",
            "session": {
                "voice": config.voice.voice_id,
                "instructions": config.system_instruction,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        await self._ws.send(json.dumps(session_update))

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
            
        if self._ws:
            try:
                await self._ws.close()
            except:
                pass
            self._ws = None
            
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return

        # Send audio append event
        msg = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        try:
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            print(f"Error sending audio: {e}")

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type")
                
                if event_type == "session.created":
                    self._session_id = data.get("session", {}).get("id")
                    
                elif event_type == "response.audio.delta":
                    # Audio output
                    b64_audio = data.get("delta", "")
                    if b64_audio:
                        self._emit_audio(b64_audio, 0) # Sequence not strictly tracked by OpenAI protocol
                        
                elif event_type == "response.audio_transcript.delta":
                    # Model transcript (streaming)
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # User transcript (final)
                    text = data.get("transcript", "")
                    if text:
                        self._emit_transcription("user", text, is_final=True)
                        
                elif event_type == "response.output_item.done":
                    # Check if it was a message response
                    item = data.get("item", {})
                    if item.get("type") == "message":
                        # Mark model turn as potentially done?
                        pass

                elif event_type == "error":
                    err = data.get("error", {})
                    self._emit_error(4003, f"OpenAI Error: {err.get('message')}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
                # self._emit_error(1000, "Connection closed by server")
        except Exception as e:
            print(f"OpenAI Receive Loop Error: {e}")
