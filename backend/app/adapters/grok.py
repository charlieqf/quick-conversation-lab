import os
import json
import asyncio
import base64
import websockets
from typing import Optional
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig
from app.config import settings

class GrokAdapter(BaseModelAdapter):
    """Adapter for Grok Realtime API (xAI) using WebSockets"""
    
    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
        self._response_in_progress: bool = False
        self._audio_chunks_sent: int = 0
        self._user_speech_detected: bool = False
        self._response_debounce_task: Optional[asyncio.Task] = None
    
    @property
    def id(self) -> str:
        return "grok-beta"
    
    @property
    def name(self) -> str:
        return "Grok Voice (Beta)"
    
    @property
    def provider(self) -> str:
        return "xAI"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        # Allow BYOK
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=True,
            supported_sample_rates=[24000], 
            supported_encodings=["pcm_s16le"], 
            default_sample_rate=24000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "ara", "name": "Ara", "gender": "Female", "style": "Warm"},
                {"id": "rex", "name": "Rex", "gender": "Male", "style": "Confident"},
                {"id": "sal", "name": "Sal", "gender": "Neutral", "style": "Smooth"},
                {"id": "eve", "name": "Eve", "gender": "Female", "style": "Energetic"},
                {"id": "leo", "name": "Leo", "gender": "Male", "style": "Authoritative"}
            ],
            default_voice="ara",
            supports_transcription=True,
            supports_interruption=True
        )

    async def connect(self, config: SessionConfig) -> None:
        # Prioritize User Key -> Server Key
        # Note: settings.xai_api_key needs to be added to config.py
        api_key = config.api_key or getattr(settings, "xai_api_key", None) or os.getenv("XAI_API_KEY")
        
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "xAI API key not configured (Server or User)")
            return
        
        url = "wss://api.x.ai/v1/realtime"
        headers = {
            "Authorization": f"Bearer {api_key}"
            # Grok docs don't mention OpenAI-Beta header
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
            print(f"Grok Connect Error: {e}")
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect to Grok: {str(e)}")
            await self.disconnect()

    async def _send_session_update(self, config: SessionConfig):
        if not self._ws: return

        # Grok uses same session.update structure as OpenAI
        session_update = {
            "type": "session.update",
            "session": {
                "voice": config.voice.voice_id,
                "instructions": config.system_instruction,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1" # Assuming Grok supports this or ignores it
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.4,
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

        if self._response_debounce_task:
            self._response_debounce_task.cancel()
            self._response_debounce_task = None
            
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
            self._audio_chunks_sent += 1
            
            if sequence % 50 == 0:
                print(f"WS Debug: Sending Grok Audio Chunk {sequence} (Total: {self._audio_chunks_sent})")
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            print(f"Error sending audio: {e}")

    async def _send_response_create(self):
        if not self._ws: return
        self._response_in_progress = True
        
        msg = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
            }
        }
        await self._ws.send(json.dumps(msg))

    async def _trigger_model_response_with_delay(self, delay: float = 0.5):
        try:
            await asyncio.sleep(delay)
            self._response_debounce_task = None
            
            print("WS Debug: Debounce timer expired, triggering response...")
            await self._send_response_create()

        except asyncio.CancelledError:
            print("WS Debug: Response debounce task cancelled (server responded first)")

    def _pcm_to_wav_base64(self, audio_b64: str, sample_rate: int = 24000) -> str:
        pcm_bytes = base64.b64decode(audio_b64)
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        chunk_size = 36 + data_size
        
        header = b"".join([
            b"RIFF",
            chunk_size.to_bytes(4, "little"),
            b"WAVE",
            b"fmt ",
            (16).to_bytes(4, "little"),
            (1).to_bytes(2, "little"),
            num_channels.to_bytes(2, "little"),
            sample_rate.to_bytes(4, "little"),
            byte_rate.to_bytes(4, "little"),
            block_align.to_bytes(2, "little"),
            bits_per_sample.to_bytes(2, "little"),
            b"data",
            data_size.to_bytes(4, "little")
        ])
        wav_bytes = header + pcm_bytes
        return base64.b64encode(wav_bytes).decode("ascii")

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type")
                
                # Grok Events Refined
                
                if event_type == "response.created":
                     # Server beat us to it, cancel any pending manual trigger
                    # print(f"WS Debug: response.created payload: {data}")
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                    self._response_in_progress = True

                elif event_type == "conversation.created":
                    # Grok sends this on connect
                    self._session_id = data.get("conversation", {}).get("id")
                    
                elif event_type == "session.updated":
                    # Acknowledge our session.update
                    pass

                elif event_type == "response.output_audio.delta": 
                    self._response_in_progress = True
                    b64_audio = data.get("delta", "")
                    if b64_audio:
                        try:
                            # Grok is PCM16 base64
                            pcm = base64.b64decode(b64_audio)
                            if len(pcm) < 4 or len(pcm) % 2 != 0:
                                continue
                            # Wrap in 24kHz WAV header for Frontend compat
                            # Note: Adapter says 24kHz in capabilities, so we assume frontend expects 24k
                            wav_b64 = self._pcm_to_wav_base64(b64_audio, 24000)
                            self._emit_audio(wav_b64, 0)
                        except Exception:
                            pass
                        
                elif event_type == "response.output_audio_transcript.delta":
                    self._response_in_progress = True
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "response.text.delta":
                    # If using text modality
                    self._response_in_progress = True
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    text = data.get("transcript", "")
                    if text:
                        self._emit_transcription("user", text, is_final=True)
                        self._user_speech_detected = True 
                    
                    should_respond = bool(text) and not self._response_in_progress
                    if should_respond:
                        pass
                        # print(f"WS Debug: Grok Transcription Completed - Server should be responding...")
                        
                elif event_type == "input_audio_buffer.speech_started":
                    print("WS Debug: Grok VAD - Speech Started")
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                        self._response_in_progress = False
                    
                elif event_type == "input_audio_buffer.speech_stopped":
                    print("WS Debug: Grok VAD - Speech Stopped")
                    has_sufficient_audio = self._audio_chunks_sent > 5
                    
                    if has_sufficient_audio and not self._response_in_progress:
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                        
                        # print(f"WS Debug: Grok VAD Stopped - Scheduling manual trigger...")
                        self._response_in_progress = True
                        self._response_debounce_task = asyncio.create_task(
                            self._trigger_model_response_with_delay(0.3)
                        )

                elif event_type == "response.done":
                    # Turn complete
                    if self._response_in_progress:
                        self._response_in_progress = False
                        self._audio_chunks_sent = 0 
                        self._user_speech_detected = False
                        self._emit_transcription("system", "TURN_COMPLETE", True)

                elif event_type == "error":
                    err = data.get("error", {})
                    print(f"WS Error: Grok Event Error: {err}")
                    self._response_in_progress = False 
                    self._audio_chunks_sent = 0
                    self._user_speech_detected = False
                    self._emit_error(4003, f"Grok Error: {err.get('message')}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"Grok Receive Loop Error: {e}")
            self._response_in_progress = False
