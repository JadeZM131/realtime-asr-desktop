// popup.js - 浏览器插件Popup脚本

let ws = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let reconnectTimer = null;

const statusEl = document.getElementById('status');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const outputEl = document.getElementById('output');
const serverUrlInput = document.getElementById('serverUrl');

const results = [];

// 连接WebSocket
function connect() {
  const serverUrl = serverUrlInput.value;
  statusEl.textContent = '连接中...';
  statusEl.className = 'status connecting';

  ws = new WebSocket(serverUrl);

  ws.onopen = () => {
    statusEl.textContent = '已连接';
    statusEl.className = 'status ready';
    startBtn.disabled = false;
    console.log('WebSocket 已连接');
  };

  ws.onclose = () => {
    statusEl.textContent = '连接断开';
    statusEl.className = 'status stopped';
    startBtn.disabled = false;
    stopBtn.disabled = true;
    console.log('WebSocket 已断开');

    // 自动重连
    if (isRecording) {
      reconnectTimer = setTimeout(connect, 3000);
    }
  };

  ws.onerror = (e) => {
    console.error('WebSocket 错误:', e);
    statusEl.textContent = '连接错误';
    statusEl.className = 'status stopped';
  };

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'result') {
        displayResult(data.data);
      } else if (data.type === 'error') {
        console.error('服务器错误:', data.message);
      }
    } catch (err) {
      console.error('解析错误:', err);
    }
  };
}

// 显示结果
function displayResult(data) {
  const segments = data.segments || [];
  segments.forEach(seg => {
    results.push(seg.text);

    const div = document.createElement('div');
    div.className = 'segment';
    div.innerHTML = `
      <div class="time">${seg.start.toFixed(1)}s - ${seg.end.toFixed(1)}s</div>
      <div class="text">${seg.text}</div>
    `;
    outputEl.appendChild(div);
  });

  // 滚动到底部
  outputEl.scrollTop = outputEl.scrollHeight;
}

// 开始录制
async function startRecording() {
  try {
    // 获取当前标签页的媒体流
    const stream = await chrome.tabCapture.captureMediaStream();

    if (!stream) {
      alert('无法捕获标签页音频。请刷新页面后重试。');
      return;
    }

    audioChunks = [];
    isRecording = true;

    // 创建MediaRecorder
    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) {
      alert('该标签页没有音频');
      return;
    }

    // 使用AudioContext处理音频
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;

      const inputData = e.inputBuffer.getChannelData(0);

      // 转换为16-bit PCM
      const pcmData = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      // 转换为base64
      const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcmData.buffer)));

      ws.send(JSON.stringify({
        type: 'audio',
        data: base64
      }));
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    statusEl.textContent = '录制中...';
    statusEl.className = 'status recording';
    startBtn.disabled = true;
    stopBtn.disabled = false;

    // 保存processor用于停止
    window.processor = processor;
    window.audioContext = audioContext;

  } catch (e) {
    alert('启动失败: ' + e.message);
    console.error(e);
  }
}

// 停止录制
function stopRecording() {
  isRecording = false;

  if (window.processor) {
    window.processor.disconnect();
    window.processor = null;
  }

  if (window.audioContext) {
    window.audioContext.close();
    window.audioContext = null;
  }

  statusEl.textContent = '已停止';
  statusEl.className = 'status stopped';
  startBtn.disabled = false;
  stopBtn.disabled = true;
}

// 事件监听
startBtn.addEventListener('click', () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connect();
  }
  setTimeout(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      startRecording();
    }
  }, 500);
});

stopBtn.addEventListener('click', stopRecording);

document.getElementById('copyBtn').addEventListener('click', () => {
  const text = results.join('\n');
  navigator.clipboard.writeText(text).then(() => {
    alert('已复制到剪贴板');
  });
});

document.getElementById('clearBtn').addEventListener('click', () => {
  results.length = 0;
  outputEl.innerHTML = '';
});

// 页面加载时检查连接状态
if (ws && ws.readyState === WebSocket.OPEN) {
  statusEl.textContent = '已连接';
  statusEl.className = 'status ready';
  startBtn.disabled = false;
}