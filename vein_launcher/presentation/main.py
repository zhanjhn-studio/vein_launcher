"""Vein Launcher 入口：QWebEngineView + React 前端 + QWebChannel 桥"""

from __future__ import annotations

import faulthandler
import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

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


class MainWindow(QMainWindow):
    """主窗口：原生边框 + WebView"""

    def __init__(self, context: AppContext):
        super().__init__()
        started = time.perf_counter()
        self._ctx = context

        self.setWindowTitle(f"Vein Launcher {VERSION}")
        self.resize(1280, 820)
        self.setMinimumSize(1080, 680)

        self.view = QWebEngineView(self)
        page = LoggingPage(self.view)
        self.view.setPage(page)
        self.setCentralWidget(self.view)

        self.channel = QWebChannel(page)
        self.bridge = ApiBridge(context, page, self)
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
    return code


if __name__ == "__main__":
    raise SystemExit(main())
