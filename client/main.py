"""
桌面应用主界面 (PyQt6)
"""
import sys
import os
import yaml
import threading
import queue
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox, QGroupBox,
    QScrollArea, QFrame, QStatusBar, QMenuBar, QMenu,
    QMessageBox, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QColor

from audio_capture import AudioCapture, get_audio_devices
from ws_client import WSClient


class TranscriptionWorker(QThread):
    """转写工作线程"""
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, audio_capture: AudioCapture, ws_client: WSClient):
        super().__init__()
        self.audio_capture = audio_capture
        self.ws_client = ws_client
        self.is_running = False

    def run(self):
        self.is_running = True
        audio_buffer = b""

        while self.is_running:
            # 获取音频数据
            chunk = self.audio_capture.get_audio_chunk(timeout=0.5)
            if chunk:
                audio_buffer += chunk

                # 缓冲约 2 秒后发送（32KB/s @ 16kHz, 16-bit）
                if len(audio_buffer) >= 64000:
                    if self.ws_client.is_connected:
                        self.ws_client.send_audio(audio_buffer)
                    audio_buffer = b""

    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.audio_capture = None
        self.ws_client = None
        self.worker = None

        self.is_recording = False
        self.transcription_history = []

        self.init_ui()

    def _load_config(self) -> dict:
        """加载配置"""
        config_path = "config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # 默认配置
        return {
            "server": {"host": "localhost", "port": 8000},
            "audio": {"sample_rate": 16000, "chunk_size": 4096}
        }

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("实时语音转文字 (Realtime ASR)")
        self.setGeometry(100, 100, 800, 600)

        # 创建菜单
        self._create_menu()

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 控制面板
        control_group = self._create_control_panel()
        layout.addWidget(control_group)

        # 显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.text_display)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _create_menu(self):
        """创建菜单"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        export_action = QAction("导出文字", self)
        export_action.triggered.connect(self.export_text)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置")

        server_action = QAction("服务器设置", self)
        server_action.triggered.connect(self.show_server_settings)
        settings_menu.addAction(server_action)

        audio_action = QAction("音频设备", self)
        audio_action.triggered.connect(self.show_audio_devices)
        settings_menu.addAction(audio_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_control_panel(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox("控制")
        layout = QHBoxLayout()

        # 录音按钮
        self.record_btn = QPushButton("● 开始录音")
        self.record_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)

        # 连接按钮
        self.connect_btn = QPushButton("连接服务器")
        self.connect_btn.clicked.connect(self.connect_server)
        layout.addWidget(self.connect_btn)

        # 模型显示
        layout.addWidget(QLabel("模型: VibeVoice-ASR"))

        # 语言选择
        layout.addWidget(QLabel("翻译目标:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["中文", "英文", "日文", "韩文", "法文", "德文"])
        self.lang_combo.setCurrentText("中文")
        layout.addWidget(self.lang_combo)

        group.setLayout(layout)
        return group

    def connect_server(self):
        """连接服务器"""
        server_config = self.config.get("server", {})
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8000)

        self.ws_client = WSClient(host, port)

        if self.ws_client.start(callback=self.on_result, error_callback=self.on_error):
            self.status_bar.showMessage(f"已连接服务器: {host}:{port}")
            QMessageBox.information(self, "连接", f"已连接到服务器 {host}:{port}")
        else:
            QMessageBox.warning(self, "连接失败", "无法连接到服务器，请检查服务器是否启动")

    def toggle_recording(self):
        """切换录音状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录音"""
        if not self.ws_client or not self.ws_client.is_connected:
            QMessageBox.warning(self, "未连接", "请先连接服务器")
            return

        # 初始化音频捕获
        audio_config = self.config.get("audio", {})
        self.audio_capture = AudioCapture(
            sample_rate=audio_config.get("sample_rate", 16000),
            chunk_size=audio_config.get("chunk_size", 4096)
        )

        try:
            self.audio_capture.start()
            self.worker = TranscriptionWorker(self.audio_capture, self.ws_client)
            self.worker.start()

            self.is_recording = True
            self.record_btn.setText("■ 停止录音")
            self.record_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
            self.status_bar.showMessage("录音中...")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动音频捕获失败: {e}")

    def stop_recording(self):
        """停止录音"""
        if self.worker:
            self.worker.stop()
            self.worker = None

        if self.audio_capture:
            self.audio_capture.stop()
            self.audio_capture.close()
            self.audio_capture = None

        self.is_recording = False
        self.record_btn.setText("● 开始录音")
        self.record_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.status_bar.showMessage("已停止")

    def on_result(self, result: dict):
        """处理转写结果"""
        if result.get("type") == "translation":
            # 翻译结果
            original = result.get("original", "")
            translated = result.get("translated", "")
            self.append_text(f"[翻译] {original} → {translated}\n")
        else:
            # 转写结果
            segments = result.get("segments", [])
            for seg in segments:
                speaker = seg.get("speaker", "未知")
                text = seg.get("text", "")
                start = seg.get("start", 0)

                if text:
                    self.transcription_history.append({
                        "speaker": speaker,
                        "text": text,
                        "timestamp": datetime.now()
                    })
                    self.append_text(f"[{speaker}] {text}\n")

    def on_error(self, error: str):
        """处理错误"""
        self.status_bar.showMessage(f"错误: {error}")

    def append_text(self, text: str):
        """追加文本"""
        self.text_display.append(text)
        # 滚动到底部
        self.text_display.verticalScrollBar().setValue(
            self.text_display.verticalScrollBar().maximum()
        )

    def export_text(self):
        """导出文字"""
        if not self.transcription_history:
            QMessageBox.information(self, "提示", "没有可导出的内容")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出文字", "transcription.txt", "Text Files (*.txt)"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in self.transcription_history:
                    f.write(f"[{item['speaker']}] {item['text']}\n")
            QMessageBox.information(self, "导出成功", f"已保存到 {file_path}")

    def show_server_settings(self):
        """显示服务器设置"""
        host, ok = QInputDialog.getText(self, "服务器设置", "服务器地址:", text=self.config.get("server", {}).get("host", "localhost"))
        if ok:
            port, ok2 = QInputDialog.getInt(self, "服务器设置", "端口:", value=self.config.get("server", {}).get("port", 8000))
            if ok2:
                if "server" not in self.config:
                    self.config["server"] = {}
                self.config["server"]["host"] = host
                self.config["server"]["port"] = port
                self._save_config()

    def show_audio_devices(self):
        """显示音频设备"""
        devices = get_audio_devices()
        msg = "可用音频输入设备:\n\n"
        for dev in devices:
            msg += f"[{dev['index']}] {dev['name']}\n"
        QMessageBox.information(self, "音频设备", msg)

    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            self,
            "关于",
            "实时语音转文字桌面应用\n\n"
            "基于 VibeVoice-ASR\n"
            "支持说话人分离和翻译功能"
        )

    def _save_config(self):
        """保存配置"""
        with open("config.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)

    def closeEvent(self, event):
        """关闭事件"""
        if self.is_recording:
            self.stop_recording()
        if self.ws_client:
            self.ws_client.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
