"""应用层 - 模组服务（Modrinth 搜索 / 依赖解析 / 安装）"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import DownloadError
from vein_launcher.common.utils.path_utils import get_version_dir
from vein_launcher.infrastructure.download.downloader import AsyncDownloader, DownloadTask
from vein_launcher.infrastructure.network.modrinth_api import ModrinthAPI
from vein_launcher.infrastructure.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)


class ModService:
    """模组市场与应用内安装"""

    def __init__(
        self,
        api: Optional[ModrinthAPI] = None,
        storage: Optional[FileStorage] = None,
        downloader: Optional[AsyncDownloader] = None,
    ):
        self._api = api or ModrinthAPI()
        self._storage = storage or FileStorage()
        self._downloader = downloader

    async def close(self) -> None:
        await self._api.close()

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    async def search(
        self,
        query: str,
        mc_version: Optional[str] = None,
        loader: Optional[str] = "fabric",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        hits = await self._api.search_mods(
            query,
            limit=limit,
            tags=[loader] if loader else None,
            game_versions=[mc_version] if mc_version else None,
        )
        return [ModrinthAPI.to_mod_summary(hit) for hit in hits]

    async def versions(
        self, slug: str, mc_version: Optional[str] = None, loader: Optional[str] = "fabric"
    ) -> List[Dict[str, Any]]:
        raw = await self._api.get_mod_versions(
            slug,
            game_version=mc_version,
            loaders=[loader] if loader else None,
        )
        files = [ModrinthAPI.to_mod_file(v) for v in raw]
        return [f for f in files if f]

    # ------------------------------------------------------------------
    # 安装（含一级前置依赖）
    # ------------------------------------------------------------------
    async def install(
        self,
        slug: str,
        version_id: str,
        mc_version: str,
        loader: str = "fabric",
        with_dependencies: bool = True,
    ) -> Dict[str, Any]:
        """下载模组主文件 + required 依赖到该版本的 mods 目录"""
        files = await self.versions(slug, mc_version=mc_version, loader=loader)
        if not files:
            raise DownloadError(f"未找到 {slug} 适配 {mc_version}/{loader} 的文件")

        primary = files[0]
        targets: List[Dict[str, Any]] = [primary]

        if with_dependencies:
            required = [
                dep for dep in primary.get("dependencies", [])
                if dep.get("dependency_type") == "required"
            ]
            for dep in required[:10]:  # 防止依赖爆炸
                dep_id = dep.get("project_id")
                if not dep_id:
                    continue
                try:
                    dep_versions = await self._api.get_mod_versions(
                        dep_id, game_version=mc_version, loaders=[loader]
                    )
                except Exception as exc:
                    logger.warning("依赖解析失败 %s: %s", dep_id, exc)
                    continue
                if dep_versions:
                    mapped = ModrinthAPI.to_mod_file(dep_versions[0])
                    if mapped:
                        targets.append(mapped)

        mods_dir = get_version_dir(version_id) / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)

        tasks = [
            DownloadTask(
                url=item["url"],
                dest=mods_dir / item["name"],
                expected_sha1=item.get("sha1") or None,
                size=item.get("size") or None,
            )
            for item in targets
        ]

        downloader = self._downloader or AsyncDownloader()
        own = self._downloader is None
        results: List[Dict[str, Any]] = []
        try:
            outcomes = await downloader.download_many(tasks)
        finally:
            if own:
                await downloader.close()

        for item, outcome in zip(targets, outcomes):
            if isinstance(outcome, BaseException):
                results.append({"name": item["name"], "ok": False, "error": str(outcome)})
            else:
                results.append({"name": item["name"], "ok": True, "skipped": outcome.skipped})

        event_bus.publish(EventNames.MODS_UPDATED, version_id=version_id)
        return {"primary": primary.get("name"), "files": results}

    # ------------------------------------------------------------------
    # 本地模组列表
    # ------------------------------------------------------------------
    async def list_installed(self, version_id: str) -> List[Dict[str, Any]]:
        mods_dir = get_version_dir(version_id) / "mods"
        if not mods_dir.is_dir():
            return []
        items = []
        for file in sorted(mods_dir.glob("*.jar")):
            stat = file.stat()
            items.append(
                {
                    "name": file.name,
                    "size": stat.st_size,
                    "enabled": not file.name.endswith(".disabled.jar"),
                    "path": str(file),
                }
            )
        return items

    async def toggle(self, version_id: str, file_name: str, enable: bool) -> bool:
        if enable:
            return await self._storage.enable_mod(version_id, file_name)
        return await self._storage.disable_mod(version_id, file_name)


__all__ = ["ModService"]
