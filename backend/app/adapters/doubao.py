import os
import json
import base64
import asyncio
import websockets
from typing import Optional, List
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig


class DoubaoAdapter(BaseModelAdapter):
    """Adapter for ByteDance Doubao Realtime Voice (Volcengine Ark)."""

    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._response_in_progress: bool = False
        self._debounce_task: Optional[asyncio.Task] = None

    @property
    def id(self) -> str:
        return "doubao-realtime"

    @property
    def name(self) -> str:
        return "Doubao Realtime Voice"

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
            supported_sample_rates=[24000],
            supported_encodings=["pcm_s16le"],
            default_sample_rate=24000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "zh_female_kailangjiejie_moon", "name": "Moon (zh_female_kailangjiejie_moon)", "gender": "Female", "style": "Upbeat"},
                {"id": "zh_female_yuanqi_shaonv_mengmeng", "name": "Mengmeng (zh_female_yuanqi_shaonv_mengmeng)", "gender": "Female", "style": "Cute"},
                {"id": "zh_male_wennan_shuanglang", "name": "Shuanglang (zh_male_wennan_shuanglang)", "gender": "Male", "style": "Warm"},
            ],
            default_voice="zh_female_kailangjiejie_moon",
            supports_transcription=True,
            supports_interruption=True,
        )

    async def connect(self, config: SessionConfig) -> None:
        api_key = os.getenv("VOLC_API_KEY")
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Volcengine API key not configured")
            return

        url = "wss://ark.cn-beijing.volcengine.com/api/v3/realtime?model=doubao-seed-realtimevoice"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, extra_headers=headers)
            self._status = AdapterStatus.CONNECTED

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Create session with chosen voice and basic params
            session_create = {
                "type": "session.create",
                "voice": config.voice.voice_id,
                "temperature": 0.85,
                "max_tokens": 2048,
            }
            await self._ws.send(json.dumps(session_create))

        except Exception as e:
            print(f"Doubao Connect Error: {e}")
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect to Doubao: {str(e)}")
            await self.disconnect()

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._debounce_task:
            self._debounce_task.cancel()
            self._debounce_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        self._status = AdapterStatus.DISCONNECTED
        self._response_in_progress = False

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        """Send a user turn as an audio conversation item, then trigger response."""
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return

        try:
            # Create a user item with audio content
            await self._ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "role": "user",
                    "content": [
                        {
                            "type": "audio",
                            "mime_type": "audio/pcm",
                            "data": audio_base64
                        }
                    ]
                }
            }))

            # Request model response
            if not self._response_in_progress:
                self._response_in_progress = True
                await self._ws.send(json.dumps({"type": "response.create"}))

        except Exception as e:
            print(f"Doubao send_audio error: {e}")
            self._response_in_progress = False

    def _pcm_to_wav_base64(self, audio_b64: str, sample_rate: int = 24000) -> str:
        pcm_bytes = base64.b64decode(audio_b64)
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        chunk_size = 36 + data_size
        
        header = b"".join([
            b"RIFF",
            chunk_size.to_bytes(4, "little"),
            b"WAVE",
            b"fmt ",
            (16).to_bytes(4, "little"),
            (1).to_bytes(2, "little"),
            num_channels.to_bytes(2, "little"),
            sample_rate.to_bytes(4, "little"),
            byte_rate.to_bytes(4, "little"),
            block_align.to_bytes(2, "little"),
            bits_per_sample.to_bytes(2, "little"),
            b"data",
            data_size.to_bytes(4, "little")
        ])
        wav_bytes = header + pcm_bytes
        return base64.b64encode(wav_bytes).decode("ascii")

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type")

                if event_type == "response.audio.delta":
                    self._response_in_progress = True
                    b64_audio = data.get("delta") or data.get("audio")
                    if b64_audio:
                        try:
                            pcm = base64.b64decode(b64_audio)
                            if len(pcm) < 4 or len(pcm) % 2 != 0:
                                continue
                            wav_b64 = self._pcm_to_wav_base64(b64_audio, 24000)
                            self._emit_audio(wav_b64, 0)
                        except Exception:
                            pass

                elif event_type == "response.text.delta":
                    self._response_in_progress = True
                    text = data.get("delta") or data.get("text")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "response.done":
                    if self._response_in_progress:
                        self._response_in_progress = False
                        self._emit_transcription("system", "TURN_COMPLETE", True)

                elif event_type == "error":
                    err_msg = data.get("message") or str(data)
                    self._response_in_progress = False
                    self._emit_error(4003, f"Doubao Error: {err_msg}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"Doubao Receive Loop Error: {e}")
            self._response_in_progress = False
