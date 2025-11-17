import sys
import os
import time
import io
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QTextCursor
import importlib.util


def load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location("captcha3", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


class QtLogStream(io.TextIOBase):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def write(self, s):
        if s:
            self.signal.emit(s)
        return len(s)

    def flush(self):
        pass


class Worker(QtCore.QThread):
    log = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    done = QtCore.pyqtSignal()

    def __init__(self, interval: float, count: int, save_dir: Path, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.count = count
        self.save_dir = save_dir
        self._stop = False
        base = Path(__file__).resolve().parent
        self.module_path = base / "破解验证码.py"
        self.mod = load_module(self.module_path)
        self.js_code = self.mod.execjs.compile(self.mod.resolve_login_js())
        self.headers = {
            'connection': 'keep-alive',
            'host': 'captcha.chaoxing.com',
            'sec-fetch-dest': 'script',
            'referer': 'https://authserver.whsw.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }

    def stop(self):
        self._stop = True

    def run(self):
        self.save_dir.mkdir(parents=True, exist_ok=True)
        orig_stdout = sys.stdout
        stream = QtLogStream(self.log)
        old_cwd = os.getcwd()
        try:
            for i in range(self.count):
                if self._stop:
                    break
                os.chdir(str(self.save_dir))
                sys.stdout = stream
                try:
                    ts = int(time.time() * 1000)
                    self.mod.fetch_once(self.js_code, self.headers)
                except Exception as e:
                    self.log.emit(f"[ERROR] {e}\n")
                finally:
                    sys.stdout = orig_stdout
                    os.chdir(old_cwd)
                self.progress.emit(i + 1)
                if i + 1 < self.count and not self._stop:
                    time.sleep(self.interval)
        finally:
            sys.stdout = orig_stdout
            os.chdir(old_cwd)
            self.done.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("验证码滑块获取器 (请勿将此程序用于非法用途，只做参考学习)")
        self.worker = None

        self.interval_input = QtWidgets.QDoubleSpinBox()
        self.interval_input.setRange(0.1, 3600.0)
        self.interval_input.setDecimals(2)
        self.interval_input.setValue(2.0)
        self.interval_input.setSuffix(" 秒")

        self.count_input = QtWidgets.QSpinBox()
        self.count_input.setRange(1, 10000)
        self.count_input.setValue(10)

        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setText(str(Path(__file__).resolve().parent))
        browse_btn = QtWidgets.QPushButton("选择目录")
        browse_btn.clicked.connect(self.browse_dir)

        self.start_btn = QtWidgets.QPushButton("开始")
        self.stop_btn = QtWidgets.QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_run)
        self.stop_btn.clicked.connect(self.stop_run)
        info_btn = QtWidgets.QPushButton("使用说明")
        info_btn.clicked.connect(self.show_help)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)

        form = QtWidgets.QFormLayout()
        form.addRow("间隔时间(秒)", self.interval_input)
        form.addRow("获取数量", self.count_input)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        form.addRow("保存目录", path_layout)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(info_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_view)

    def browse_dir(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "选择保存目录", self.path_input.text())
        if d:
            self.path_input.setText(d)

    def start_run(self):
        interval = float(self.interval_input.value())
        count = int(self.count_input.value())
        save_dir = Path(self.path_input.text()).resolve()
        self.log_view.append(f"[INFO] 开始运行：间隔 {interval} 秒，次数 {count}，保存目录 {save_dir}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setRange(0, count)
        self.progress_bar.setValue(0)

        self.worker = Worker(interval, count, save_dir)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def stop_run(self):
        if self.worker:
            self.worker.stop()
            self.log_view.append("[INFO] 停止中...")

    def append_log(self, s: str):
        ts = time.strftime("%H:%M:%S")
        self.log_view.moveCursor(QTextCursor.End)
        self.log_view.insertPlainText(f"[{ts}] {s}")
        self.log_view.moveCursor(QTextCursor.End)

    def on_progress(self, v: int):
        self.progress_bar.setValue(v)

    def on_done(self):
        self.log_view.append("[INFO] 运行结束")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

    def show_help(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("使用说明与程序介绍")
        text = QtWidgets.QTextBrowser(dlg)
        text.setOpenExternalLinks(True)
        text.setHtml(
            """
            <h3>程序介绍</h3>
            <p>本程序基于 PyQt5 提供图形界面，调用 3.0 版脚本的获取流程，支持设置间隔时间、批量获取数量和固定保存目录，并在界面中实时显示日志。</p>
            <h3>使用说明</h3>
            <ol>
              <li>在“间隔时间(秒)”中设置每次获取的时间间隔，支持小数。</li>
              <li>在“获取数量”中输入本次批量获取的次数。</li>
              <li>通过“保存目录”选择图片保存位置，图片将以毫秒时间戳命名，如 <code>bg_1763400000000.jpg</code>。</li>
              <li>点击“开始”后程序将在后台执行，日志会在下方实时显示；可随时点击“停止”。</li>
            </ol>
            <h3>依赖与环境</h3>
            <ul>
              <li>需要已安装 PyQt5、requests、execjs、ddddocr。</li>
              <li>Node 环境与 crypto-js 需可用，以支持 login.js 中加密。</li>
            </ul>
            <h3>提示</h3>
            <ul>
              <li>如日志较多导致界面卡顿，可适当增大间隔或减少获取数量。</li>
              <li>字体相关的控制台警告不影响运行。</li>
              <li>请勿将此程序用于非法用途，只做参考学习</li>
            </ul>
            """
        )
        close_btn = QtWidgets.QPushButton("关闭", dlg)
        close_btn.clicked.connect(dlg.accept)
        lay = QtWidgets.QVBoxLayout(dlg)
        lay.addWidget(text)
        lay.addWidget(close_btn, alignment=QtCore.Qt.AlignRight)
        dlg.resize(640, 520)
        dlg.exec_()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()