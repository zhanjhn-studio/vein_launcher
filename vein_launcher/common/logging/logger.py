"""日志系统 - 控制台 + 滚动文件 + 错误专档 + Qt/异常接管"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)-7s] [%(threadName)s] "
    "%(name)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def log_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    path = Path(base) / "VeinLauncher" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logger(name: str = "vein_launcher", level: Optional[int] = None) -> logging.Logger:
    """配置根 logger（幂等）"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    if level is None:
        level = getattr(logging, os.environ.get("VEIN_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    app_log = log_dir() / f"{datetime.now():%Y-%m-%d}.log"
    file_handler = logging.FileHandler(app_log, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        log_dir() / "error.log", maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    logger.info("===== 日志系统就绪 pid=%s level=%s =====", os.getpid(), logging.getLevelName(level))
    return logger


def install_excepthook(logger: logging.Logger) -> None:
    """未捕获异常写入日志（含线程名与堆栈）"""
    original = sys.excepthook

    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            original(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "未捕获异常 [thread=%s]", threading.current_thread().name,
            exc_info=(exc_type, exc_value, exc_tb),
        )
        original(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def install_qt_message_handler(logger: logging.Logger) -> None:
    """把 Qt 自身的警告/错误接到日志系统"""
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError:  # 非 PySide6 环境（如纯脚本）直接跳过
        return

    mapping = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }
    qt_logger = logging.getLogger("qt")

    def handler(mode, context, message):  # noqa: ANN001 - Qt 回调签名
        level = mapping.get(mode, logging.INFO)
        location = f"{context.file}:{context.line}" if context and context.file else ""
        qt_logger.log(level, "%s %s", message, location)

    qInstallMessageHandler(handler)


__all__ = [
    "setup_logger",
    "install_excepthook",
    "install_qt_message_handler",
    "log_dir",
    "logger",
]

# 兼容旧导入：模块级 logger（handler 由 setup_logger 配置）
logger = logging.getLogger("vein_launcher")
