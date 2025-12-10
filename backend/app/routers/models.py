"""
Models API Router - List and get model capabilities
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.adapters.base import ModelCapabilities
from app.adapters.gemini import GeminiAdapter

router = APIRouter()

# Registry from common module
from ..registry import ADAPTERS


@router.get("", response_model=List[dict])
async def list_models():
    """List all available voice models"""
    models = []
    for adapter_id, adapter_cls in ADAPTERS.items():
        # Instantiate adapter to get capabilities
        adapter = adapter_cls()
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
    
    adapter_cls = ADAPTERS[model_id]
    adapter = adapter_cls()
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
    
    adapter_cls = ADAPTERS[model_id]
    adapter = adapter_cls()
    return adapter.capabilities.available_voices
