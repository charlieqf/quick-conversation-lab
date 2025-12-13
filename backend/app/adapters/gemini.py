"""
Gemini Native Audio Adapter
"""
import json
import asyncio
import websockets
import base64
from typing import Optional

from app.adapters.base import (
    BaseModelAdapter, 
    SessionConfig, 
    ModelCapabilities,
    AdapterStatus
)
from app.config import settings


class GeminiAdapter(BaseModelAdapter):
    """Adapter for Google Gemini Native Audio model"""
    
    MODEL_NAME = "models/gemini-2.5-flash-native-audio-preview-09-2025"
    WS_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
    
    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._audio_sequence = 0
        self._client_ws = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_audio_time = 0
        self._last_chunk_time = 0
        self._turn_open = False
    
    @property
    def id(self) -> str:
        return "gemini"
    
    @property
    def name(self) -> str:
        return "Gemini Native Audio"
    
    @property
    def provider(self) -> str:
        return "Google"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        # If server side key is missing, we still report as enabled IF we want to allow users to bring their own key.
        # However, list_models doesn't know about user key.
        # We'll default to True if server key exists, OR True generally if we assume client might have it?
        # Safe bet: If server key is missing, is_enabled = False. 
        # But wait, if we want to support BYOK, we should report True and fail connection later?
        # Let's trust that if the user restores this feature they will provide a key. 
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=True, # Allow BYOK. Validated in connect.
            supported_sample_rates=[16000],  # Gemini Bidi expects 16kHz input
            supported_encodings=["pcm_s16le"],
            default_sample_rate=16000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "Puck", "name": "Puck", "gender": "Male"},
                {"id": "Charon", "name": "Charon", "gender": "Male"},
                {"id": "Kore", "name": "Kore", "gender": "Female"},
                {"id": "Fenrir", "name": "Fenrir", "gender": "Male"},
                {"id": "Zephyr", "name": "Zephyr", "gender": "Female"},
            ],
            default_voice="Kore",
            supports_transcription=True,
            supports_interruption=True,
            max_session_duration=600
        )
    
    async def connect(self, config: SessionConfig) -> None:
        """Connect to Gemini WebSocket API"""
        # Prioritize User Key -> Server Key
        api_key = config.api_key or settings.gemini_api_key
        
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Gemini API key not configured (Server or User)")
            return
        
        self._status = AdapterStatus.CONNECTING
        
        try:
            url = f"{self.WS_URL}?key={api_key}"
            self._ws = await websockets.connect(url)
            
            # Send setup message
            setup_msg = {
                "setup": {
                    "model": self.MODEL_NAME,
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": config.voice.voice_id
                                }
                            }
                        }
                    },
                    "system_instruction": {
                        "parts": [{"text": config.system_instruction}]
                    },
                    "input_audio_transcription": {},
                    "output_audio_transcription": {}
                }
            }
            await self._ws.send(json.dumps(setup_msg))
            
            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._monitor_task = asyncio.create_task(self._monitor_silence())
            self._status = AdapterStatus.CONNECTED
            
        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._emit_error(4100, f"Failed to connect: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._status = AdapterStatus.DISCONNECTED
    
    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        """Send audio chunk to Gemini"""
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return
        
        # Decode audio to check energy (VAD)
        # Prevent "Keep-Alive" from noisy silence preventing the turn closure
        try:
            audio_data = base64.b64decode(audio_base64)
            # Simple volume check (Mean Absolute Value of 16-bit PCM)
            # Create array of short ints
            pcm_shorts = []
            for i in range(0, len(audio_data), 2):
                chunk_val = int.from_bytes(audio_data[i:i+2], byteorder='little', signed=True)
                pcm_shorts.append(abs(chunk_val))
            
            avg_amp = sum(pcm_shorts) / len(pcm_shorts) if pcm_shorts else 0
            
            # Threshold: 500 is roughly -36dBFS for 16-bit
            # Adjustable based on env.
            is_speech = avg_amp > 800 
            
            if is_speech:
                self._last_audio_time = asyncio.get_event_loop().time()
                self._turn_open = True
            
            # print(f"Audio Seq={sequence} Amp={int(avg_amp)} Speech={is_speech}")
            
        except Exception as e:
            print(f"VAD Calc Error: {e}")
        except Exception as e:
            print(f"VAD Calc Error: {e}")
            self._last_audio_time = asyncio.get_event_loop().time() # Fallback

        # Update last chunk time unconditionally for rate limiting
        self._last_chunk_time = asyncio.get_event_loop().time()

        msg = {
            "realtime_input": {
                "media_chunks": [{
                    "mime_type": "audio/pcm;rate=16000",
                    "data": audio_base64
                }]
            }
        }
        try:
            print(f"Gemini TX chunk seq={sequence} len={len(audio_base64)}")
        except Exception:
            pass
        try:
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            print(f"Gemini send_audio error: {e}")

    async def _monitor_silence(self):
        """Monitor for silence and send turn_complete to bypass Gemini's long timeout"""
        while True:
            try:
                await asyncio.sleep(0.1)
                if not self._ws or self._status != AdapterStatus.CONNECTED:
                    continue

                if self._turn_open:
                    now = asyncio.get_event_loop().time()
                    
                    # Guard: Don't close if we just sent a chunk (wait 200ms grace)
                    if now - self._last_chunk_time < 0.2:
                        continue

                    # 1.0s silence threshold
                    if now - self._last_audio_time > 1.0:
                        print("Gemini Silence: >1.0s without audio, sending turn_complete")
                        self._turn_open = False
                        
                        # Explicitly tell Gemini the user turn is done
                        try:
                            # Send explicit end-of-turn (snake_case)
                            # User requested realtime_input wrapper
                            await self._ws.send(json.dumps({
                                "realtime_input": {
                                    "turn_complete": True
                                }
                            }))
                        except Exception as e:
                            print(f"Gemini turn_complete send error: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Silence Monitor Error: {e}")
                await asyncio.sleep(1)
    
    async def _receive_loop(self) -> None:
        """Background task to receive messages from Gemini"""
        try:
            async for message in self._ws:
                await self._handle_message(message)
        except websockets.ConnectionClosed as e:
            print(f"Gemini WS Closed: Code={e.code}, Reason={e.reason}")
            self._status = AdapterStatus.DISCONNECTED
            self._emit_error(4005, f"Connection closed: {e.reason or 'unknown'}")
        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._emit_error(4100, f"Receive error: {str(e)}")

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
    
    async def _handle_message(self, message: str) -> None:
        """Handle incoming message from Gemini"""
        try:
            if isinstance(message, bytes):
                data = json.loads(message.decode())
            else:
                data = json.loads(message)
            
            content = data.get("serverContent", {})
            try:
                if content:
                    print(f"Gemini RX keys={list(content.keys())}")
            except Exception:
                pass
            
            # Check for explicit error in serverContent
            if "error" in content:
                print(f"Gemini Server Info/Error: {content.get('error')}")

            
            # Handle audio output
            if "modelTurn" in content:
                parts = content["modelTurn"].get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        self._audio_sequence += 1
                        raw_b64 = part["inlineData"]["data"]
                        # Gemini Native output is 24kHz
                        wav_b64 = self._pcm_to_wav_base64(raw_b64, sample_rate=24000)
                        self._emit_audio(
                            wav_b64,
                            self._audio_sequence,
                            False
                        )
            
            # Handle transcription
            if "outputTranscription" in content:
                text = content["outputTranscription"].get("text", "")
                if text:
                    self._emit_transcription("model", text, False)
            
            if "inputTranscription" in content:
                text = content["inputTranscription"].get("text", "")
                if text:
                    self._emit_transcription("user", text, False)
            
            # Handle turn complete
            if content.get("turnComplete"):
                self._turn_open = False
                self._emit_transcription("system", "TURN_COMPLETE", True)
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Gemini handle_message error: {e}")
