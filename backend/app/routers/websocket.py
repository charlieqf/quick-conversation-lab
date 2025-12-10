"""
WebSocket Router - Voice session WebSocket endpoints
"""
import json
import time
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional

from app.adapters.base import SessionConfig, AudioConfig, VoiceConfig, AdapterStatus
from app.adapters.gemini import GeminiAdapter

router = APIRouter()

# Registry of available adapters
ADAPTERS = {
    "gemini": GeminiAdapter,
    # Add more adapters here
}


@router.websocket("/ws/{model_id}")
async def websocket_endpoint(websocket: WebSocket, model_id: str):
    """
    WebSocket endpoint for voice sessions.
    
    Protocol:
    1. Client connects
    2. Client sends: {"type": "session.create", "payload": {...}}
    3. Server responds: {"type": "session.created", "payload": {...}}
    4. Client sends: {"type": "audio.input", "payload": {"data": "base64...", "sequence": N}}
    5. Server sends: {"type": "audio.output", "payload": {...}}
    6. Server sends: {"type": "transcription", "payload": {...}}
    7. Client sends: {"type": "session.end"} or disconnects
    """
    await websocket.accept()
    
    # Validate model
    if model_id not in ADAPTERS:
        await websocket.send_json({
            "type": "error",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "code": 4002,
                "message": f"Model '{model_id}' not found"
            }
        })
        await websocket.close(code=4002)
        return
    
    # Create adapter instance
    adapter_class = ADAPTERS[model_id]
    adapter = adapter_class()
    
    # Message handlers
    audio_sequence = 0
    
    # Input guards state
    last_audio_time = time.time()
    audio_chunks_in_window = 0
    last_client_sequence = -1
    
    def on_audio(data: str, sequence: int, is_final: bool):
        nonlocal audio_sequence
        audio_sequence = sequence
        asyncio.create_task(websocket.send_json({
            "type": "audio.output",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "data": data,
                "sequence": sequence,
                "isFinal": is_final
            }
        }))
    
    def on_transcription(role: str, text: str, is_final: bool):
        if role == "system" and text == "TURN_COMPLETE":
            asyncio.create_task(websocket.send_json({
                "type": "turn.complete",
                "timestamp": int(time.time() * 1000),
                "payload": {}
            }))
        else:
            asyncio.create_task(websocket.send_json({
                "type": "transcription",
                "timestamp": int(time.time() * 1000),
                "payload": {
                    "role": role,
                    "text": text,
                    "isFinal": is_final
                }
            }))
    
    async def handle_error_async(code: int, message: str):
        try:
            await websocket.send_json({
                "type": "error",
                "timestamp": int(time.time() * 1000),
                "payload": {
                    "code": code,
                    "message": message
                }
            })
            # Use standard WS codes: 1008 (Policy Violation) for user errors, 1011 (Internal Error) for others
            ws_close_code = 1008 if code < 4100 else 1011
            await websocket.close(code=ws_close_code)
        except Exception:
            # If sending fails (e.g. socket already closed), just ensure we cleanup
            pass

    def on_error(code: int, message: str):
        asyncio.create_task(handle_error_async(code, message))
    
    # Register callbacks
    adapter.on_audio_received(on_audio)
    adapter.on_transcription(on_transcription)
    adapter.on_error(on_error)
    
    session_id: Optional[str] = None
    
    try:
        while True:
            # Receive message from client
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")
            payload = msg.get("payload", {})
            request_id = msg.get("requestId")
            
            if msg_type == "session.create":
                # Reset guard state for new session
                audio_sequence = 0
                last_client_sequence = -1
                audio_chunks_in_window = 0
                last_audio_time = time.time()
                
                # Create session
                session_id = f"sess-{int(time.time() * 1000)}"
                
                # Get model capabilities
                cap = adapter.capabilities
                
                # FIX: Reject disabled models early
                if not cap.is_enabled:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": int(time.time() * 1000),
                        "payload": {
                            "code": 4003,
                            "message": f"Model '{model_id}' is disabled (check API key)"
                        }
                    })
                    await websocket.close(code=4003)
                    return

                requested_sample_rate = payload.get("audio", {}).get("sampleRate", cap.default_sample_rate)
                requested_encoding = payload.get("audio", {}).get("encoding", cap.default_encoding)
                
                # Validate and enforce sample rate
                if requested_sample_rate not in cap.supported_sample_rates:
                    negotiated_sample_rate = cap.default_sample_rate
                else:
                    negotiated_sample_rate = requested_sample_rate
                    
                # FIX: Validate encoding
                if requested_encoding not in cap.supported_encodings:
                     await handle_error_async(4003, f"Unsupported encoding: {requested_encoding}. Supported: {cap.supported_encodings}")
                     return
                
                config = SessionConfig(
                    model_id=model_id,
                    audio=AudioConfig(
                        sample_rate=negotiated_sample_rate,
                        encoding=requested_encoding,
                        channels=payload.get("audio", {}).get("channels", 1)
                    ),
                    voice=VoiceConfig(
                        voice_id=payload.get("voice", {}).get("voiceId", "Kore"),
                        language=payload.get("voice", {}).get("language", "zh-CN")
                    ),
                    system_instruction=payload.get("session", {}).get("systemInstruction", ""),
                    max_duration=payload.get("session", {}).get("maxDuration", 600)
                )
                
                await adapter.connect(config)
                
                # FIX: Check if connection actually succeeded using Enum
                if adapter.status != AdapterStatus.CONNECTED:
                    # Error is already emitted by adapter via on_error callback if connect failed
                    # But we ensure we return if status is not connected
                    if websocket.client_state.name == "CONNECTED": # Check if WS still open
                         await websocket.close(code=4001)
                    return
                
                await websocket.send_json({
                    "type": "session.created",
                    "timestamp": int(time.time() * 1000),
                    "requestId": request_id,
                    "payload": {
                        "sessionId": session_id,
                        "negotiated": {
                            "sampleRate": config.audio.sample_rate,
                            "encoding": config.audio.encoding,
                            "voiceId": config.voice.voice_id
                        },
                        "capabilities": {
                            "transcription": cap.supports_transcription,
                            "interruption": cap.supports_interruption
                        }
                    }
                })
            
            elif msg_type == "audio.input":
                # Forward audio to model
                data = payload.get("data", "")
                sequence = payload.get("sequence", 0)
                
                # Guard 1: Max payload size (64KB base64 ~= 48KB binary)
                if len(data) > 64 * 1024:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": int(time.time() * 1000),
                        "payload": {
                            "code": 4003,
                            "message": "Audio chunk too large (max 64KB)"
                        }
                    })
                    continue

                # Guard 2: Sequence check (must be strictly increasing)
                if sequence <= last_client_sequence:
                    # Drop out-of-order or duplicate packets
                    continue
                last_client_sequence = sequence
                
                # Guard 3: Rate limiting (token bucket or simple counter)
                # Simple counter per second
                current_time = time.time()
                if current_time - last_audio_time >= 1.0:
                    audio_chunks_in_window = 0
                    last_audio_time = current_time
                
                audio_chunks_in_window += 1
                if audio_chunks_in_window > 50: # Rate limit
                     if audio_chunks_in_window > 100:
                         # Abuse detected, close connection
                         await websocket.close(code=1008, reason="Rate limit exceeded")
                         return
                     
                     # Warn once
                     if audio_chunks_in_window == 51:
                         await websocket.send_json({
                            "type": "warning",
                            "timestamp": int(time.time() * 1000),
                            "payload": {"code": 4004, "message": "Rate limit exceeded (audio dropping)"}
                         })
                     continue

                await adapter.send_audio(data, sequence)
            
            elif msg_type == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": int(time.time() * 1000)
                })
            
            elif msg_type == "session.end":
                # End session
                break
    
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "code": 4006,
                "message": "Invalid JSON message"
            }
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "code": 4100,
                "message": str(e)
            }
        })
    finally:
        # Cleanup
        await adapter.disconnect()
