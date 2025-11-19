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

    def __init__(self, interval: float, count: int, save_dir: Path, parent=None, mode: str = 'interval', duration: float = 0.0, start_ts: float = None, end_ts: float = None, periods: list = None):
        super().__init__(parent)
        self.interval = interval
        self.count = count
        self.save_dir = save_dir
        self._stop = False
        self.mode = mode
        self.duration = duration
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.periods = periods or []
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
            if self.mode == 'interval':
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
            else:
                if self.periods:
                    idx = 0
                    for s_ts, e_ts in self.periods:
                        if self._stop:
                            break
                        if s_ts is not None:
                            while not self._stop:
                                now = time.time()
                                if now >= s_ts:
                                    break
                                time.sleep(min(0.2, max(0.0, s_ts - now)))
                        while not self._stop and time.time() < e_ts:
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
                            idx += 1
                            self.progress.emit(idx)
                            if not self._stop:
                                time.sleep(self.interval)
                else:
                    if self.start_ts is not None:
                        while not self._stop:
                            now = time.time()
                            if now >= self.start_ts:
                                break
                            time.sleep(min(0.2, self.start_ts - now))
                    deadline = self.end_ts if self.end_ts is not None else (time.time() + self.duration)
                    idx = 0
                    while not self._stop and time.time() < deadline:
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
                        idx += 1
                        self.progress.emit(idx)
                        if not self._stop:
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

        self.mode_interval = QtWidgets.QRadioButton("按间隔采集")
        self.mode_duration = QtWidgets.QRadioButton("按时长自动采集")
        self.mode_interval.setChecked(True)
        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.addWidget(self.mode_interval)
        mode_layout.addWidget(self.mode_duration)

        self.duration_input = QtWidgets.QDoubleSpinBox()
        self.duration_input.setRange(0.1, 86400.0)
        self.duration_input.setDecimals(2)
        self.duration_input.setValue(10.0)
        self.duration_input.setSuffix(" 秒")

        self.start_time_enable = QtWidgets.QCheckBox("指定开始时间")
        self.start_time_input = QtWidgets.QDateTimeEdit()
        self.start_time_input.setCalendarPopup(True)
        self.start_time_input.setDateTime(QtCore.QDateTime.currentDateTime())
        self.start_time_input.setEnabled(False)
        self.start_time_enable.toggled.connect(self.start_time_input.setEnabled)
        start_layout = QtWidgets.QHBoxLayout()
        start_layout.addWidget(self.start_time_enable)
        start_layout.addWidget(self.start_time_input)

        self.end_time_enable = QtWidgets.QCheckBox("指定结束时间")
        self.end_time_input = QtWidgets.QDateTimeEdit()
        self.end_time_input.setCalendarPopup(True)
        self.end_time_input.setDateTime(QtCore.QDateTime.currentDateTime())
        self.end_time_input.setEnabled(False)
        self.end_time_enable.toggled.connect(self.end_time_input.setEnabled)
        end_layout = QtWidgets.QHBoxLayout()
        end_layout.addWidget(self.end_time_enable)
        end_layout.addWidget(self.end_time_input)

        self.schedule_group = QtWidgets.QGroupBox("时间段安排(可选)")
        schedule_v = QtWidgets.QVBoxLayout(self.schedule_group)
        self.schedule_table = QtWidgets.QTableWidget(0, 2)
        self.schedule_table.setHorizontalHeaderLabels(["开始时间", "结束时间"]) 
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        add_schedule_btn = QtWidgets.QPushButton("添加时间段")
        del_schedule_btn = QtWidgets.QPushButton("删除选中")
        add_schedule_btn.clicked.connect(self.add_schedule_row)
        del_schedule_btn.clicked.connect(self.remove_selected_rows)
        sch_btns = QtWidgets.QHBoxLayout()
        sch_btns.addWidget(add_schedule_btn)
        sch_btns.addWidget(del_schedule_btn)
        schedule_v.addWidget(self.schedule_table)
        schedule_v.addLayout(sch_btns)

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
        form.addRow("采集模式", mode_layout)
        form.addRow("持续时长(秒)", self.duration_input)
        form.addRow("开始时间", start_layout)
        form.addRow("结束时间", end_layout)
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
        layout.addWidget(self.schedule_group)
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
        if self.mode_interval.isChecked():
            self.log_view.append(f"[INFO] 开始运行：按间隔采集，间隔 {interval} 秒，次数 {count}，保存目录 {save_dir}")
            self.progress_bar.setRange(0, count)
            self.progress_bar.setValue(0)
            self.worker = Worker(interval, count, save_dir, mode='interval')
        else:
            duration = float(self.duration_input.value())
            start_ts = None
            if self.start_time_enable.isChecked():
                start_ts = self.start_time_input.dateTime().toMSecsSinceEpoch() / 1000.0
            end_ts = None
            if self.end_time_enable.isChecked():
                end_ts = self.end_time_input.dateTime().toMSecsSinceEpoch() / 1000.0
            periods = []
            for r in range(self.schedule_table.rowCount()):
                s_widget = self.schedule_table.cellWidget(r, 0)
                e_widget = self.schedule_table.cellWidget(r, 1)
                if s_widget and e_widget:
                    s_ts = s_widget.dateTime().toMSecsSinceEpoch() / 1000.0
                    e_ts = e_widget.dateTime().toMSecsSinceEpoch() / 1000.0
                    if e_ts <= s_ts:
                        self.log_view.append(f"[ERROR] 第{r+1}行结束时间必须晚于开始时间")
                        return
                    periods.append((s_ts, e_ts))
            if periods:
                self.log_view.append(f"[INFO] 开始运行：按时间段采集，间隔 {interval} 秒，保存目录 {save_dir}")
                self.progress_bar.setRange(0, 0)
                self.worker = Worker(interval, count, save_dir, mode='duration', periods=periods)
            else:
                if start_ts is not None and end_ts is not None and end_ts <= start_ts:
                    self.log_view.append("[ERROR] 结束时间必须晚于开始时间")
                    return
                self.log_view.append(f"[INFO] 开始运行：按时长采集，时长 {duration} 秒，间隔 {interval} 秒，保存目录 {save_dir}")
                self.progress_bar.setRange(0, 0)
                self.worker = Worker(interval, count, save_dir, mode='duration', duration=duration, start_ts=start_ts, end_ts=end_ts)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def add_schedule_row(self):
        r = self.schedule_table.rowCount()
        self.schedule_table.insertRow(r)
        s = QtWidgets.QDateTimeEdit()
        s.setCalendarPopup(True)
        s.setDateTime(QtCore.QDateTime.currentDateTime())
        e = QtWidgets.QDateTimeEdit()
        e.setCalendarPopup(True)
        e.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))
        self.schedule_table.setCellWidget(r, 0, s)
        self.schedule_table.setCellWidget(r, 1, e)

    def remove_selected_rows(self):
        sel = self.schedule_table.selectionModel().selectedRows()
        rows = sorted([i.row() for i in sel], reverse=True)
        for r in rows:
            self.schedule_table.removeRow(r)

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
            <p>本程序为“验证码滑块获取器”图形界面（PyQt5），集成后端脚本的验证码获取与滑块验证流程，支持以下采集模式与功能：</p>
            <ul>
              <li>按间隔采集：每隔指定秒数执行一次采集，共执行指定次数。</li>
              <li>按时长采集：从开始时间起，持续指定时长内按间隔执行采集。</li>
              <li>时间段安排：可添加多个“开始时间/结束时间”时间段，程序按时间段依次自动采集。</li>
              <li>固定保存目录：图片保存到指定目录，文件名为毫秒时间戳（如 <code>bg_1763400000000.jpg</code>），避免覆盖。</li>
              <li>实时日志：界面展示请求参数、响应数据、匹配与验证结果，便于观察与定位。</li>
            </ul>
            <h3>架构概览</h3>
            <ul>
              <li>UI层：<code>ui.py</code>（当前文件）负责界面、参数采集、线程调度与日志展示。</li>
              <li>逻辑层：<code>破解验证码.py</code> 提供一次采集函数 <code>fetch_once</code> 与 <code>resolve_login_js</code>。</li>
              <li>参数签名：<code>login.js</code> 使用 <code>crypto-js</code> 生成接口所需签名参数。</li>
              <li>第三方库：<code>requests</code> 发起接口请求；<code>ddddocr</code> 计算滑块匹配位置。</li>
            </ul>
            <h3>使用步骤</h3>
            <ol>
              <li>选择“采集模式”：<b>按间隔采集</b> 或 <b>按时长自动采集</b>。</li>
              <li>设置参数：
                <ul>
                  <li>间隔时间(秒)：支持小数，需大于 0。</li>
                  <li>获取数量：仅在“按间隔采集”模式下使用，总执行次数。</li>
                  <li>持续时长(秒)：仅在“按时长自动采集”模式下使用，总运行秒数。</li>
                  <li>开始/结束时间：勾选启用，指定未来时间点自动开始/结束；结束时间需晚于开始时间。</li>
                  <li>时间段安排(可选)：点击“添加时间段”，为每行设置开始/结束时间，程序按顺序依次执行。</li>
                  <li>保存目录：选择图片保存路径。</li>
                </ul>
              </li>
              <li>点击“开始”：程序在后台线程执行；点击“停止”可随时终止。</li>
            </ol>
            <h3>依赖与安装</h3>
            <ul>
              <li>Python 包：PyQt5、requests、execjs、ddddocr。</li>
              <li>Node 包：crypto-js（用于 <code>login.js</code>）。</li>
              <li>安装示例：
                <pre>pip install PyQt5 requests execjs ddddocr
npm i crypto-js</pre>
              </li>
            </ul>
            <h3>常见问题</h3>
            <ul>
              <li>字体警告（qt.qpa.fonts）为环境提示，可忽略。</li>
              <li>日志过多可能影响界面流畅度，可增大间隔或减少数量。</li>
              <li>如 <code>login.js</code> 报 <code>crypto-js</code> 未安装，请先安装并确保 Node 环境可用。</li>
            </ul>
            <h3>免责声明</h3>
            <p>本程序仅供技术学习与研究，请勿用于违反网站服务条款或法律法规的用途。</p>
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