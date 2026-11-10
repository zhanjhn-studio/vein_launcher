"""Windows 下隐藏子进程控制台窗口（避免 cmd 闪窗）。"""

from __future__ import annotations

import subprocess
import sys

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def hidden_kwargs() -> dict:
    """asyncio.create_subprocess_exec 用：隐藏控制台窗口。"""
    if sys.platform != "win32":
        return {}
    kwargs = {"creationflags": CREATE_NO_WINDOW}
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs


def hidden_popen_kwargs() -> dict:
    """subprocess.Popen 用：隐藏控制台窗口。"""
    return hidden_kwargs()
