import os
import json
import base64
import asyncio
import websockets
from typing import Optional
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig


class TongyiAdapter(BaseModelAdapter):
    """Adapter for Alibaba Tongyi / Qwen Realtime (DashScope WS)."""

    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._response_in_progress: bool = False
        self._response_debounce_task: Optional[asyncio.Task] = None

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
            supported_sample_rates=[16000],
            supported_encodings=["pcm_s16le"],
            default_sample_rate=16000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "qwen2_default", "name": "Qwen Default", "gender": "Neutral", "style": "General"},
            ],
            default_voice="qwen2_default",
            supports_transcription=True,
            supports_interruption=True,
        )

    async def connect(self, config: SessionConfig) -> None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "DashScope API key not configured")
            return

        # Standard DashScope realtime endpoint; change to dashscope-intl if needed.
        url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen-omni-turbo-realtime"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, extra_headers=headers)
            self._status = AdapterStatus.CONNECTED

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Create session with VAD so the server detects turns
            session_create = {
                "type": "session.create",
                "data": {
                    "modalities": ["text", "audio"],
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "audio_sample_rate": config.audio.sample_rate,
                    "turn_detection": {"type": "vad"},
                    "instructions": config.system_instruction or "",
                },
            }
            await self._ws.send(json.dumps(session_create))

        except Exception as e:
            print(f"Tongyi Connect Error: {e}")
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect to Tongyi: {str(e)}")
            await self.disconnect()

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        if self._response_debounce_task:
            self._response_debounce_task.cancel()
            self._response_debounce_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        self._status = AdapterStatus.DISCONNECTED
        self._response_in_progress = False

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return

        msg = {
            "type": "input_audio_buffer.append",
            "data": {"audio": audio_base64},
        }
        try:
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            print(f"Tongyi send_audio error: {e}")

    async def _trigger_response_debounced(self, delay: float = 0.3):
        try:
            await asyncio.sleep(delay)
            self._response_debounce_task = None
            if not self._response_in_progress and self._ws:
                self._response_in_progress = True
                await self._ws.send(json.dumps({"type": "response.create"}))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Tongyi response.create error (debounced): {e}")
            self._response_in_progress = False

    def _pcm_to_wav_base64(self, audio_b64: str, sample_rate: int = 16000) -> str:
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
                payload = data.get("data", {}) or data  # some events nest under data

                if event_type == "session.created":
                    continue

                elif event_type == "response.output_audio.delta":
                    self._response_in_progress = True
                    audio_b64 = payload.get("audio") or payload.get("delta")
                    if audio_b64:
                        try:
                            pcm = base64.b64decode(audio_b64)
                            if len(pcm) < 4 or len(pcm) % 2 != 0:
                                continue
                            wav_b64 = self._pcm_to_wav_base64(audio_b64, 16000)
                            self._emit_audio(wav_b64, 0)
                        except Exception:
                            pass

                elif event_type == "response.output_text.delta":
                    self._response_in_progress = True
                    text = payload.get("text") or payload.get("delta")
                    if text:
                        self._emit_transcription("model", text, is_final=False)

                elif event_type == "response.completed":
                    self._response_in_progress = False
                    self._emit_transcription("system", "TURN_COMPLETE", True)

                elif event_type == "turn_detected":
                    if not self._response_in_progress:
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                        # Schedule a small delay to let the server auto-start; then trigger if needed
                        self._response_debounce_task = asyncio.create_task(
                            self._trigger_response_debounced(0.3)
                        )
                    else:
                        # If server already in progress, cancel any pending manual trigger
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                            self._response_debounce_task = None

                elif event_type == "error":
                    err_msg = payload.get("message") or str(payload)
                    self._response_in_progress = False
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                        self._response_debounce_task = None
                    self._emit_error(4003, f"Tongyi Error: {err_msg}")

        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"Tongyi Receive Loop Error: {e}")
            self._response_in_progress = False
