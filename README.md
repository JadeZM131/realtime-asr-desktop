# Realtime ASR Desktop
实时语音转文字桌面应用，支持说话人分离和翻译功能。

## 功能特性

- 🎙️ 实时语音转文字（VibeVoice-ASR）
- 👥 说话人分离
- ⏱️ 时间戳支持
- 🌐 多语言支持（50+）
- 🔄 可选翻译功能（支持多种 API）
- 🖥️ 桌面应用（Windows）

## 系统架构

```
┌──────────────┐     WebSocket      ┌──────────────┐
│  本地桌面    │ ─────────────────▶ │  远端服务器   │
│  (音频捕获)  │ ◀───────────────── │  (GPU推理)   │
└──────────────┘                    └──────────────┘
```

## 环境要求

### 服务器端
- NVIDIA GPU (8GB+ VRAM，推荐 16GB+)
- Python 3.10+
- CUDA 11.8+

### 客户端
- Windows 10/11
- VB-Cable 虚拟声卡

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/JadeZM131/realtime-asr-desktop.git
cd realtime-asr-desktop
```

### 2. 服务器端部署

```bash
# 进入服务器目录
cd server

# 安装依赖
pip install -r requirements.txt

# 下载 VibeVoice-ASR 模型
python -c "from huggingface_hub import snapshot_download; snapshot_download('microsoft/VibeVoice-ASR')"

# 配置（编辑 config.yaml）
# 设置服务器地址和端口

# 启动服务
python server.py
```

### 3. 客户端配置

```bash
# 进入客户端目录
cd client

# 安装依赖
pip install -r requirements.txt

# 安装 VB-Cable 虚拟声卡
# 下载地址: https://vb-audio.com/Cable/
```

### 4. 运行

1. 设置系统声音输出为 VB-Cable
2. 启动服务器端
3. 运行客户端 `python main.py`

## 配置文件

### 服务器端 (server/config.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 8000

asr:
  model: "microsoft/VibeVoice-ASR"
  device: "cuda"

translator:
  enabled: false
  provider: "deepl"  # google, deepl, openai
  api_key: ""       # 填入你的 API Key
  default_target_lang: "zh"
```

### 客户端 (client/config.yaml)

```yaml
server:
  host: "localhost"  # 服务器地址
  port: 8000

audio:
  sample_rate: 16000
  chunk_size: 4096

ui:
  language: "zh-CN"
```

## 翻译功能

支持多种翻译 API，配置方式：

```yaml
translator:
  enabled: true
  provider: "deepl"
  api_key: "your-api-key"
```

支持的提供商：
- `deepl` - DeepL（免费额度：50万字符/月）
- `google` - Google Translate
- `openai` - OpenAI GPT

## 项目结构

```
realtime-asr-desktop/
├── server/
│   ├── server.py          # WebSocket 服务端
│   ├── asr_engine.py      # VibeVoice-ASR 推理
│   ├── config.yaml        # 服务器配置
│   ├── requirements.txt   # 依赖
│   └── translator/        # 翻译模块
│       ├── __init__.py
│       ├── base.py
│       ├── deepl.py
│       ├── google.py
│       └── openai.py
├── client/
│   ├── main.py            # 客户端入口
│   ├── audio_capture.py   # 音频捕获
│   ├── ws_client.py       # WebSocket 客户端
│   ├── config.yaml        # 客户端配置
│   └── requirements.txt   # 依赖
└── README.md
```

## 技术栈

- **ASR**: VibeVoice-ASR (Microsoft)
- **音频捕获**: NAudio
- **桌面UI**: PyQt6
- **WebSocket**: FastAPI + Uvicorn
- **翻译**: DeepL / Google / OpenAI API

## 许可证

MIT License

## 注意事项

1. 模型需要自行下载（通过 HuggingFace）
2. 翻译 API 需要自行申请
3. 请遵守各 API 服务商的使用条款
4. 虚拟声卡 VB-Cable 需要单独安装
