from .adapters.gemini import GeminiAdapter
from .adapters.openai import OpenAIAdapter
from .adapters.grok import GrokAdapter
from .adapters.tongyi import TongyiAdapter
from .adapters.doubao import DoubaoAdapter
from .adapters.elevenlabs import ElevenLabsAdapter

# Registry of all available adapters
# Key is the 'modelId' used in API and WebSocket paths
ADAPTERS = {
    "gemini": GeminiAdapter,
    "openai-realtime": OpenAIAdapter,
    "grok-beta": GrokAdapter,
    "tongyi-realtime": TongyiAdapter,
    "doubao-realtime": DoubaoAdapter,
    "elevenlabs-realtime": ElevenLabsAdapter,
}

def get_adapter_class(model_id: str):
    return ADAPTERS.get(model_id)
