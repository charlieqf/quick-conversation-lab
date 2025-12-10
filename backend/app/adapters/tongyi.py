from typing import Optional
import os
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig

class TongyiAdapter(BaseModelAdapter):
    """Adapter for Alibaba Tongyi (Qwen/CosyVoice)"""
    
    @property
    def id(self) -> str:
        return "tongyi-realtime"
    
    @property
    def name(self) -> str:
        return "Tongyi Realtime (Qwen)"
    
    @property
    def provider(self) -> str:
        return "Alibaba Cloud"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=bool(api_key),
            supported_sample_rates=[16000, 24000],
            supported_encodings=["pcm_s16le"],
            default_sample_rate=16000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "xiaoyun", "name": "Xiaoyun (小云)", "gender": "Female", "style": "Standard"},
                {"id": "xiaogang", "name": "Xiaogang (小刚)", "gender": "Male", "style": "News"},
                {"id": "amei", "name": "Amei (阿美)", "gender": "Female", "style": "Sweet"}
            ],
            default_voice="xiaoyun",
            supports_transcription=True,
            supports_interruption=False # Assumption for skeleton
        )

    async def connect(self, config: SessionConfig) -> None:
        if not self.capabilities.is_enabled:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "DashScope API key not configured")
            return
        
        self._status = AdapterStatus.CONNECTING
        import asyncio
        await asyncio.sleep(0.5)
        self._status = AdapterStatus.CONNECTED

    async def disconnect(self) -> None:
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        pass
