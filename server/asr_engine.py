"""
ASR 推理引擎 - 使用 Faster Whisper
"""
import os

# 自定义模型保存路径
MODEL_PATH = "/data/lzm/model/faster_whisper"
os.environ["HF_HOME"] = MODEL_PATH
os.environ["HF_CACHE_DIR"] = MODEL_PATH

import yaml
import torch
import numpy as np
from typing import Optional, List, Dict, Any


class ASREngine:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.model = None
        self.device = self.config.get("asr", {}).get("device", "cuda")
        self.model_size = self.config.get("asr", {}).get("whisper_size", "large-v3")

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def load_model(self):
        """加载 Faster Whisper 模型"""
        print(f"正在加载 Faster Whisper 模型: {self.model_size}")

        try:
            from faster_whisper import WhisperModel
            # 使用 int8 量化减少显存占用
            # download_root 指定本地模型路径
            self.model = WhisperModel(
                self.model_size,
                device="cuda",
                compute_type="int8",
                download_root="/data/lzm/model/faster_whisper"
            )
            print(f"模型加载成功: {self.model_size}")
        except Exception as e:
            raise RuntimeError(f"无法加载模型: {e}")

    def transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """转写音频

        Args:
            audio_data: 原始音频字节

        Returns:
            {
                "segments": [
                    {
                        "speaker": "Speaker 1",
                        "text": "转写文本",
                        "start": 0.0,
                        "end": 2.5,
                        "language": "zh"
                    }
                ]
            }
        """
        # 将字节转换为 numpy 数组
        audio_array = self._bytes_to_array(audio_data)

        # 使用 Faster Whisper 转写
        result = self.model.transcribe(audio_array, language=None)

        segments = []
        for seg in result.segments:
            segments.append({
                "speaker": "Speaker 1",
                "text": seg.text.strip(),
                "start": seg.start,
                "end": seg.end,
                "language": result.language or "auto"
            })

        return {"segments": segments}

    def _bytes_to_array(self, audio_bytes: bytes) -> np.ndarray:
        """将音频字节转换为 numpy 数组"""
        # 假设音频是 16-bit PCM 格式
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        # 转换为 float32
        audio = audio.astype(np.float32) / 32768.0
        return audio

    def get_device(self) -> str:
        """获取当前设备"""
        return self.device


if __name__ == "__main__":
    # 测试
    engine = ASREngine()
    engine.load_model()
    print(f"使用设备: {engine.get_device()}")
