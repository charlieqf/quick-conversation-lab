import os
import json
import base64
import asyncio
import uuid
import gzip
import websockets
from typing import Optional, List, Dict, Any
from .base import BaseModelAdapter, ModelCapabilities, AdapterStatus, SessionConfig
from app.config import settings

# Protocol Constants
PROTOCOL_VERSION = 0b0001
DEFAULT_HEADER_SIZE = 0b0001

# Message Type
CLIENT_FULL_REQUEST = 0b0001
CLIENT_AUDIO_ONLY_REQUEST = 0b0010
SERVER_FULL_RESPONSE = 0b1001
SERVER_ACK = 0b1011
SERVER_ERROR_RESPONSE = 0b1111

# Message Type Specific Flags
NO_SEQUENCE = 0b0000
MSG_WITH_EVENT = 0b0100
NEG_SEQUENCE = 0b0010

# Message Serialization
NO_SERIALIZATION = 0b0000
JSON = 0b0001

# Message Compression
NO_COMPRESSION = 0b0000
GZIP = 0b0001

class DoubaoAdapter(BaseModelAdapter):
    """Adapter for ByteDance Doubao End-to-End Realtime Voice (Volcengine Openspeech)."""

    def __init__(self):
        super().__init__()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._response_in_progress: bool = False
        self._session_id: str = str(uuid.uuid4())
        self._logid: str = ""

    @property
    def id(self) -> str:
        return "doubao-realtime"

    @property
    def name(self) -> str:
        return "Doubao End-to-End Voice"

    @property
    def provider(self) -> str:
        return "ByteDance"

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            id=self.id,
            name=self.name,
            provider=self.provider,
            is_enabled=True,
            supported_sample_rates=[24000],
            supported_encodings=["pcm_s16le"],
            default_sample_rate=24000,
            default_encoding="pcm_s16le",
            available_voices=[
                {"id": "zh_female_vv_jupiter_bigtts", "name": "VV (Female)", "gender": "Female", "style": "Standard"},
                {"id": "zh_female_xiaohe_jupiter_bigtts", "name": "Xiaohe (Female)", "gender": "Female", "style": "Standard"},
                {"id": "zh_male_yunzhou_jupiter_bigtts", "name": "Yunzhou (Male)", "gender": "Male", "style": "Standard"},
                {"id": "zh_male_xiaotian_jupiter_bigtts", "name": "Xiaotian (Male)", "gender": "Male", "style": "Standard"},
            ],
            default_voice="zh_female_vv_jupiter_bigtts",
            supports_transcription=True,
            supports_interruption=True,
        )

    def _generate_header(self, message_type=CLIENT_FULL_REQUEST, flags=MSG_WITH_EVENT, serial=JSON, compression=GZIP):
        header = bytearray()
        header.append((PROTOCOL_VERSION << 4) | DEFAULT_HEADER_SIZE)
        header.append((message_type << 4) | flags)
        header.append((serial << 4) | compression)
        header.append(0x00)  # Reserved
        return header

    def _parse_response(self, res: bytes) -> Dict[str, Any]:
        if not res:
            return {}
            
        if not isinstance(res, (bytes, bytearray)):
            print(f"Doubao: Error - _parse_response received {type(res)}, expected bytes")
            return {}

        if len(res) < 4:
            return {}
        
        header_size = res[0] & 0x0f
        message_type = res[1] >> 4
        flags = res[1] & 0x0f
        serial = res[2] >> 4
        compression = res[2] & 0x0f
        
        payload = res[header_size * 4:]
        result = {"message_type": message_type}
        start = 0
        
        if message_type in [SERVER_FULL_RESPONSE, SERVER_ACK]:
            if flags & NEG_SEQUENCE:
                start += 4
            if flags & MSG_WITH_EVENT:
                if len(payload) < start + 4:
                    return result
                result["event"] = int.from_bytes(payload[start:start+4], "big")
                start += 4
            
            payload = payload[start:]
            if len(payload) >= 4:
                sid_size = int.from_bytes(payload[:4], "big")
                if len(payload) < 4 + sid_size:
                    return result
                result["session_id"] = payload[4:4+sid_size].decode("utf-8", errors="ignore")
                payload = payload[4+sid_size:]
                if len(payload) >= 4:
                    payload_size = int.from_bytes(payload[:4], "big")
                    if len(payload) < 4 + payload_size:
                         return result
                    data = payload[4:4+payload_size]
                    if compression == GZIP:
                        try:
                            data = gzip.decompress(data)
                        except Exception as ge:
                            print(f"Doubao GZIP Error: {ge}")
                            return result
                    
                    if serial == JSON:
                        try:
                            result["payload"] = json.loads(data.decode("utf-8"))
                        except Exception as je:
                            print(f"Doubao JSON Error: {je}")
                    else:
                        result["payload"] = data
        elif message_type == SERVER_ERROR_RESPONSE:
            if len(payload) >= 8:
                result["code"] = int.from_bytes(payload[:4], "big")
                p_size = int.from_bytes(payload[4:8], "big")
                if len(payload) >= 8 + p_size:
                    result["error"] = payload[8:8+p_size].decode("utf-8", errors="ignore")
            
        return result

    async def connect(self, config: SessionConfig) -> None:
        # Use settings if available, otherwise fallback to os.getenv as backup
        app_id = settings.volc_app_id or os.getenv("VOLC_APP_ID")
        # In the context of ByteDance, config.api_key from frontend "Volcengine Key" field is the Access Token
        # Otherwise use the server-configured volc_access_key
        access_token = config.api_key or settings.volc_access_key or os.getenv("VOLC_ACCESS_KEY")
        
        if not app_id or not access_token:
            self._status = AdapterStatus.ERROR
            self._emit_error(4001, "Doubao AppID or Access Token missing")
            return

        url = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"
        headers = {
            "X-Api-App-ID": app_id,
            "X-Api-Access-Key": access_token,
            "X-Api-Resource-Id": "volc.speech.dialog",
            "X-Api-App-Key": "PlgvMymc7f3tQnJ6",
            "X-Api-Connect-Id": str(uuid.uuid4())
        }

        try:
            self._status = AdapterStatus.CONNECTING
            self._ws = await websockets.connect(url, additional_headers=headers, ping_interval=None)
            
            # Retrieve LogID safely (attribute name changed in recent websockets versions)
            self._logid = ""
            if hasattr(self._ws, "response_headers"):
                self._logid = self._ws.response_headers.get("X-Tt-Logid", "")
            elif hasattr(self._ws, "response") and hasattr(self._ws.response, "headers"):
                self._logid = self._ws.response.headers.get("X-Tt-Logid", "")
            
            print(f"Doubao: Connected. LogID: {self._logid}")
            self._emit_transcription("system", f"Doubao: Connected. LogID: {self._logid}", True)

            # 1. StartConnection
            conn_req = bytearray(self._generate_header())
            conn_req.extend(int(1).to_bytes(4, 'big')) # Event ID 1
            payload = gzip.compress(b"{}")
            conn_req.extend(len(payload).to_bytes(4, 'big'))
            conn_req.extend(payload)
            await self._ws.send(conn_req)
            
            resp = await self._ws.recv()
            if isinstance(resp, str):
                raise Exception(f"Doubao StartConnection received text frame instead of binary: {resp[:100]}")
            
            shake1 = self._parse_response(resp)
            m_type1 = shake1.get("message_type")
            
            if m_type1 == SERVER_ERROR_RESPONSE:
                err = shake1.get('error', 'Unknown Error')
                self._emit_transcription("system", f"Doubao: StartConnection Failed: {err}", True)
                raise Exception(f"Doubao StartConnection failure: {err}")
            
            # CRITICAL: Use server-provided session_id if available
            if shake1.get("session_id"):
                self._session_id = shake1["session_id"]
                print(f"Doubao: Switched to server session ID: {self._session_id}")
            
            self._emit_transcription("system", f"Doubao: StartConnection successful. SID={self._session_id[:8]}...", True)

            # 2. StartSession
            session_req_data = {
                "asr": {"extra": {"end_smooth_window_ms": 1500}},
                "tts": {
                    "speaker": config.voice.voice_id or self.capabilities.default_voice,
                    "audio_config": {"channel": 1, "format": "pcm_s16le", "sample_rate": 24000}
                },
                "dialog": {
                    "bot_name": "豆包",
                    "system_role": config.system_instruction or "你是一个乐于助人的AI助手。",
                    "speaking_style": "你的说话风格简洁明了，语速适中，语调自然。",
                    "extra": {
                        "input_mod": "audio", 
                        "model": "O",
                        "strict_audit": False
                    }
                }
            }
            payload = gzip.compress(json.dumps(session_req_data).encode("utf-8"))
            session_req = bytearray(self._generate_header())
            session_req.extend(int(100).to_bytes(4, 'big')) # Event ID 100
            session_req.extend(len(self._session_id).to_bytes(4, 'big'))
            session_req.extend(self._session_id.encode("utf-8"))
            session_req.extend(len(payload).to_bytes(4, 'big'))
            session_req.extend(payload)
            await self._ws.send(session_req)
            
            resp = await self._ws.recv()
            if isinstance(resp, str):
                raise Exception(f"Doubao StartSession received text frame: {resp[:100]}")
                
            shake2 = self._parse_response(resp)
            m_type2 = shake2.get("message_type")
            
            if m_type2 == SERVER_ERROR_RESPONSE:
                 err = shake2.get('error', 'Unknown Error')
                 self._emit_transcription("system", f"Doubao: StartSession Failed: {err}", True)
                 raise Exception(f"Doubao StartSession failure: {err}")
                 
            self._emit_transcription("system", "Doubao: StartSession successful.", True)
            
            # Start receive loop
            self._status = AdapterStatus.CONNECTED
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._emit_transcription("system", "Doubao: Handshake complete. Waiting for input...", True)

        except Exception as e:
            print(f"Doubao Connect Error: {e}")
            import traceback
            traceback.print_exc()
            self._status = AdapterStatus.ERROR
            self._emit_error(4002, f"Failed to connect: {str(e)}")
            await self.disconnect()

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        self._status = AdapterStatus.DISCONNECTED

    async def send_audio(self, audio_base64: str, sequence: int) -> None:
        if not self._ws or self._status != AdapterStatus.CONNECTED:
            return
        
        try:
            audio_data = base64.b64decode(audio_base64)
            # self._emit_transcription("system", f"Debug: Sending audio data {len(audio_data)} bytes", True)
            
            # Binary Audio-only request
            req = bytearray(self._generate_header(
                message_type=CLIENT_AUDIO_ONLY_REQUEST,
                serial=NO_SERIALIZATION,
                compression=GZIP
            ))
            req.extend(int(200).to_bytes(4, 'big')) # Audio Event ID
            req.extend(len(self._session_id).to_bytes(4, 'big'))
            req.extend(self._session_id.encode("utf-8"))
            payload = gzip.compress(audio_data)
            req.extend(len(payload).to_bytes(4, 'big'))
            req.extend(payload)
            await self._ws.send(req)
        except Exception as e:
            print(f"Doubao send error: {e}")
            self._emit_transcription("system", f"Doubao: Audio send error: {str(e)}", True)

    def _pcm_to_wav_base64(self, pcm_bytes: bytes, sample_rate: int = 24000) -> str:
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
        msg_count = 0
        try:
            async for message in self._ws:
                msg_count += 1
                if isinstance(message, str):
                    # self._emit_transcription("system", f"Debug: Received text frame {msg_count}", False)
                    continue
                
                if not isinstance(message, (bytes, bytearray)):
                    continue

                parsed = self._parse_response(message)
                if not parsed:
                    continue

                m_type = parsed.get("message_type")

                if m_type == SERVER_ERROR_RESPONSE:
                    err_msg = parsed.get('error', 'Unknown Error')
                    self._emit_error(4003, f"Doubao Server Error: {err_msg}")
                    continue
                
                # SERVER_ACK (Type 11) contains raw audio data
                if m_type == SERVER_ACK:
                    payload = parsed.get("payload")
                    if payload and isinstance(payload, bytes):
                        try:
                            wav_b64 = self._pcm_to_wav_base64(payload)
                            self._emit_audio(wav_b64, 0)
                        except Exception as ae:
                            print(f"Doubao ACK Audio Error: {ae}")
                    continue

                # SERVER_FULL_RESPONSE (Type 9) contains JSON payloads
                payload = parsed.get("payload")
                if not payload:
                    continue
                
                if isinstance(payload, dict):
                    # Audio in base64 format
                    if "audio" in payload:
                        try:
                            audio_val = payload["audio"]
                            if audio_val:
                                pcm = base64.b64decode(audio_val)
                                wav_b64 = self._pcm_to_wav_base64(pcm)
                                self._emit_audio(wav_b64, 0)
                        except Exception as ae:
                            print(f"Doubao Audio Decode Error: {ae}")
                    
                    # Text transcription - check both 'content' and 'text' keys
                    if "content" in payload:
                        self._emit_transcription("model", str(payload["content"]), is_final=False)
                    elif "text" in payload:
                        self._emit_transcription("model", str(payload["text"]), is_final=False)
                    
                    # ASR results (user speech recognition)
                    if "results" in payload:
                        try:
                            results = payload["results"]
                            if isinstance(results, list):
                                for r in results:
                                    if isinstance(r, dict) and r.get("text"):
                                        self._emit_transcription("user", str(r["text"]), is_final=r.get("is_final", False))
                        except Exception:
                            pass
                    
                    if payload.get("is_last") or payload.get("no_content"):
                        self._emit_transcription("system", "TURN_COMPLETE", True)
                else:
                    # Raw payload (not JSON) - could be audio
                    if isinstance(payload, bytes):
                        try:
                            wav_b64 = self._pcm_to_wav_base64(payload)
                            self._emit_audio(wav_b64, 0)
                        except Exception:
                            pass

        except websockets.ConnectionClosed:
            self._status = AdapterStatus.DISCONNECTED
        except Exception as e:
            print(f"Doubao Loop Error: {e}")
            import traceback
            traceback.print_exc()
            self._emit_error(4004, f"Doubao Loop Error: {str(e)}")
