"""基础设施层 - SHA-1 校验工具"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Optional


def sha1_file(path: Path) -> Optional[str]:
    """同步计算文件 SHA-1；文件不存在返回 None"""
    path = Path(path)
    if not path.is_file():
        return None
    hasher = hashlib.sha1()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


async def sha1_file_async(path: Path) -> Optional[str]:
    return await asyncio.to_thread(sha1_file, Path(path))


async def verify_file(path: Path, expected_sha1: str) -> bool:
    """校验文件 SHA-1 是否匹配"""
    actual = await sha1_file_async(path)
    return bool(actual) and actual.lower() == expected_sha1.lower()


__all__ = ["sha1_file", "sha1_file_async", "verify_file"]
