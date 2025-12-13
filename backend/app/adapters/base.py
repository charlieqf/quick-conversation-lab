"""
Base Model Adapter - Abstract interface for all voice model adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, List
from enum import Enum


class AdapterStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class AudioConfig:
    """Audio configuration for the session"""
    sample_rate: int = 16000
    encoding: str = "pcm_s16le"
    channels: int = 1


@dataclass
class VoiceConfig:
    """Voice configuration"""
    voice_id: str = "default"
    language: str = "zh-CN"


@dataclass
class SessionConfig:
    """Configuration for a voice session"""
    model_id: str
    audio: AudioConfig = field(default_factory=AudioConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    system_instruction: str = ""
    max_duration: int = 600  # seconds
    api_key: Optional[str] = None # User override


@dataclass
class ModelCapabilities:
    """Model capabilities and configuration"""
    id: str
    name: str
    provider: str
    is_enabled: bool = True
    
    # Audio capabilities
    supported_sample_rates: List[int] = field(default_factory=lambda: [16000, 24000])
    supported_encodings: List[str] = field(default_factory=lambda: ["pcm_s16le"])
    default_sample_rate: int = 16000
    default_encoding: str = "pcm_s16le"
    
    # Voice options
    available_voices: List[dict] = field(default_factory=list)
    default_voice: str = "default"
    
    # Features
    supports_transcription: bool = True
    supports_interruption: bool = True
    max_session_duration: int = 600


class BaseModelAdapter(ABC):
    """Abstract base class for all voice model adapters"""
    
    def __init__(self):
        self._status = AdapterStatus.DISCONNECTED
        self._audio_callback: Optional[Callable[[str, int, bool], None]] = None
        self._transcription_callback: Optional[Callable[[str, str, bool], None]] = None
        self._error_callback: Optional[Callable[[int, str], None]] = None
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this adapter"""
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for this adapter"""
        ...
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider name (e.g., 'Google', 'OpenAI')"""
        ...
    
    @property
    @abstractmethod
    def capabilities(self) -> ModelCapabilities:
        """Get model capabilities"""
        ...
    
    @property
    def status(self) -> AdapterStatus:
        return self._status
    
    @abstractmethod
    async def connect(self, config: SessionConfig) -> None:
        """Establish connection with the model"""
        ...
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        ...
    
    @abstractmethod
    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        """Send audio chunk to the model"""
        ...
    
    def on_audio_received(self, callback: Callable[[str, int, bool], None]) -> None:
        """Register callback for received audio: (base64_data, sequence, is_final)"""
        self._audio_callback = callback
    
    def on_transcription(self, callback: Callable[[str, str, bool], None]) -> None:
        """Register callback for transcription: (role, text, is_final)"""
        self._transcription_callback = callback
    
    def on_error(self, callback: Callable[[int, str], None]) -> None:
        """Register callback for errors: (code, message)"""
        self._error_callback = callback
    
    def _emit_audio(self, data: str, sequence: int, is_final: bool = False) -> None:
        if self._audio_callback:
            self._audio_callback(data, sequence, is_final)
    
    def _emit_transcription(self, role: str, text: str, is_final: bool = False) -> None:
        if self._transcription_callback:
            self._transcription_callback(role, text, is_final)
    
    def _emit_error(self, code: int, message: str) -> None:
        if self._error_callback:
            self._error_callback(code, message)
