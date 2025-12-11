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
        self._audio_chunks_sent: int = 0
        self._user_speech_detected: bool = False
        self._response_debounce_task: Optional[asyncio.Task] = None
    
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
            # Track chunks to ensure we have enough audio buffer (OpenAI needs >100ms)
            self._audio_chunks_sent += 1
            
            if sequence % 50 == 0:
                print(f"WS Debug: Sending OpenAI Audio Chunk {sequence} (Total: {self._audio_chunks_sent})")
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
                
                if event_type == "response.created":
                     # Server beat us to it, cancel any pending manual trigger
                    print(f"WS Debug: response.created payload: {data}")
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                    self._response_in_progress = True

                elif event_type == "session.created":
                    self._session_id = data.get("session", {}).get("id")
                    
                elif event_type == "response.audio.delta":
                    self._response_in_progress = True
                    b64_audio = data.get("delta", "")
                    if b64_audio:
                        try:
                            pcm = base64.b64decode(b64_audio)
                            if len(pcm) < 4 or len(pcm) % 2 != 0:
                                continue
                            # Wrap in 24kHz WAV header for Frontend compat
                            wav_b64 = self._pcm_to_wav_base64(b64_audio, 24000)
                            self._emit_audio(wav_b64, 0)
                        except Exception:
                            pass
                        
                elif event_type == "response.audio_transcript.delta":
                    self._response_in_progress = True
                    text = data.get("delta", "")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "response.text.delta":
                    self._response_in_progress = True
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
                    # 1. We have actual text (don't respond to empty transcripts) 
                    # 2. No response is currently in progress
                    # 3. We have sent enough audio (prevent buffer too small error)
                    should_respond = bool(text) and not self._response_in_progress
                    if should_respond: # Just log, don't interfere
                        print(f"WS Debug: OpenAI Transcription Completed (Text=True) - Server should be responding...")
                        
                elif event_type == "input_audio_buffer.speech_started":
                    print("WS Debug: OpenAI VAD - Speech Started")
                    # If we started talking, interrupt any pending response trigger
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                        self._response_in_progress = False
                    
                elif event_type == "input_audio_buffer.speech_stopped":
                    print("WS Debug: OpenAI VAD - Speech Stopped")
                    has_sufficient_audio = self._audio_chunks_sent > 5
                    
                    if has_sufficient_audio and not self._response_in_progress:
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                        
                        print(f"WS Debug: OpenAI VAD Stopped (Chunks={self._audio_chunks_sent}) - Scheduling manual trigger...")
                        # Speculatively mark response in progress to avoid race
                        self._response_in_progress = True
                        self._response_debounce_task = asyncio.create_task(
                            self._trigger_model_response_with_delay(0.3)
                        )

                elif event_type == "response.done":
                    # Turn complete
                    print(f"WS Debug: response.done payload: {data}")
                    if self._response_in_progress:
                        self._response_in_progress = False
                        self._audio_chunks_sent = 0 # Reset for next turn
                        self._user_speech_detected = False
                        self._emit_transcription("system", "TURN_COMPLETE", True)

                elif event_type == "error":
                    err = data.get("error", {})
                    print(f"WS Error: OpenAI Event Error: {err}")
                    self._response_in_progress = False 
                    self._audio_chunks_sent = 0
                    self._user_speech_detected = False
                    self._emit_error(4003, f"OpenAI Error: {err.get('message')}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"OpenAI Receive Loop Error: {e}")
            self._response_in_progress = False
