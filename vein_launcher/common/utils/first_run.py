"""首启日志 —— 第一次进入时写入 first_run.log

记录：时间、版本、系统、Python、主题与语言选择。
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime
from pathlib import Path

from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir
from vein_launcher.common.version import __version__


def write_first_run_log(theme: str, language: str) -> Path:
    """写入首启日志并返回路径"""
    log_dir = ensure_dir(get_app_data_dir() / "logs")
    path = log_dir / "first_run.log"

    lines = [
        "Vein Launcher · first run",
        f"time      : {datetime.now().isoformat(timespec='seconds')}",
        f"version   : {__version__}",
        f"platform  : {platform.platform()}",
        f"machine   : {platform.machine()}",
        f"python    : {sys.version.split()[0]}",
        f"theme     : {theme}",
        f"language  : {language}",
        f"data dir  : {get_app_data_dir()}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


__all__ = ["write_first_run_log"]
