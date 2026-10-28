"""基础设施层 - Java 运行时探测

来源优先级：用户配置 > JAVA_HOME > 注册表 > PATH > 常见安装目录。
"""

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
_VENDOR_HINTS = (
    ("temurin", "Eclipse Temurin"),
    ("adoptium", "Eclipse Adoptium"),
    ("zulu", "Azul Zulu"),
    ("graalvm", "GraalVM"),
    ("corretto", "Amazon Corretto"),
    ("microsoft", "Microsoft OpenJDK"),
    ("jbr", "JetBrains Runtime"),
    ("openjdk", "OpenJDK"),
)


@dataclass(slots=True)
class JavaInstallation:
    """一个可用的 Java 运行时"""

    path: Path
    major: int
    full_version: str
    vendor: str
    arch: str

    @property
    def is_64bit(self) -> bool:
        return self.arch in ("64", "amd64", "x86_64")


class JavaDetector:
    """异步探测本机 Java 环境"""

    def __init__(self, extra_candidates: Optional[List[Path]] = None):
        self._extra = extra_candidates or []

    async def detect_all(self) -> List[JavaInstallation]:
        """探测所有候选并返回去重后的列表（按 major 降序）"""
        candidates: List[Path] = []
        configured = self._configured_path()
        if configured:
            candidates.append(configured)

        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java.exe")

        candidates.extend(self._registry_candidates())
        found = shutil.which("java")
        if found:
            candidates.append(Path(found))
        candidates.extend(self._common_dirs())
        candidates.extend(self._extra)

        installations: List[JavaInstallation] = []
        seen: set[str] = set()
        for exe in candidates:
            key = str(exe).lower()
            if key in seen or not exe.exists():
                continue
            seen.add(key)
            info = await self._probe(exe)
            if info:
                installations.append(info)

        installations.sort(key=lambda j: (j.major, j.full_version), reverse=True)
        logger.info("探测到 %d 个 Java 运行时", len(installations))
        return installations

    def select_best(
        self, required_major: int, installations: Optional[List[JavaInstallation]] = None
    ) -> Optional[JavaInstallation]:
        """挑选满足要求的最低版本（避免无谓地跑 21 启动 1.16）"""
        pool = installations or []
        usable = [j for j in pool if j.major >= required_major]
        if not usable:
            return None
        return min(usable, key=lambda j: (j.major, j.full_version))

    # ------------------------------------------------------------------
    # 候选来源
    # ------------------------------------------------------------------
    @staticmethod
    def _configured_path() -> Optional[Path]:
        try:
            from vein_launcher.common.config.settings import settings_manager

            configured = settings_manager.get().java.path
            if configured:
                path = Path(configured)
                return path if path.is_file() else path / "bin" / "java.exe"
        except Exception:  # 配置损坏不应阻断探测
            logger.debug("读取 Java 配置失败", exc_info=True)
        return None

    @staticmethod
    def _registry_candidates() -> List[Path]:
        """Windows 注册表：JavaSoft / Adoptium"""
        if sys.platform != "win32":
            return []
        try:
            import winreg
        except ImportError:
            return []

        results: List[Path] = []
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JRE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Runtime Environment"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Foundation\JDK"),
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
                            with winreg.OpenKey(base, name) as version_key:
                                home, _ = winreg.QueryValueEx(version_key, "JavaHome")
                                results.append(Path(home) / "bin" / "java.exe")
                        except OSError:
                            continue
            except OSError:
                continue
        return results

    @staticmethod
    def _common_dirs() -> List[Path]:
        """常见安装目录扫描（一层深度）"""
        if sys.platform != "win32":
            return [
                Path("/usr/lib/jvm"),
                Path("/Library/Java/JavaVirtualMachines"),
            ]
        bases = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        ]
        vendors = (
            "Java", "Eclipse Adoptium", "Eclipse Foundation", "Zulu",
            "Microsoft", "Amazon Corretto", "BellSoft", "JetBrains",
        )
        results: List[Path] = []
        for base in bases:
            if not base.is_dir():
                continue
            for vendor in vendors:
                vendor_dir = base / vendor
                if not vendor_dir.is_dir():
                    continue
                try:
                    for child in vendor_dir.iterdir():
                        if not child.is_dir():
                            continue
                        exe = child / "bin" / "java.exe"
                        if exe.is_file():
                            results.append(exe)
                        nested = child / "bin" / "java.exe"
                        if nested.is_file():
                            results.append(nested)
                except OSError:
                    continue
        return results

    # ------------------------------------------------------------------
    # 版本探测
    # ------------------------------------------------------------------
    async def _probe(self, exe: Path) -> Optional[JavaInstallation]:
        """执行 `java -version` 解析版本信息"""
        try:
            proc = await asyncio.create_subprocess_exec(
                str(exe),
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        except (OSError, asyncio.TimeoutError) as exc:
            logger.debug("探测 Java 失败 %s: %s", exe, exc)
            return None

        text = (out or b"").decode("utf-8", errors="replace")
        match = _VERSION_RE.search(text)
        if not match:
            return None

        major = int(match.group(1))
        full = match.group(0).split('"')[1] if '"' in match.group(0) else str(major)
        lower = text.lower()
        vendor = next((label for hint, label in _VENDOR_HINTS if hint in lower), "Unknown")

        is64 = "64-bit" in text or "amd64" in lower
        arch = "64" if is64 else "32"
        return JavaInstallation(path=exe, major=major, full_version=full, vendor=vendor, arch=arch)


__all__ = ["JavaDetector", "JavaInstallation"]
