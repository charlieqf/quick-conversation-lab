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
        self._output_bits_per_sample: int = 16 # Default to 16, will update based on session.created

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
        # Allow BYOK
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=True,
            default_sample_rate=16000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "Cherry", "name": "Cherry", "gender": "Female", "style": "Sweet"},
                {"id": "Harry", "name": "Harry", "gender": "Male", "style": "Calm"},
                {"id": "qwen2_default", "name": "Qwen Default", "gender": "Neutral", "style": "General"},
            ],
            default_voice="Cherry",
            supports_transcription=True,
            supports_interruption=True,
        )

    async def connect(self, config: SessionConfig) -> None:
        api_key = config.api_key or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "DashScope API key not configured (Server or User)")
            return

        # Use qwen-omni-turbo-realtime (Stable WebSocket Model)
        # qwen3-omni-flash is HTTP-only or has different WS path currently.
        model = "qwen3-omni-flash-realtime" 
        
        # Using International Endpoint (Singapore) as verified with user key
        url = f"wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model={model}"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, additional_headers=headers)
            self._status = AdapterStatus.CONNECTED

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Start receive loop
            # Start receive loop (removed duplicate)

            # Define the initial session configuration
            # Based on Alibaba Cloud Qwen-Omni-Realtime documentation
            session_config_payload = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "voice": "Cherry",  # Default voice
                    "instructions": "You are a helpful assistant.",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm24", # Official docs say only pcm24 supported
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5, # Revert to default
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 800 # Match official example
                    }
                }
            }

            # Send session update to initialize the session
            await self._ws.send(json.dumps(session_config_payload))

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

        # Debug log for sending audio
        # if sequence % 50 == 0:
        #    print(f"Tongyi Sending audio seq={sequence} len={len(audio_base64)}")

        msg = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
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

    def _pcm_to_wav_base64(self, audio_b64: str, sample_rate: int = 24000) -> str:
        import io
        import wave
        
        # 官方文档使用 pyaudio 本地播放，因此不需要 WAV 头。
        # 我们的应用是 Web 前端，浏览器通常需要 WAV 头才能通过 decodeAudioData 识别采样率和格式。
        # 这里使用标准库 wave 生成带头的音频数据，替代之前手动拼接字节的“复杂”写法。
        
        pcm_bytes = base64.b64decode(audio_b64)
        
        with io.BytesIO() as wav_io:
            # 写入 WAV 头和数据
            with wave.open(wav_io, mode='wb') as wf:
                wf.setnchannels(1)      # 单声道
                wf.setsampwidth(2)      # 16-bit (2 bytes)
                wf.setframerate(sample_rate) # 24000Hz
                wf.writeframes(pcm_bytes)
            
            # 获取完整 WAV 文件的 bytes
            wav_bytes = wav_io.getvalue()
            
        return base64.b64encode(wav_bytes).decode("ascii")

    async def _receive_loop(self):
        print("Tongyi: --- New Session ---")
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type")
                payload = data.get("data", {}) or data

                # Log event summary
                if event_type not in ["response.audio.delta", "response.output_text.delta"]:
                    print(f"Tongyi Event: {event_type}")

                if event_type == "session.created":
                    session_obj = payload.get("session", {})
                    print(f"Tongyi Session Created: {json.dumps(session_obj)}")
                    continue

                elif event_type == "response.audio.delta":
                    self._response_in_progress = True
                    audio_b64 = payload.get("audio") or payload.get("delta")
                    if audio_b64:
                        try:
                            # Use 24000 Hz for Qwen Realtime (Confirmed by official Python SDK example)
                            wav_b64 = self._pcm_to_wav_base64(audio_b64, 24000)
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
                    print("Tongyi Response Completed.")

                elif event_type == "turn_detected":
                    print("Tongyi Turn Detected.")
                    if not self._response_in_progress:
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                        self._response_debounce_task = asyncio.create_task(
                            self._trigger_response_debounced(0.3)
                        )
                    else:
                        if self._response_debounce_task:
                            self._response_debounce_task.cancel()
                            self._response_debounce_task = None

                elif event_type == "input_audio_buffer.speech_started":
                     print("Tongyi Speech Started.")

                elif event_type == "input_audio_buffer.speech_stopped":
                     print("Tongyi Speech Stopped.")

                elif event_type == "error":
                    err_msg = payload.get("message") or str(payload)
                    self._response_in_progress = False
                    if self._response_debounce_task:
                        self._response_debounce_task.cancel()
                        self._response_debounce_task = None
                    self._emit_error(4003, f"Tongyi Error: {err_msg}")
                    print(f"Tongyi Error: {err_msg}")
        
        except websockets.ConnectionClosed:
            if self._status == AdapterStatus.CONNECTED:
                self._status = AdapterStatus.DISCONNECTED
            print("Tongyi Connection Closed.")
        except Exception as e:
            print(f"Tongyi Receive Loop Error: {e}")
            self._response_in_progress = False
