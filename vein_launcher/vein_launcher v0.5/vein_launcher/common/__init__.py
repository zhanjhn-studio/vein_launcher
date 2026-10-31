"""Common 公共层 - 所有层的底层依赖"""

# 事件总线
from .events import event_bus, EventBus, EventNames

# 配置管理
from .config import settings_manager, SettingsManager, Settings

# i18n 国际化
from .i18n import translator, Translator, _

# 日志系统
from .logging import logger, setup_logger

# 异常定义
from .exceptions import (
    VeinError,
    DownloadError,
    SHA1MismatchError,
    VersionNotFoundError,
    JavaNotFoundError,
    GameLaunchError,
    ConfigError
)

__all__ = [
    # Events
    "event_bus",
    "EventBus", 
    "EventNames",
    # Config
    "settings_manager",
    "SettingsManager",
    "Settings",
    # I18n
    "translator",
    "Translator",
    "_",
    # Logging
    "logger",
    "setup_logger",
    # Exceptions
    "VeinError",
    "DownloadError",
    "SHA1MismatchError",
    "VersionNotFoundError",
    "JavaNotFoundError",
    "GameLaunchError",
    "ConfigError"
]
