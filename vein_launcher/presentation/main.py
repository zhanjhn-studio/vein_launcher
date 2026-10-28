"""Vein Launcher 入口

用法：
    python -m vein_launcher
    python -m vein_launcher.presentation.main
"""

from __future__ import annotations

import asyncio
import logging
import sys

from PySide6.QtWidgets import QApplication

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.logging.logger import setup_logger
from vein_launcher.presentation.bridge import AsyncBridge
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)


def main() -> int:
    setup_logger()
    logger.info("Vein Launcher 启动中…")

    app = QApplication(sys.argv)
    app.setApplicationName("Vein Launcher")
    app.setOrganisationName("Vein Studio")

    bridge = AsyncBridge()

    # 服务装配需要 async（会创建 aiohttp 相关对象），放到后台循环完成后回到 UI
    holder: dict = {}
    ready = {"done": False}

    def on_ready(context, error) -> None:
        if error:
            logger.exception("应用初始化失败", exc_info=error)
            app.quit()
            return
        holder["context"] = context
        ready["done"] = True

        from vein_launcher.presentation.ui.main_window import MainWindow

        window = MainWindow(context, bridge)
        window.show()
        holder["window"] = window

        event_bus.publish(EventNames.APP_STARTUP)

    bridge.submit(AppContext.create(), on_ready)

    # 等待初始化完成（最多 15 秒），期间持续处理 Qt 事件
    import time

    deadline = time.monotonic() + 15
    while not ready["done"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.02)

    if not ready["done"]:
        logger.error("应用初始化超时")
        return 1

    code = app.exec()
    event_bus.publish(EventNames.APP_SHUTDOWN)
    logger.info("Vein Launcher 退出，code=%s", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
