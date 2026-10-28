"""基础设施层 - Java 运行时探测"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r'version "(\d+)(?:\.(\d+))?[^"]*"')


@dataclass(slots=True)
class JavaRuntime:
    """一个可用的 Java 运行时"""

    path: Path
    major: int
    version: str
    vendor: str


class JavaDetector:
    """从 JAVA_HOME、注册表、PATH、常见目录探测 Java"""

    def __init__(self, extra: Optional[List[Path]] = None):
        self._extra = extra or []

    async def detect(self) -> List[JavaRuntime]:
        candidates: List[Path] = []

        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java.exe")

        candidates.extend(self._registry_candidates())

        on_path = shutil.which("java")
        if on_path:
            candidates.append(Path(on_path))

        candidates.extend(self._common_dirs())
        candidates.extend(self._extra)

        result: List[JavaRuntime] = []
        seen: set[str] = set()
        for exe in candidates:
            key = str(exe).lower()
            if key in seen or not exe.is_file():
                continue
            seen.add(key)
            runtime = await self._probe(exe)
            if runtime:
                result.append(runtime)

        result.sort(key=lambda r: (r.major, r.version), reverse=True)
        return result

    async def select(self, required_major: int, runtimes: Optional[List[JavaRuntime]] = None) -> Optional[JavaRuntime]:
        """选择满足要求的最低版本"""
        pool = runtimes if runtimes is not None else await self.detect()
        usable = [r for r in pool if r.major >= required_major]
        return min(usable, key=lambda r: (r.major, r.version)) if usable else None

    # ------------------------------------------------------------------
    @staticmethod
    def _registry_candidates() -> List[Path]:
        if sys.platform != "win32":
            return []
        try:
            import winreg
        except ImportError:
            return []

        result: List[Path] = []
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JRE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
        ]
        for hive, subkey in roots:
            try:
                with winreg.OpenKey(hive, subkey) as base:
                    index = 0
                    while True:
                        try:
                            name = winreg.EnumKey(base, index)
                        except OSError:
                            break
                        index += 1
                        try:
                            with winreg.OpenKey(base, name) as key:
                                home, _ = winreg.QueryValueEx(key, "JavaHome")
                            result.append(Path(home) / "bin" / "java.exe")
                        except OSError:
                            continue
            except OSError:
                continue
        return result

    @staticmethod
    def _common_dirs() -> List[Path]:
        if sys.platform != "win32":
            return []
        bases = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        ]
        vendors = ("Java", "Eclipse Adoptium", "Programs", "Zulu", "Microsoft")
        found: List[Path] = []
        for base in bases:
            for vendor in vendors:
                vendor_dir = base / vendor
                if not vendor_dir.is_dir():
                    continue
                try:
                    for child in vendor_dir.iterdir():
                        exe = child / "bin" / "java.exe"
                        if exe.is_file():
                            found.append(exe)
                except OSError:
                    continue
        return found

    async def _probe(self, exe: Path) -> Optional[JavaRuntime]:
        try:
            proc = await asyncio.create_subprocess_exec(
                str(exe), "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        except (OSError, asyncio.TimeoutError):
            return None

        text = (out or b"").decode("utf-8", errors="replace")
        match = _VERSION_RE.search(text)
        if not match:
            return None

        major = int(match.group(1))
        full = match.group(0).split('"')[1] if '"' in match.group(0) else str(major)
        lower = text.lower()
        vendor = next(
            (v for hint, v in (
                ("temurin", "Temurin"), ("adoptium", "Adoptium"), ("zulu", "Zulu"),
                ("corretto", "Corretto"), ("microsoft", "Microsoft"), ("openjdk", "OpenJDK"),
            ) if hint in lower),
            "Unknown",
        )
        return JavaRuntime(path=exe, major=major, version=full, vendor=vendor)


__all__ = ["JavaDetector", "JavaRuntime"]
