"""Java 运行时管理：自动检索 + 自动下载（Adoptium Temurin）

流程：
1. 先查 JavaDetector 已安装的运行时（满足 major 即用）
2. 查 <root>/java 下已下载的运行时
3. 都没有 → 调用 Adoptium API 解析下载地址 → 下载 zip → 解压 → 记录 java_paths.json
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from vein_launcher.common.utils.path_utils import ensure_dir, get_config_dir, get_downloads_dir, get_root_dir
from vein_launcher.infrastructure.download.downloader import Downloader
from vein_launcher.infrastructure.network.http_client import HttpClient
from vein_launcher.infrastructure.process.java_detector import JavaDetector, JavaRuntime

logger = logging.getLogger(__name__)

ADOPTIUM_ASSETS = (
    "https://api.adoptium.net/v3/assets/latest/{major}/hotspot"
    "?architecture=x64&image_type=jdk&os=windows"
)

Progress = Callable[[str, int, int], None]


class JavaManager:
    def __init__(self, detector: Optional[JavaDetector] = None,
                 http: Optional[HttpClient] = None):
        self._detector = detector or JavaDetector()
        self._http = http or HttpClient()
        self._java_root = ensure_dir(get_root_dir() / "java")
        self._paths_file = get_config_dir() / "java_paths.json"

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    def _installed_map(self) -> Dict[str, str]:
        try:
            data = json.loads(self._paths_file.read_text(encoding="utf-8"))
            return {str(k): str(v) for k, v in data.items() if Path(str(v)).is_file()}
        except (OSError, json.JSONDecodeError):
            return {}

    def _remember(self, major: int, path: Path) -> None:
        data = self._installed_map()
        data[str(major)] = str(path)
        try:
            self._paths_file.parent.mkdir(parents=True, exist_ok=True)
            self._paths_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            logger.warning("java_paths.json 写入失败")

    def _downloaded_for(self, major: int) -> Optional[Path]:
        known = self._installed_map().get(str(major))
        if known and Path(known).is_file():
            return Path(known)
        for candidate in self._java_root.glob(f"*/bin/java.exe"):
            if f"-{major}" in candidate.parent.parent.name or str(major) in candidate.parent.parent.name:
                return candidate
        return None

    # ------------------------------------------------------------------
    async def resolve_download(self, major: int) -> Dict[str, Any]:
        """解析 Adoptium 下载信息（不下载）"""
        data = await self._http.get_json(ADOPTIUM_ASSETS.format(major=major))
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"没有适用于 Java {major} 的 Windows x64 包")
        binary = (data[0].get("binary") or {})
        package = binary.get("package") or {}
        link = package.get("link")
        if not link:
            raise RuntimeError("Adoptium 返回缺少下载链接")
        return {
            "major": major,
            "url": link,
            "name": package.get("name", f"temurin-{major}.zip"),
            "size": package.get("size", 0),
            "version": (data[0].get("version") or {}).get("semver", ""),
        }

    async def ensure(self, major: int, progress: Optional[Progress] = None,
                     download: bool = True) -> Dict[str, Any]:
        """确保存在满足 major 的 Java；返回 {major, path, downloaded, source}"""
        major = int(major)

        runtimes = await self._detector.detect()
        match = next((rt for rt in runtimes if rt.major == major), None)
        if match is not None:
            return {"major": major, "path": str(match.path), "downloaded": False, "source": "system"}

        local = self._downloaded_for(major)
        if local is not None:
            return {"major": major, "path": str(local), "downloaded": False, "source": "local"}

        if not download:
            info = await self.resolve_download(major)
            return {"major": major, "path": None, "downloaded": False, "source": "remote",
                    "remote": info}

        info = await self.resolve_download(major)
        if progress:
            progress("准备", 0, int(info.get("size") or 0))

        archive_dir = ensure_dir(get_downloads_dir() / "java")
        archive = archive_dir / info["name"]
        async with Downloader() as downloader:
            await downloader.download(info["url"], archive)

        target = ensure_dir(self._java_root / f"temurin-{major}")
        await self._extract(archive, target)

        exe = next(target.glob("*/bin/java.exe"), None) or next(target.glob("bin/java.exe"), None)
        if exe is None:
            raise RuntimeError("解压后未找到 java.exe")

        self._remember(major, exe)
        if progress:
            progress("完成", 1, 1)
        logger.info("Java %s 安装完成：%s", major, exe)
        return {"major": major, "path": str(exe), "downloaded": True, "source": "adoptium"}

    # ------------------------------------------------------------------
    @staticmethod
    async def _extract(archive: Path, target: Path) -> None:
        import asyncio

        def _run() -> None:
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(target)

        await asyncio.to_thread(_run)


__all__ = ["JavaManager"]
