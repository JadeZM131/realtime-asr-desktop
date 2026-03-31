"""
音频捕获模块
从虚拟声卡（VB-Cable）捕获系统音频
"""
import pyaudio
import numpy as np
import threading
import queue
from typing import Optional, Callable


class AudioCapture:
    """音频捕获器"""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 4096,
        format_type: int = pyaudio.paInt16,
        channels: int = 1,
        device_index: Optional[int] = None
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.format_type = format_type
        self.channels = channels
        self.device_index = device_index

        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream = None
        self.is_capturing = False

        self.audio_queue: queue.Queue = queue.Queue()
        self.callback: Optional[Callable] = None

    def list_devices(self) -> list:
        """列出所有音频设备"""
        if self.audio is None:
            self.audio = pyaudio.PyAudio()

        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                "index": i,
                "name": info["name"],
                "channels": info["maxInputChannels"]
            })
        return devices

    def find_vb_cable(self) -> Optional[int]:
        """查找 VB-Cable 设备"""
        devices = self.list_devices()
        for dev in devices:
            if "cable" in dev["name"].lower() or "virtual" in dev["name"].lower():
                return dev["index"]
        return None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频流回调"""
        if status:
            print(f"音频回调状态: {status}")

        # 放入队列
        self.audio_queue.put(in_data)

        # 如果有回调，调用
        if self.callback:
            self.callback(in_data)

        return None, pyaudio.paContinue

    def start(self, device_index: Optional[int] = None):
        """开始捕获音频"""
        if self.is_capturing:
            print("已经在捕获中")
            return

        if self.audio is None:
            self.audio = pyaudio.PyAudio()

        # 使用指定设备或自动查找 VB-Cable
        device = device_index or self.device_index or self.find_vb_cable()

        if device is None:
            # 使用默认输入设备
            print("未找到 VB-Cable，使用默认设备")
            device = None
        else:
            print(f"使用音频设备: {device}")

        try:
            self.stream = self.audio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            self.is_capturing = True
            print("音频捕获已开始")

        except Exception as e:
            print(f"启动音频捕获失败: {e}")
            raise

    def stop(self):
        """停止捕获音频"""
        if not self.is_capturing:
            return

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self.is_capturing = False
        print("音频捕获已停止")

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """获取音频块"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def set_callback(self, callback: Callable):
        """设置音频回调函数"""
        self.callback = callback

    def close(self):
        """关闭音频"""
        self.stop()
        if self.audio:
            self.audio.terminate()
            self.audio = None


def get_audio_devices() -> list:
    """获取所有音频输入设备"""
    audio = pyaudio.PyAudio()
    devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append({
                "index": i,
                "name": info["name"]
            })
    audio.terminate()
    return devices


if __name__ == "__main__":
    # 测试列出设备
    devices = get_audio_devices()
    print("可用音频输入设备:")
    for dev in devices:
        print(f"  [{dev['index']}] {dev['name']}")
