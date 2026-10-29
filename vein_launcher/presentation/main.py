"""Vein Launcher 入口：QWebEngineView + React 前端 + QWebChannel 桥"""

from __future__ import annotations

import faulthandler
import logging
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
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
from vein_launcher.presentation.floating import LogoBall

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

    def show_page(self, page: str) -> None:
        if page == "quit":
            self.quit_app()
            return
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.bridge.navigate(page)
        logger.info("悬浮球跳转：%s", page)

    def quit_app(self) -> None:
        logger.info("用户从悬浮球退出")
        self._quitting = True
        self.close()
        QApplication.quit()

    def _on_renderer_crashed(self, status, exit_code: int) -> None:
        logger.critical("渲染进程终止：status=%s exit_code=%s", status, exit_code)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        if not getattr(self, "_quitting", False):
            logger.info("窗口收起（保留悬浮球）")
            event.ignore()
            self.hide()
            return
        logger.info("窗口关闭，开始释放资源")
        try:
            self.bridge.shutdown()
            self._ctx.launcher.process.kill()
        except Exception:
            logger.exception("关闭清理失败")
        finally:
            super().closeEvent(event)


def main() -> int:
    faulthandler.enable()

    logger_root = setup_logger()
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
    app.setQuitOnLastWindowClosed(False)

    started = time.perf_counter()
    context = AppContext()
    logger.info("服务装配完成，耗时 %.0f ms", (time.perf_counter() - started) * 1000)

    window = MainWindow(context)
    window.show()

    ball = LogoBall()
    ball.navigate.connect(window.show_page)
    ball.show()
    window.ball = ball
    logger.info("悬浮球已启用")
    logger.info("窗口已显示")

    code = app.exec()
    logger.info("退出，code=%s", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
