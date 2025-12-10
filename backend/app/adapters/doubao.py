from typing import Optional
import os
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig

class DoubaoAdapter(BaseModelAdapter):
    """Adapter for ByteDance Doubao"""
    
    @property
    def id(self) -> str:
        return "doubao-realtime"
    
    @property
    def name(self) -> str:
        return "Doubao (豆包)"
    
    @property
    def provider(self) -> str:
        return "ByteDance"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        api_key = os.getenv("VOLC_API_KEY")
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=bool(api_key),
            supported_sample_rates=[16000, 24000],
            supported_encodings=["pcm_s16le", "opus"],
            default_sample_rate=24000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "zh_female_1", "name": "灿灿 (Cancang)", "gender": "Female", "style": "Friendly"},
                {"id": "zh_male_1", "name": "运运 (Yunyun)", "gender": "Male", "style": "Confident"},
                {"id": "zh_female_2", "name": "玲玲 (Lingling)", "gender": "Female", "style": "Sweet"}
            ],
            default_voice="zh_female_1",
            supports_transcription=True,
            supports_interruption=True
        )

    async def connect(self, config: SessionConfig) -> None:
        if not self.capabilities.is_enabled:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Volcengine API key not configured")
            return
            
        self._status = AdapterStatus.CONNECTING
        import asyncio
        await asyncio.sleep(0.5)
        self._status = AdapterStatus.CONNECTED

    async def disconnect(self) -> None:
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        pass
