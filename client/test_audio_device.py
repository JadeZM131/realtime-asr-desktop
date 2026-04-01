"""
测试音频设备可用性
"""
import pyaudio

audio = pyaudio.PyAudio()

print("所有音频设备详情:")
print("-" * 60)

for i in range(audio.get_device_count()):
    try:
        info = audio.get_device_info_by_index(i)
        print(f"设备 {i}: {info['name']}")
        print(f"  输入通道: {info['maxInputChannels']}")
        print(f"  输出通道: {info['maxOutputChannels']}")
        print(f"  默认采样率: {info['defaultSampleRate']}")

        # 尝试打开设备测试
        if info['maxInputChannels'] > 0:
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=1024
                )
                stream.stop_stream()
                stream.close()
                print(f"  ✅ 可以打开")
            except Exception as e:
                print(f"  ❌ 无法打开: {e}")
        print()
    except Exception as e:
        print(f"设备 {i}: 获取信息失败 - {e}")
        print()

audio.terminate()

print("-" * 60)
print("建议使用的设备: 选择 maxInputChannels > 0 且可以打开的设备")