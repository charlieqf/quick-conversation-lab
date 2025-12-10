"""
Gemini Native Audio Adapter
"""
import json
import asyncio
import websockets
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
        self._client_ws = None  # Reference to client WebSocket for error propagation
    
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
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=bool(settings.gemini_api_key),
            supported_sample_rates=[24000],  # Gemini Native Audio requires 24kHz
            supported_encodings=["pcm_s16le"],
            default_sample_rate=24000,  # Must be 24kHz for Gemini
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
        if not settings.gemini_api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Gemini API key not configured")
            return
        
        self._status = AdapterStatus.CONNECTING
        
        try:
            url = f"{self.WS_URL}?key={settings.gemini_api_key}"
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
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._status = AdapterStatus.DISCONNECTED
    
    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        """Send audio chunk to Gemini"""
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return
        
        msg = {
            "realtime_input": {
                "media_chunks": [{
                    "mime_type": "audio/pcm",
                    "data": audio_base64
                }]
            }
        }
        await self._ws.send(json.dumps(msg))
    
    async def _receive_loop(self) -> None:
        """Background task to receive messages from Gemini"""
        try:
            async for message in self._ws:
                await self._handle_message(message)
        except websockets.ConnectionClosed as e:
            self._status = AdapterStatus.DISCONNECTED
            self._emit_error(4005, f"Connection closed: {e.reason or 'unknown'}")
        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._emit_error(4100, f"Receive error: {str(e)}")
    
    async def _handle_message(self, message: str) -> None:
        """Handle incoming message from Gemini"""
        try:
            if isinstance(message, bytes):
                data = json.loads(message.decode())
            else:
                data = json.loads(message)
            
            content = data.get("serverContent", {})
            
            # Handle audio output
            if "modelTurn" in content:
                parts = content["modelTurn"].get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        self._audio_sequence += 1
                        self._emit_audio(
                            part["inlineData"]["data"],
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
                self._emit_transcription("system", "TURN_COMPLETE", True)
                
        except json.JSONDecodeError:
            pass
