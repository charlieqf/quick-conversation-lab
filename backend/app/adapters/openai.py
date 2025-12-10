from typing import Optional
import os
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig

class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI Realtime API (GPT-4o Audio)"""
    
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
        api_key = os.getenv("OPENAI_API_KEY")
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
        if not self.capabilities.is_enabled:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "OpenAI API key not configured")
            return
        
        # Skeleton connection simulation
        self._status = AdapterStatus.CONNECTING
        # Simulate async connection
        import asyncio
        await asyncio.sleep(0.5) 
        self._status = AdapterStatus.CONNECTED
        # In real impl, we would start websocket here
        
    async def disconnect(self) -> None:
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        # In skeleton, just log or ignore
        pass
