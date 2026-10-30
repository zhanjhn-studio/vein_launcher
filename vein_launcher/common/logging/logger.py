"""日志系统：纯文件输出 + 分类归档（禁止写控制台）

目录：<VeinLauncher>/log/
├── launcher-YYYY-MM-DD.log   启动器主体
├── plugin-YYYY-MM-DD.log     插件宿主与插件
├── mlc-YYYY-MM-DD.log        MLC 控制层
├── download-YYYY-MM-DD.log   下载调度
├── error.log                 所有 ERROR
└── crash.log                 faulthandler 现场
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)-7s] [%(threadName)s] "
    "%(name)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CATEGORY_PREFIXES = {
    "plugin": (
        "vein_launcher.infrastructure.plugin_host",
        "vein_launcher.application.services.plugin_service",
    ),
    "mlc": ("vein_launcher.mlc",),
    "download": ("vein_launcher.infrastructure.download",),
}


class _PrefixFilter(logging.Filter):
    def __init__(self, prefixes: Iterable[str]):
        super().__init__()
        self._prefixes = tuple(prefixes)

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        return record.name.startswith(self._prefixes)


class _ExcludeFilter(logging.Filter):
    def __init__(self, prefixes: Iterable[str]):
        super().__init__()
        self._prefixes = tuple(prefixes)

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        return not record.name.startswith(self._prefixes)


def log_dir() -> Path:
    from vein_launcher.common.utils.path_utils import bootstrap_layout, get_log_dir

    bootstrap_layout()
    return get_log_dir()


def _file_handler(path: Path, level: int, formatter: logging.Formatter,
                  filter_: Optional[logging.Filter] = None) -> logging.Handler:
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    if filter_ is not None:
        handler.addFilter(filter_)
    return handler


def setup_logger(name: str = "vein_launcher", level: Optional[int] = None) -> logging.Logger:
    """配置日志（幂等）：只写文件，不注册任何控制台 handler"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    if level is None:
        level = getattr(logging, os.environ.get("VEIN_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    today = datetime.now().strftime("%Y-%m-%d")
    base = log_dir()

    all_prefixes = [p for group in CATEGORY_PREFIXES.values() for p in group]

    logger.addHandler(
        _file_handler(
            base / f"launcher-{today}.log",
            logging.DEBUG,
            formatter,
            _ExcludeFilter(all_prefixes),
        )
    )
    for category, prefixes in CATEGORY_PREFIXES.items():
        logger.addHandler(
            _file_handler(base / f"{category}-{today}.log", logging.DEBUG, formatter,
                          _PrefixFilter(prefixes))
        )
    logger.addHandler(_file_handler(base / "error.log", logging.ERROR, formatter))

    logger.info("===== 日志就绪 pid=%s level=%s 目录=%s =====",
                os.getpid(), logging.getLevelName(level), base)
    return logger


def install_excepthook(logger: logging.Logger) -> None:
    """未捕获异常写入日志"""
    original = sys.excepthook

    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            original(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "未捕获异常 [thread=%s]", threading.current_thread().name,
            exc_info=(exc_type, exc_value, exc_tb),
        )

    sys.excepthook = hook


def install_qt_message_handler(logger: logging.Logger) -> None:
    """Qt 消息接入日志（同样只写文件）"""
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError:
        return

    mapping = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }
    qt_logger = logging.getLogger("qt")

    def handler(mode, context, message):  # noqa: ANN001
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

# 兼容旧导入
logger = logging.getLogger("vein_launcher")
