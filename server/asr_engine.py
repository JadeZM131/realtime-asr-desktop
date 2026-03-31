"""
VibeVoice-ASR 推理引擎
"""
import os
import yaml
import torch
import numpy as np
from typing import Optional, List, Dict, Any
from huggingface_hub import snapshot_download


class ASREngine:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.model = None
        self.device = self.config.get("asr", {}).get("device", "cuda")

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def load_model(self):
        """加载 VibeVoice-ASR 模型"""
        model_name = self.config.get("asr", {}).get("model", "microsoft/VibeVoice-ASR")

        print(f"正在加载模型: {model_name}")

        # 如果模型未下载，尝试下载
        model_path = os.path.join("./models", model_name.replace("/", "_"))
        if not os.path.exists(model_path):
            print("模型未找到，正在从 HuggingFace 下载...")
            snapshot_download(model_name, local_dir=model_path)

        # 导入 VibeVoice-ASR 并加载模型
        # 注意：实际使用时需要根据 VibeVoice-ASR 的 API 进行调整
        try:
            from VibeVoice_ASR import VibeVoiceASR
            self.model = VibeVoiceASR(model_path if os.path.exists(model_path) else model_name)
            self.model.to(self.device)
            print("模型加载成功")
        except ImportError:
            print("警告: VibeVoice-ASR 未安装，使用 Faster Whisper 作为备选")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """加载备用模型（Faster Whisper）"""
        try:
            from faster_whisper import WhisperModel
            model_size = self.config.get("asr", {}).get("whisper_size", "large-v3")
            self.model = WhisperModel(model_size, device="cuda", compute_type="int8")
            self.is_fallback = True
            print(f"已加载 Faster Whisper {model_size} 作为备选")
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

        if self.is_fallback:
            # 使用 Faster Whisper
            result = self.model.transcribe(audio_array, language=None)
            segments = []
            for seg in result.segments:
                segments.append({
                    "speaker": "Speaker 1",
                    "text": seg.text,
                    "start": seg.start,
                    "end": seg.end,
                    "language": result.language or "auto"
                })
            return {"segments": segments}
        else:
            # 使用 VibeVoice-ASR
            result = self.model.transcribe(audio_array)
            return result

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
