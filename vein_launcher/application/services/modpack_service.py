"""应用层 - 整合包（.mrpack）解析与安装

MRPack 结构（Modrinth 规范）：
    modrinth.index.json
      ├── formatVersion / game / versionId / name
      ├── dependencies: {"minecraft": "1.20.4", "fabric-loader": "0.15.7"}
      └── files: [{path, hashes{sha1,sha512}, downloads[], env{client,server}, fileSize}]
    overrides/          客户端与通用覆盖文件
    client-overrides/   仅客户端覆盖
    server-overrides/   仅服务端（忽略）

安装：先写入 overrides，再按 files[].path 下载到实例根目录。
"""

from __future__ import annotations

import json
import logging
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import DownloadError
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir
from vein_launcher.infrastructure.download.downloader import AsyncDownloader, DownloadTask

logger = logging.getLogger(__name__)

INDEX_NAME = "modrinth.index.json"
SUPPORTED_FORMATS = (1,)


@dataclass
class ModpackInfo:
    """整合包元信息"""

    name: str
    version_id: str
    dependencies: Dict[str, str] = field(default_factory=dict)
    files: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def minecraft_version(self) -> Optional[str]:
        return self.dependencies.get("minecraft")

    @property
    def loader(self) -> Optional[str]:
        for key in ("fabric-loader", "forge", "quilt-loader", "neoforge"):
            if key in self.dependencies:
                return key
        return None

    @property
    def client_files(self) -> List[Dict[str, Any]]:
        """排除 server-only 与 unsupported"""
        result = []
        for item in self.files:
            env = item.get("env") or {}
            if env.get("client") in ("unsupported", "server"):
                continue
            if env.get("server") == "required" and env.get("client") is None:
                continue
            result.append(item)
        return result


class ModpackService:
    """读取 .mrpack 并安装到指定实例"""

    def __init__(self, downloader: Optional[AsyncDownloader] = None):
        self._downloader = downloader

    # ------------------------------------------------------------------
    @staticmethod
    def read_index(archive: Path) -> ModpackInfo:
        """解析 modrinth.index.json（不落盘覆盖文件）"""
        archive = Path(archive)
        if not archive.is_file():
            raise DownloadError(f"整合包文件不存在：{archive}")

        try:
            with zipfile.ZipFile(archive) as zf:
                if INDEX_NAME not in zf.namelist():
                    raise DownloadError("不是有效的 Modrinth 整合包：缺少 modrinth.index.json")
                raw = json.loads(zf.read(INDEX_NAME).decode("utf-8"))
        except zipfile.BadZipFile as exc:
            raise DownloadError(f"整合包损坏：{exc}") from exc

        fmt = int(raw.get("formatVersion", 0))
        if fmt not in SUPPORTED_FORMATS:
            raise DownloadError(f"不支持的整合包格式版本：{fmt}")

        return ModpackInfo(
            name=raw.get("name", archive.stem),
            version_id=str(raw.get("versionId", "1.0.0")),
            dependencies=dict(raw.get("dependencies") or {}),
            files=list(raw.get("files") or []),
        )

    # ------------------------------------------------------------------
    async def install(
        self,
        archive: Path,
        instance_id: str,
        progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """安装整合包：覆盖文件 → 下载清单文件 → 返回统计"""
        archive = Path(archive)
        info = self.read_index(archive)
        instance_dir = ensure_dir(get_version_dir(instance_id))

        event_bus.publish(EventNames.MODS_UPDATED, version_id=instance_id, source="modpack")

        # 1) 覆盖文件
        extracted = await self._extract_overrides(archive, instance_dir)
        logger.info("整合包 %s：覆盖文件 %d 个", info.name, extracted)

        # 2) 下载清单
        files = info.client_files
        tasks: List[DownloadTask] = []
        for item in files:
            path = item.get("path") or ""
            downloads = item.get("downloads") or []
            if not path or not downloads:
                continue
            # 防路径穿越
            target = (instance_dir / path).resolve()
            if instance_dir.resolve() not in target.parents:
                logger.warning("整合包路径越界，已跳过：%s", path)
                continue
            tasks.append(
                DownloadTask(
                    url=downloads[0],
                    dest=target,
                    expected_sha1=(item.get("hashes") or {}).get("sha1"),
                    size=item.get("fileSize"),
                    mirrors=tuple(downloads[1:]),
                )
            )

        report: Dict[str, Any] = {
            "files": len(tasks),
            "ok": 0,
            "failed": 0,
            "errors": [],
        }
        downloader = self._downloader or AsyncDownloader()
        owns = self._downloader is None
        try:
            if tasks:
                outcomes = await downloader.download_many(tasks)
                for task, outcome in zip(tasks, outcomes):
                    if isinstance(outcome, BaseException):
                        report["failed"] += 1
                        report["errors"].append(f"{task.dest.name}: {outcome}")
                    else:
                        report["ok"] += 1
                    if progress:
                        progress("整合包", report["ok"] + report["failed"], len(tasks))
        finally:
            if owns:
                await downloader.close()

        report.update(
            {
                "name": info.name,
                "minecraft": info.minecraft_version,
                "loader": info.loader,
                "extracted": extracted,
                "instance": str(instance_dir),
            }
        )
        logger.info(
            "整合包安装完成：%s（%d/%d 文件）",
            info.name, report["ok"], report["files"],
        )
        return report

    # ------------------------------------------------------------------
    @staticmethod
    async def _extract_overrides(archive: Path, instance_dir: Path) -> int:
        """解压 overrides/ 与 client-overrides/（忽略 server-overrides）"""

        def _do() -> int:
            count = 0
            with zipfile.ZipFile(archive) as zf:
                for member in zf.namelist():
                    for prefix in ("overrides/", "client-overrides/"):
                        if not member.startswith(prefix) or member.endswith("/"):
                            continue
                        rel = member[len(prefix):]
                        if not rel:
                            continue
                        target = (instance_dir / rel).resolve()
                        try:
                            target.relative_to(instance_dir.resolve())
                        except ValueError:
                            continue  # 路径穿越，跳过
                        ensure_dir(target.parent)
                        with zf.open(member) as src, target.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
                        count += 1
            return count

        import asyncio

        return await asyncio.to_thread(_do)


__all__ = ["ModpackService", "ModpackInfo", "INDEX_NAME"]
