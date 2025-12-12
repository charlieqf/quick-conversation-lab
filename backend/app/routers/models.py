"""
Models API Router - List and get model capabilities
"""
from fastapi import APIRouter, HTTPException, Response, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import httpx
import base64
import struct
import json

from app.config import settings
from app.adapters.base import ModelCapabilities
from app.adapters.gemini import GeminiAdapter

router = APIRouter()

# Registry from common module
from ..registry import ADAPTERS


@router.get("", response_model=List[dict])
async def list_models(response: Response):
    """List all available voice models"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
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


class PreviewRequest(BaseModel):
    modelId: str
    voiceId: str
    text: Optional[str] = "Hello, this is a voice preview."


@router.post("/preview")
async def preview_voice(req: PreviewRequest):
    """Generate a short audio preview for the selected voice"""
    
    # 1. OpenAI Handling
    if req.modelId.startswith("openai") or "gpt" in req.modelId:
        if not settings.openai_api_key:
             raise HTTPException(status_code=400, detail="OpenAI API Key not configured")

        try:
            async with httpx.AsyncClient() as client:
                # https://platform.openai.com/docs/api-reference/audio/createSpeech
                res = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "tts-1", # Standard TTS model
                        "input": req.text,
                        "voice": req.voiceId.lower() # OpenAI voices are lowercase
                    },
                    timeout=10.0
                )
                
                if res.status_code != 200:
                    print(f"OpenAI TTS Error: {res.text}")
                    raise HTTPException(status_code=res.status_code, detail=f"Provider Error: {res.text}")
                
                return Response(content=res.content, media_type="audio/mpeg")
                
        except Exception as e:
            print(f"TTS Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # 2. Gemini Handling
    elif req.modelId.startswith("gemini"):
        if not settings.gemini_api_key:
             raise HTTPException(status_code=400, detail="Gemini API Key not configured")

        try:
            # Helper to create WAV header for 24kHz, 16-bit, Mono
            def create_wav_header(pcm_data_len: int, sample_rate: int = 24000) -> bytes:
                # RIFF chunk
                header = b'RIFF'
                header += struct.pack('<I', 36 + pcm_data_len) # File size - 8
                header += b'WAVE'
                
                # fmt chunk
                header += b'fmt '
                header += struct.pack('<I', 16) # Chunk size (16 for PCM)
                header += struct.pack('<H', 1)  # Audio format (1 for PCM)
                header += struct.pack('<H', 1)  # Num channels (1 for Mono)
                header += struct.pack('<I', sample_rate) # Sample rate
                header += struct.pack('<I', sample_rate * 2) # Byte rate (SampleRate * NumChannels * BitsPerSample/8)
                header += struct.pack('<H', 2)  # Block align (NumChannels * BitsPerSample/8)
                header += struct.pack('<H', 16) # Bits per sample
                
                # data chunk
                header += b'data'
                header += struct.pack('<I', pcm_data_len)
                return header

            async with httpx.AsyncClient() as client:
                model_name = "gemini-2.5-flash-native-audio-preview-09-2025" # Hardcoded best model for audio
                url = f"https://generativelanguage.googleapis.com/v1alpha/models/{model_name}:generateContent?key={settings.gemini_api_key}"
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"Please say: {req.text}"
                        }]
                    }],
                    "generation_config": {
                       "response_modalities": ["AUDIO"],
                       "speech_config": {
                          "voice_config": {
                              "prebuilt_voice_config": {
                                  "voice_name": req.voiceId
                              }
                          }
                       }
                    }
                }
                
                res = await client.post(
                    url,
                    json=payload,
                    timeout=15.0
                )
                
                if res.status_code != 200:
                    print(f"Gemini TTS Error: {res.text}")
                    if res.status_code == 404:
                         # Fallback for preview model unavailability
                         raise HTTPException(status_code=501, detail="Voice preview not supported by this model")
                    raise HTTPException(status_code=res.status_code, detail=f"Gemini Error: {res.text}")
                
                data = res.json()
                # Extract inlineData
                # Response structure: candidates[0].content.parts[0].inlineData.data (Base64)
                try:
                    b64_data = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                    pcm_bytes = base64.b64decode(b64_data)
                    
                    # Create WAV container
                    wav_header = create_wav_header(len(pcm_bytes))
                    wav_data = wav_header + pcm_bytes
                    
                    return Response(content=wav_data, media_type="audio/wav")
                    
                except (KeyError, IndexError) as ignored:
                    print(f"Gemini Unexpected Response: {data}")
                    raise HTTPException(status_code=502, detail="Invalid response format from Gemini")
                    
        except Exception as e:
            print(f"Gemini TTS Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Unsupported model for preview")


@router.get("/scenario", response_model=List[dict])
async def list_scenario_models():
    """List models supported for Scenario Generation (Mirroring Legacy App Options)"""
    return [
        { 
            "id": "gemini-2.5-flash", 
            "name": "Gemini 2.5 Flash", 
            "badge": "Fast",
            "description": "Optimized for speed and efficiency. Best for real-time interactions." 
        },
        { 
            "id": "gemini-3-pro-preview", 
            "name": "Gemini 3.0 Pro", 
            "badge": "Smart",
            "description": "High reasoning capability. Best for complex scenario generation." 
        }
    ]


class ScenarioRequest(BaseModel):
    contents: List[Dict[str, Any]]
    model: Optional[str] = "gemini-2.5-flash"
    generation_config: Optional[Dict[str, Any]] = None

@router.post("/tools/scenario-generate")
async def generate_scenario(req: ScenarioRequest):
    """Proxy request to Gemini for scenario generation (secures API Key)"""
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured on server")

    # Use specified model or default to 2.5 Flash
    model_name = req.model or "gemini-2.5-flash"

    # Direct pass-through (Validated that 2.5/3.0 exist in this environment)
    if not model_name.startswith("gemini"):
         raise HTTPException(status_code=400, detail="Only Gemini models are supported for this endpoint")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.gemini_api_key}"

    payload = {"contents": req.contents}
    if req.generation_config:
        payload["generation_config"] = req.generation_config

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                url,
                json=payload,
                timeout=60.0 # Allow longer timeout for generation
            )
            
            if res.status_code != 200:
                print(f"Scenario Gen Error: {res.text}")
                raise HTTPException(status_code=res.status_code, detail=f"Gemini Error: {res.text}")
                
            data = res.json()
            # Extract text from standard Gemini response
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"text": text}
            except (KeyError, IndexError):
                raise HTTPException(status_code=500, detail="Invalid response format from Gemini")
                
        except Exception as e:
            print(f"Scenario Gen Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))


class ImageGenerationRequest(BaseModel):
    prompt: str

@router.post("/tools/image-generate")
async def generate_image(req: ImageGenerationRequest):
    """Proxy request to Imagen for avatar generation"""
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured")

    # Use Imagen 4 (3.0 not available)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={settings.gemini_api_key}"

    async with httpx.AsyncClient() as client:
        try:
            # Imagen API format
            payload = {
                "instances": [
                    { "prompt": req.prompt }
                ],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "1:1"
                }
            }
            
            res = await client.post(
                url,
                json=payload,
                timeout=30.0
            )
            
            if res.status_code != 200:
                print(f"Imagen Error: {res.text}")
                raise HTTPException(status_code=res.status_code, detail=f"Imagen Error: {res.text}")
                
            data = res.json()
            # Extract base64 image
            # Response: { "predictions": [ { "bytesBase64Encoded": "..." } ] }
            try:
                b64 = data["predictions"][0]["bytesBase64Encoded"]
                mime_type = data["predictions"][0].get("mimeType", "image/png")
                return {"image": f"data:{mime_type};base64,{b64}"}
            except (KeyError, IndexError):
                raise HTTPException(status_code=500, detail="Invalid response from Imagen")
                
        except Exception as e:
            print(f"Image Gen Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))
