"""
WebSocket 客户端
与服务器通信，发送音频并接收转写结果
"""
import asyncio
import json
import base64
import threading
from typing import Optional, Callable, Dict, Any
import websockets


class WSClient:
    """WebSocket 客户端"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/ws/asr"

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.is_running = False

        self.callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None

        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.Event] = None

    async def _connect(self):
        """连接到服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            print(f"已连接到服务器: {self.uri}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            self.is_connected = False
            return False

    async def _disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False
        print("已断开连接")

    async def _send_audio(self, audio_data: bytes, translate: bool = False):
        """发送音频数据"""
        if not self.is_connected or not self.websocket:
            return False

        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            await self.websocket.send(json.dumps({
                "type": "audio",
                "data": audio_base64,
                "translate": translate
            }))
            return True
        except Exception as e:
            print(f"发送音频失败: {e}")
            return False

    async def _send_translate(self, text: str, source_lang: str = None, target_lang: str = "zh"):
        """发送翻译请求"""
        if not self.is_connected or not self.websocket:
            return False

        try:
            await self.websocket.send(json.dumps({
                "type": "translate",
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }))
            return True
        except Exception as e:
            print(f"发送翻译请求失败: {e}")
            return False

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            while self.is_running and self.websocket:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)

                    msg_type = data.get("type")

                    if msg_type == "result":
                        # 转写结果
                        if self.callback:
                            self.callback(data.get("data", {}))
                    elif msg_type == "translation":
                        # 翻译结果
                        if self.callback:
                            self.callback({"type": "translation", **data})
                    elif msg_type == "error":
                        # 错误
                        if self.error_callback:
                            self.error_callback(data.get("message", ""))

                except websockets.exceptions.ConnectionClosed:
                    print("连接已关闭")
                    break
                except Exception as e:
                    print(f"接收消息错误: {e}")

        finally:
            self.is_connected = False

    async def _run_async(self):
        """异步运行"""
        if await self._connect():
            self.is_running = True
            await self._receive_loop()

    def connect(self) -> bool:
        """同步连接"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._connect())
            return self.is_connected
        except Exception as e:
            print(f"连接错误: {e}")
            return False

    def start(self, callback: Optional[Callable] = None, error_callback: Optional[Callable] = None):
        """启动客户端（在后台线程运行）"""
        self.callback = callback
        self.error_callback = error_callback

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_async())

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

        # 等待连接
        import time
        for _ in range(50):  # 5秒超时
            if self.is_connected:
                return True
            time.sleep(0.1)

        return self.is_connected

    def stop(self):
        """停止客户端"""
        self.is_running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def send_audio(self, audio_data: bytes, translate: bool = False) -> bool:
        """发送音频（同步）"""
        if not self.is_connected:
            return False

        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._send_audio(audio_data, translate),
                    self._loop
                )
                return True
        except Exception as e:
            print(f"发送音频失败: {e}")
        return False

    def send_translate(self, text: str, source_lang: str = None, target_lang: str = "zh") -> bool:
        """发送翻译请求（同步）"""
        if not self.is_connected:
            return False

        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._send_translate(text, source_lang, target_lang),
                    self._loop
                )
                return True
        except Exception as e:
            print(f"发送翻译请求失败: {e}")
        return False


def create_client(host: str = "localhost", port: int = 8000) -> WSClient:
    """创建客户端实例"""
    return WSClient(host, port)


if __name__ == "__main__":
    # 测试
    client = create_client()
    print(f"目标服务器: {client.uri}")
