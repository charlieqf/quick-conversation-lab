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
        self._response_in_progress: bool = False
        self._user_speech_detected: bool = False
    
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
            self._ws = await websockets.connect(url, additional_headers=headers)
            self._status = AdapterStatus.CONNECTED
            
            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # Configure Session
            await self._send_session_update(config)
            
        except Exception as e:
            print(f"OpenAI Connect Error: {e}")
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
                    "threshold": 0.6,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800
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
            if sequence % 50 == 0:
                print(f"WS Debug: Sending OpenAI Audio Chunk {sequence}")
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
                    b64_audio = data.get("delta", "")
                    if b64_audio:
                        self._emit_audio(b64_audio, 0)
                        
                elif event_type == "response.audio_transcript.delta":
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "response.text.delta":
                    # Handle separate text modality if enabled
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # Strongest signal that user turn is done
                    text = data.get("transcript", "")
                    if text:
                        self._emit_transcription("user", text, is_final=True)
                        self._user_speech_detected = True # Confirm valid speech
                    
                    # Trigger response if:
                    # 1. We have detected speech (via VAD or Text) AND 
                    # 2. No response is currently in progress
                    # 3. We have actual text (don't respond to empty transcripts unless VAD confirmed speech was real and maybe unsupported language?)
                    should_respond = (self._user_speech_detected or bool(text)) and not self._response_in_progress
                    
                    if should_respond:
                        print(f"WS Debug: OpenAI Transcription Completed (Text={bool(text)}) - Triggering Response")
                        self._response_in_progress = True
                        await self._ws.send(json.dumps({
                            "type": "response.create",
                            "response": {"modalities": ["text", "audio"]}
                        }))
                        
                elif event_type == "input_audio_buffer.speech_started":
                    print("WS Debug: OpenAI VAD - Speech Started")
                    self._user_speech_detected = True
                    
                elif event_type == "input_audio_buffer.speech_stopped":
                    print("WS Debug: OpenAI VAD - Speech Stopped")
                    # Fallback trigger: Only if we truly detected speech start/content
                    if self._user_speech_detected and not self._response_in_progress:
                        print("WS Debug: OpenAI VAD Stopped - Triggering Response (Fallback)")
                        self._response_in_progress = True
                        await self._ws.send(json.dumps({
                            "type": "response.create",
                            "response": {"modalities": ["text", "audio"]}
                        }))

                elif event_type == "response.done":
                    # Turn complete
                    if self._response_in_progress:
                        self._response_in_progress = False
                        self._user_speech_detected = False # Reset for next turn
                        self._emit_transcription("system", "TURN_COMPLETE", True)

                elif event_type == "error":
                    err = data.get("error", {})
                    print(f"WS Error: OpenAI Event Error: {err}")
                    self._response_in_progress = False 
                    self._user_speech_detected = False
                    self._emit_error(4003, f"OpenAI Error: {err.get('message')}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"OpenAI Receive Loop Error: {e}")
            self._response_in_progress = False
