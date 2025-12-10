"""
Models API Router - List and get model capabilities
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.adapters.base import ModelCapabilities
from app.adapters.gemini import GeminiAdapter

router = APIRouter()

# Registry of available adapters
ADAPTERS = {
    "gemini": GeminiAdapter(),
    # Add more adapters here as they are implemented
    # "openai": OpenAIAdapter(),
    # "doubao": DoubaoAdapter(),
}


@router.get("", response_model=List[dict])
async def list_models():
    """List all available voice models"""
    models = []
    for adapter_id, adapter in ADAPTERS.items():
        cap = adapter.capabilities
        models.append({
            "id": cap.id,
            "name": cap.name,
            "provider": cap.provider,
            "isEnabled": cap.is_enabled,
            "defaultVoice": cap.default_voice,
            "supportsTranscription": cap.supports_transcription
        })
    return models


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Get detailed capabilities for a specific model"""
    if model_id not in ADAPTERS:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    adapter = ADAPTERS[model_id]
    cap = adapter.capabilities
    
    return {
        "id": cap.id,
        "name": cap.name,
        "provider": cap.provider,
        "isEnabled": cap.is_enabled,
        "supportedSampleRates": cap.supported_sample_rates,
        "supportedEncodings": cap.supported_encodings,
        "defaultSampleRate": cap.default_sample_rate,
        "defaultEncoding": cap.default_encoding,
        "availableVoices": cap.available_voices,
        "defaultVoice": cap.default_voice,
        "supportsTranscription": cap.supports_transcription,
        "supportsInterruption": cap.supports_interruption,
        "maxSessionDuration": cap.max_session_duration
    }


@router.get("/{model_id}/voices")
async def get_model_voices(model_id: str):
    """Get available voices for a specific model"""
    if model_id not in ADAPTERS:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    adapter = ADAPTERS[model_id]
    return adapter.capabilities.available_voices
