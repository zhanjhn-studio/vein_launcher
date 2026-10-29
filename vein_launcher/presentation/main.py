"""Vein Launcher 入口：QWebEngineView + React 前端 + QWebChannel 桥"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from vein_launcher.common.logging.logger import setup_logger
from vein_launcher.presentation.bridge import ApiBridge
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)

WEBUI_DIR = Path(__file__).parent / "webui" / "dist"


class MainWindow(QMainWindow):
    """主窗口：原生边框 + WebView"""

    def __init__(self, context: AppContext):
        super().__init__()
        self._ctx = context
        self.setWindowTitle("Vein Launcher")
        self.resize(1280, 820)
        self.setMinimumSize(1080, 680)

        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        self.channel = QWebChannel(self.view.page())
        self.bridge = ApiBridge(context, self.view.page(), self)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        index = WEBUI_DIR / "index.html"
        if not index.is_file():
            logger.error("前端未构建：%s", index)
        self.view.load(QUrl.fromLocalFile(str(index)))
        self.bridge.start()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        logger.info("窗口关闭")
        try:
            self.bridge.shutdown()
            self._ctx.launcher.process.kill()
        finally:
            super().closeEvent(event)


def main() -> int:
    setup_logger()
    logger.info("Vein Launcher 启动")

    app = QApplication(sys.argv)
    app.setApplicationName("Vein Launcher")

    context = AppContext()
    window = MainWindow(context)
    window.show()

    code = app.exec()
    logger.info("退出，code=%s", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
