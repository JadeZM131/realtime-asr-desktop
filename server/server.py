"""
WebSocket 语音转写服务器
支持实时语音转文字、说话人分离和翻译
"""
import asyncio
import json
import os
import yaml
import base64
import numpy as np
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import websockets

from asr_engine import ASREngine
from translator import create_translator


# 全局变量
asr_engine: Optional[ASREngine] = None
translator: Optional[Any] = None
config: Dict[str, Any] = {}


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def init_services():
    """初始化服务"""
    global asr_engine, translator, config

    config = load_config()
    print("配置加载完成:", config)

    # 初始化 ASR 引擎
    asr_engine = ASREngine()
    asr_engine.load_model()

    # 初始化翻译器（如果启用）
    trans_config = config.get("translator", {})
    if trans_config.get("enabled", False):
        provider = trans_config.get("provider", "deepl")
        api_key = trans_config.get("api_key", "")
        if api_key:
            translator = create_translator(provider, api_key)
            print(f"翻译服务已启用: {provider}")
        else:
            print("翻译已启用但未配置 API Key")


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"客户端连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"客户端断开，当前连接数: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)


manager = ConnectionManager()

app = FastAPI(title="Realtime ASR Server")


@app.get("/")
async def root():
    """健康检查"""
    return JSONResponse({
        "status": "ok",
        "model_loaded": asr_engine is not None and asr_engine.model is not None,
        "translator_enabled": translator is not None
    })


@app.websocket("/ws/asr")
async def websocket_asr(websocket: WebSocket):
    """ASR WebSocket 端点"""
    await manager.connect(websocket)

    audio_buffer = b""
    buffer_lock = asyncio.Lock()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "audio":
                # 接收音频数据
                audio_base64 = data.get("data", "")
                audio_bytes = base64.b64decode(audio_base64)

                async with buffer_lock:
                    audio_buffer += audio_bytes

                # 音频 buffer 足够时进行转写
                # 假设 16kHz, 16-bit, 单声道，每秒 32KB
                # 缓冲 2 秒数据进行转写（约 64KB）
                if len(audio_buffer) >= 64000:
                    try:
                        result = asr_engine.transcribe(audio_buffer)

                        # 如果翻译启用，翻译文本
                        if translator and data.get("translate", False):
                            for seg in result.get("segments", []):
                                try:
                                    seg["translated_text"] = translator.translate(
                                        seg.get("text", ""),
                                        source_lang=seg.get("language"),
                                        target_lang=config.get("translator", {}).get("default_target_lang", "zh")
                                    )
                                except Exception as e:
                                    print(f"翻译失败: {e}")
                                    seg["translated_text"] = ""

                        await manager.send_message(websocket, {
                            "type": "result",
                            "data": result
                        })

                    except Exception as e:
                        await manager.send_message(websocket, {
                            "type": "error",
                            "message": str(e)
                        })

                    # 清空 buffer
                    async with buffer_lock:
                        audio_buffer = b""

            elif msg_type == "translate":
                # 单独翻译请求
                if translator:
                    text = data.get("text", "")
                    target_lang = data.get("target_lang", "zh")

                    try:
                        translated = translator.translate(
                            text,
                            source_lang=data.get("source_lang"),
                            target_lang=target_lang
                        )
                        await manager.send_message(websocket, {
                            "type": "translation",
                            "original": text,
                            "translated": translated,
                            "target_lang": target_lang
                        })
                    except Exception as e:
                        await manager.send_message(websocket, {
                            "type": "error",
                            "message": f"翻译失败: {e}"
                        })
                else:
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": "翻译服务未启用"
                    })

            elif msg_type == "flush":
                # 强制刷新 buffer
                async with buffer_lock:
                    if audio_buffer:
                        try:
                            result = asr_engine.transcribe(audio_buffer)
                            await manager.send_message(websocket, {
                                "type": "result",
                                "data": result
                            })
                        except Exception as e:
                            print(f"flush 错误: {e}")
                    audio_buffer = b""

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        manager.disconnect(websocket)


def main():
    """启动服务器"""
    # 初始化服务
    init_services()

    # 启动 FastAPI
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)

    print(f"服务器启动中: {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
