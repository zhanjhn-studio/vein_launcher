"""资源路径（源码运行 / PyInstaller 打包均可用）"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def assets_dir() -> Optional[Path]:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "assets")
    here = Path(__file__).resolve()
    for parents in (2, 3, 4):
        try:
            candidates.append(here.parents[parents] / "assets")
        except IndexError:
            continue
    for path in candidates:
        if path.is_dir():
            return path
    return None


def asset(name: str) -> Optional[Path]:
    base = assets_dir()
    if base is None:
        return None
    target = base / name
    return target if target.is_file() else None


__all__ = ["assets_dir", "asset"]
