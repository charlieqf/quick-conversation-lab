"""
Eleven Labs Conversational AI Adapter
WebSocket-based real-time voice conversation
"""
import asyncio
import json
import base64
import websockets
from typing import Optional
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig
from app.config import settings


class ElevenLabsAdapter(BaseModelAdapter):
    """Adapter for Eleven Labs Conversational AI using WebSockets"""
    
    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._conversation_id: Optional[str] = None
    
    @property
    def id(self) -> str:
        return "elevenlabs-realtime"
    
    @property
    def name(self) -> str:
        return "Eleven Labs Conversational AI"
    
    @property
    def provider(self) -> str:
        return "Eleven Labs"
    
    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=True,
            supported_sample_rates=[16000],
            supported_encodings=["pcm_s16le"],
            default_sample_rate=16000,
            default_encoding="pcm_s16le",
            available_voices=[
                # Eleven Labs uses the agent's configured voice
                {"id": "agent_default", "name": "Agent Default", "gender": "Neutral", "style": "Conversational"}
            ],
            default_voice="agent_default",
            supports_transcription=True,
            supports_interruption=True
        )

    async def connect(self, config: SessionConfig) -> None:
        api_key = config.api_key or settings.elevenlabs_api_key
        agent_id = settings.elevenlabs_agent_id
        
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Eleven Labs API key not configured")
            return
            
        if not agent_id:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Eleven Labs Agent ID not configured")
            return
        
        # WebSocket URL with agent_id
        url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        headers = {
            "xi-api-key": api_key
        }

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, additional_headers=headers)
            self._status = AdapterStatus.CONNECTED
            
            # IMMEDIATELY send conversation initialization with prompt override
            # Must be sent BEFORE server sends conversation_initiation_metadata
            system_prompt = config.system_instruction or "You are a helpful AI assistant."
            print(f"ElevenLabs: Sending prompt override (length={len(system_prompt)})")
            
            # CORRECT FORMAT per official docs:
            # https://elevenlabs.io/docs/conversational-ai/customization/personalization
            init_message = {
                "type": "conversation_initiation_client_data",
                "conversation_config_override": {
                    "agent": {
                        "prompt": {
                            "prompt": system_prompt
                        },
                        "first_message": "您好，我是李医生。今天有什么可以帮您的？",
                        "language": "zh"
                    }
                }
            }
            await self._ws.send(json.dumps(init_message))
            print(f"ElevenLabs: Sent prompt override successfully")

            
            # NOW start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            
        except Exception as e:
            print(f"ElevenLabs Connect Error: {e}")
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect to Eleven Labs: {str(e)}")
            await self.disconnect()

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
            
        if self._ws:
            try:
                await self._ws.close()
            except:
                pass
            self._ws = None
            
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return

        # Eleven Labs expects audio in a specific format
        msg = {
            "user_audio_chunk": audio_base64
        }
        try:
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            print(f"ElevenLabs send audio error: {e}")

    def _pcm_to_wav_base64(self, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        """Convert raw PCM bytes to WAV base64 for frontend playback"""
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        header = b"".join([
            b"RIFF", (36 + data_size).to_bytes(4, "little"), b"WAVE",
            b"fmt ", (16).to_bytes(4, "little"), (1).to_bytes(2, "little"),
            num_channels.to_bytes(2, "little"), sample_rate.to_bytes(4, "little"),
            byte_rate.to_bytes(4, "little"), block_align.to_bytes(2, "little"),
            bits_per_sample.to_bytes(2, "little"), b"data", data_size.to_bytes(4, "little")
        ])
        return base64.b64encode(header + pcm_bytes).decode("ascii")

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    # Might be binary audio
                    if isinstance(message, bytes):
                        wav_b64 = self._pcm_to_wav_base64(message)
                        self._emit_audio(wav_b64, 0)
                    continue
                
                event_type = data.get("type")
                
                if event_type == "conversation_initiation_metadata":
                    self._conversation_id = data.get("conversation_initiation_metadata_event", {}).get("conversation_id")
                    print(f"ElevenLabs: Conversation started: {self._conversation_id}")
                    
                elif event_type == "audio":
                    # Audio chunk from agent
                    audio_event = data.get("audio_event", {})
                    audio_b64 = audio_event.get("audio_base_64")
                    if audio_b64:
                        try:
                            pcm = base64.b64decode(audio_b64)
                            wav_b64 = self._pcm_to_wav_base64(pcm)
                            self._emit_audio(wav_b64, 0)
                        except Exception as e:
                            print(f"ElevenLabs audio decode error: {e}")
                            
                elif event_type == "agent_response":
                    # Agent text response / transcript
                    agent_response = data.get("agent_response_event", {})
                    text = agent_response.get("agent_response")
                    if text:
                        self._emit_transcription("model", text, is_final=True)
                        
                elif event_type == "user_transcript":
                    # User speech transcript
                    user_transcript = data.get("user_transcription_event", {})
                    text = user_transcript.get("user_transcript")
                    if text:
                        self._emit_transcription("user", text, is_final=True)
                        
                elif event_type == "interruption":
                    # User interrupted agent
                    print("ElevenLabs: User interruption detected")
                    
                elif event_type == "agent_response_correction":
                    # Corrected agent response
                    pass
                    
                elif event_type == "ping":
                    # Respond to ping with pong
                    pong = {"type": "pong", "event_id": data.get("ping_event", {}).get("event_id")}
                    await self._ws.send(json.dumps(pong))
                    
                elif event_type == "error":
                    error_msg = data.get("error", "Unknown error")
                    print(f"ElevenLabs Error: {error_msg}")
                    self._emit_error(4003, f"Eleven Labs Error: {error_msg}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"ElevenLabs Receive Loop Error: {e}")
            import traceback
            traceback.print_exc()
