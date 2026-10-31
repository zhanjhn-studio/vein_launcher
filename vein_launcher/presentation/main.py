"""Vein Launcher 入口：QWebEngineView + React 前端 + QWebChannel 桥"""

from __future__ import annotations

import faulthandler
import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizeGrip,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.logging.logger import (
    install_excepthook,
    install_qt_message_handler,
    log_dir,
    setup_logger,
)
from vein_launcher.presentation.bridge import ApiBridge
from vein_launcher.presentation.context import AppContext, VERSION

logger = logging.getLogger("vein_launcher.presentation.main")

WEBUI_DIR = Path(__file__).parent / "webui" / "dist"

JS_LEVELS = {
    QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: logging.INFO,
    QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: logging.WARNING,
    QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: logging.ERROR,
}


class LoggingPage(QWebEnginePage):
    """把前端 console 与加载事件接进日志系统"""

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):  # noqa: N802
        logger.log(
            JS_LEVELS.get(level, logging.INFO),
            "js %s:%s | %s",
            Path(source_id).name or source_id,
            line_number,
            message,
        )

    def javaScriptAlert(self, security_origin, msg):  # noqa: N802
        logger.info("js alert: %s", msg)

    def certificateError(self, error):  # noqa: N802
        logger.warning("证书错误：%s", error.description())
        return False


class TitleBar(QWidget):
    """自绘标题栏：拖动、最小化、最大化、关闭（替代系统原生边框）"""

    def __init__(self, window):
        super().__init__(window)
        self._window = window
        self._drag_offset = None
        self.setFixedHeight(40)
        self.setObjectName("vlTitleBar")
        self.setStyleSheet(
            """
            #vlTitleBar { background: #1b1f27; border-bottom: 1px solid #2b313d; }
            #vlTitleBar QLabel { color: #a4aec0; font-size: 12px; background: transparent; }
            #vlWinBtn {
                color: #a4aec0; background: transparent; border: 0;
                min-width: 42px; min-height: 28px; font-size: 13px; border-radius: 6px;
            }
            #vlWinBtn:hover { background: #2d3441; color: #e6e9f0; }
            #vlCloseBtn:hover { background: #c0504d; color: #ffffff; }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(4)

        logo = QLabel(self)
        icon_path = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
        if icon_path.is_file():
            logo.setPixmap(QIcon(str(icon_path)).pixmap(20, 20))
        title = QLabel(f"Vein Launcher {VERSION}", self)
        title.setStyleSheet("color:#e6e9f0; font-size:12.5px; font-weight:600;")
        layout.addWidget(logo)
        layout.addSpacing(8)
        layout.addWidget(title)
        layout.addStretch(1)

        for text, name, slot, tip in (
            ("─", "vlWinBtn", self._window.showMinimized, "最小化"),
            ("❐", "vlWinBtn", self._toggle_max, "最大化"),
            ("✕", "vlCloseBtn", self._window.close, "关闭"),
        ):
            button = QToolButton(self)
            button.setText(text)
            button.setObjectName(name)
            button.setToolTip(tip)
            button.clicked.connect(slot)
            layout.addWidget(button)

    def _toggle_max(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self._window.isMaximized():
            self._drag_offset = event.globalPosition().toPoint() - self._window.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self._toggle_max()
        super().mouseDoubleClickEvent(event)


class MainWindow(QMainWindow):
    """主窗口：原生边框 + WebView"""

    def __init__(self, context: AppContext):
        super().__init__()
        started = time.perf_counter()
        self._ctx = context

        self.setWindowTitle(f"Vein Launcher {VERSION}")
        self.resize(1280, 820)
        self.setMinimumSize(1080, 680)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.view = QWebEngineView(self)
        page = LoggingPage(self.view)
        self.view.setPage(page)

        container = QWidget(self)
        container.setObjectName("vlRoot")
        container.setStyleSheet("#vlRoot { background: #15181e; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.titlebar = TitleBar(self)
        layout.addWidget(self.titlebar)
        layout.addWidget(self.view, 1)
        self.setCentralWidget(container)

        self._grip = QSizeGrip(container)
        self._grip.setFixedSize(16, 16)

        self.channel = QWebChannel(page)
        self.bridge = ApiBridge(context, page, self)
        self.bridge._pick_request.connect(self._on_pick_directory)
        self.channel.registerObject("bridge", self.bridge)
        page.setWebChannel(self.channel)

        self.view.loadStarted.connect(lambda: logger.info("页面开始加载"))
        self.view.loadProgress.connect(
            lambda p: logger.debug("加载进度 %s%%", p) if p % 25 == 0 else None
        )
        self.view.loadFinished.connect(self._on_load_finished)
        page.renderProcessTerminated.connect(self._on_renderer_crashed)

        # 主线程心跳：卡顿超过 3 秒立刻写入日志，便于定位「未响应」
        self._last_beat = time.monotonic()
        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(1000)
        self._heartbeat.timeout.connect(self._beat)
        self._heartbeat.start()

        index = WEBUI_DIR / "index.html"
        if not index.is_file():
            logger.error("前端未构建：%s", index)
        logger.info("加载前端：%s", index)
        self.view.load(QUrl.fromLocalFile(str(index)))
        self.bridge.start()
        logger.info("主窗口初始化完成，耗时 %.0f ms", (time.perf_counter() - started) * 1000)

    # ------------------------------------------------------------------
    def _beat(self) -> None:
        now = time.monotonic()
        gap = now - self._last_beat
        if gap > 3.0:
            logger.warning("主线程卡顿 %.1f 秒（可能是同步阻塞或跨线程调用 Qt）", gap)
        self._last_beat = now

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            logger.info("页面加载完成")
        else:
            logger.error("页面加载失败")

    def _on_pick_directory(self, holder: dict) -> None:
        """在 UI 线程弹出目录选择框（供 bridge 的 app.pickDirectory 使用）"""
        from PySide6.QtWidgets import QFileDialog

        start = str(Path.home())
        current = holder.get("default") or start
        chosen = QFileDialog.getExistingDirectory(
            self, holder.get("title", "Select folder"), current
        )
        holder["result"] = chosen or ""
        holder["event"].set()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_grip"):
            self._grip.move(self.width() - 18, self.height() - 18)
            self._grip.raise_()

    def _on_renderer_crashed(self, status, exit_code: int) -> None:
        logger.critical("渲染进程终止：status=%s exit_code=%s", status, exit_code)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        logger.info("窗口关闭，开始释放资源")
        try:
            self.bridge.shutdown(self._ctx)
            self._ctx.launcher.process.kill()
        except Exception:
            logger.exception("关闭清理失败")
        finally:
            super().closeEvent(event)


def _enable_crash_handler(logger_root: logging.Logger):
    """faulthandler 写到独立文件：Chromium 的首次机会 COM 异常(0x8001010d)不再刷屏控制台"""
    try:
        crash_file = log_dir() / "crash.log"
        handle = open(crash_file, "a", encoding="utf-8", buffering=1)
        faulthandler.enable(file=handle, all_threads=True)
        logger_root.debug("faulthandler 输出：%s", crash_file)
        return handle
    except OSError:
        logger_root.exception("crash.log 打开失败，回退到默认 faulthandler")
        faulthandler.enable()
        return None


def _hide_console() -> None:
    """隐藏启动器自身的控制台窗口（打包后配合 --noconsole 更彻底）"""
    if sys.platform != "win32":
        return
    if os.environ.get("VEIN_SHOW_CONSOLE") == "1":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass


def _schedule_auto_exit(app: QApplication) -> None:
    """测试模式自毁：VEIN_AUTO_EXIT=10 → 10 秒后自动退出（默认不开）"""
    raw = os.environ.get("VEIN_AUTO_EXIT")
    if not raw:
        return
    try:
        seconds = float(raw)
    except ValueError:
        return
    if seconds <= 0:
        return
    logger.info("测试模式：%.0f 秒后自动退出", seconds)
    QTimer.singleShot(int(seconds * 1000), app.quit)


def main() -> int:
    _hide_console()
    logger_root = setup_logger()
    _crash_handle = _enable_crash_handler(logger_root)
    install_excepthook(logger_root)
    install_qt_message_handler(logger_root)

    logger.info("Vein Launcher 启动 version=%s pid=%s", VERSION, __import__("os").getpid())
    logger.info("日志目录：%s", log_dir())
    logger.info(
        "环境：python=%s qt=%s platform=%s",
        sys.version.split()[0],
        __import__("PySide6.QtCore", fromlist=["qVersion"]).qVersion(),
        sys.platform,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Vein Launcher")
    app.setOrganizationName("Vein Studio")
    icon = Path(__file__).resolve().parents[2] / "assets" / "logo.ico"
    if not icon.is_file():
        icon = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))

    started = time.perf_counter()
    context = AppContext()
    logger.info("服务装配完成，耗时 %.0f ms", (time.perf_counter() - started) * 1000)

    window = MainWindow(context)
    window.show()
    logger.info("窗口已显示")
    _schedule_auto_exit(app)

    code = app.exec()
    logger.info("退出，code=%s", code)

    if os.environ.get("VEIN_RESET_ON_EXIT") == "1":
        import shutil
        import time as _time

        from vein_launcher.common.utils.path_utils import get_root_dir

        root = get_root_dir()
        logger.info("测试清理：删除数据根目录 %s", root)

        # Windows 下必须先把日志/崩溃文件句柄关掉，否则目录删不干净
        faulthandler.disable()
        if _crash_handle is not None:
            try:
                _crash_handle.close()
            except OSError:
                pass
        for handler in list(logger_root.handlers):
            try:
                handler.close()
            except OSError:
                pass
            logger_root.removeHandler(handler)

        for attempt in range(3):
            shutil.rmtree(root, ignore_errors=True)
            if not root.exists():
                break
            _time.sleep(0.4)
        if root.exists():
            print(f"failed to remove {root}")  # 只在本机调试；正常无控制台
    return code


if __name__ == "__main__":
    raise SystemExit(main())
