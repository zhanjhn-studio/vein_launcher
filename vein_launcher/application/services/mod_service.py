"""应用层 - 资源下载服务（Modrinth / CurseForge + 整合包）

支持五类资源：mod / resourcepack / shader / datapack / modpack
支持两个来源：modrinth（默认）/ curseforge（需 API Key）
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import DownloadError
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir
from vein_launcher.infrastructure.download.downloader import (
    AsyncDownloader,
    DownloadTask,
)
from vein_launcher.infrastructure.network.curseforge_api import (
    CLASS_IDS,
    CurseForgeAPI,
)
from vein_launcher.infrastructure.network.modrinth_api import PROJECT_TYPES, ModrinthAPI
from vein_launcher.infrastructure.storage.file_storage import FileStorage
from vein_launcher.application.services.modpack_service import ModpackService

logger = logging.getLogger(__name__)

# 资源类型 -> 实例内目录
TYPE_DIRS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
    "modpack": "modpacks",
}

LOADER_TYPES = {"mod", "modpack"}


class ModService:
    """资源市场与应用内安装"""

    def __init__(
        self,
        api: Optional[ModrinthAPI] = None,
        storage: Optional[FileStorage] = None,
        downloader: Optional[AsyncDownloader] = None,
        curseforge: Optional[CurseForgeAPI] = None,
        modpack: Optional[ModpackService] = None,
    ):
        self._api = api or ModrinthAPI()
        self._storage = storage or FileStorage()
        self._downloader = downloader
        self._cf = curseforge or CurseForgeAPI()
        self._modpack = modpack or ModpackService(downloader)

    async def close(self) -> None:
        await self._api.close()
        await self._cf.close()

    # ------------------------------------------------------------------
    @staticmethod
    def _cf_key() -> str:
        return (settings_manager.get().download.curseforge_api_key or "").strip()

    def curseforge_ready(self) -> bool:
        """是否已配置 CurseForge API Key"""
        return bool(self._cf_key())

    def sources(self) -> List[Dict[str, Any]]:
        """供 UI 展示的可用来源"""
        return [
            {"id": "modrinth", "name": "Modrinth", "available": True},
            {"id": "curseforge", "name": "CurseForge", "available": self.curseforge_ready()},
        ]

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    async def search(
        self,
        query: str,
        project_type: str = "mod",
        mc_version: Optional[str] = None,
        loader: Optional[str] = "fabric",
        limit: int = 20,
        source: str = "modrinth",
    ) -> List[Dict[str, Any]]:
        if source == "curseforge":
            return await self._search_cf(query, project_type, mc_version, loader, limit)

        tags = [loader] if (loader and project_type in LOADER_TYPES) else None
        hits = await self._api.search_mods(
            query,
            limit=limit,
            tags=tags,
            game_versions=[mc_version] if mc_version else None,
            project_type=project_type,
        )
        return [ModrinthAPI.to_mod_summary(hit) for hit in hits]

    async def _search_cf(
        self,
        query: str,
        project_type: str,
        mc_version: Optional[str],
        loader: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        if not CurseForgeAPI.project_type_supported(project_type):
            raise DownloadError(f"CurseForge 不支持该类型：{project_type}")
        items = await self._cf.search_projects(
            query,
            api_key=self._cf_key(),
            limit=limit,
            game_version=mc_version,
            project_type=project_type,
            loader=loader if project_type in LOADER_TYPES else None,
        )
        return [CurseForgeAPI.to_mod_summary(item, project_type) for item in items]

    # ------------------------------------------------------------------
    # 版本列表
    # ------------------------------------------------------------------
    async def versions(
        self,
        slug: str,
        project_type: str = "mod",
        mc_version: Optional[str] = None,
        loader: Optional[str] = "fabric",
        source: str = "modrinth",
    ) -> List[Dict[str, Any]]:
        if source == "curseforge":
            files = await self._cf.get_files(
                int(slug),
                api_key=self._cf_key(),
                game_version=mc_version,
                loader=loader if project_type in LOADER_TYPES else None,
            )
            mapped = [CurseForgeAPI.to_mod_file(f) for f in files]
            return [m for m in mapped if m.get("url")]

        loaders = [loader] if (loader and project_type in LOADER_TYPES) else None
        raw = await self._api.get_mod_versions(
            slug, game_version=mc_version, loaders=loaders
        )
        files = [ModrinthAPI.to_mod_file(v) for v in raw]
        return [f for f in files if f]

    # ------------------------------------------------------------------
    # 安装
    # ------------------------------------------------------------------
    def target_dir(self, instance_id: str, project_type: str) -> Path:
        sub = TYPE_DIRS.get(project_type)
        if not sub:
            raise DownloadError(f"不支持的资源类型：{project_type}")
        return get_version_dir(instance_id) / sub

    async def install(
        self,
        slug: str,
        instance_id: str,
        project_type: str = "mod",
        mc_version: Optional[str] = None,
        loader: str = "fabric",
        with_dependencies: bool = True,
        source: str = "modrinth",
    ) -> Dict[str, Any]:
        if project_type not in PROJECT_TYPES:
            raise DownloadError(f"不支持的资源类型：{project_type}")

        files = await self.versions(slug, project_type, mc_version, loader, source)
        if not files:
            raise DownloadError(
                f"未找到 {slug} 适配 {mc_version or '任意版本'}/{loader} 的文件"
            )

        primary = files[0]
        targets: List[Dict[str, Any]] = [primary]

        if with_dependencies and project_type == "mod":
            targets.extend(await self._resolve_required(primary, mc_version, loader, source, slug))

        dest_dir = ensure_dir(self.target_dir(instance_id, project_type))
        tasks = [
            DownloadTask(
                url=item["url"],
                dest=dest_dir / item["name"],
                expected_sha1=item.get("sha1") or None,
                size=item.get("size") or None,
            )
            for item in targets
        ]

        downloader = self._downloader or AsyncDownloader()
        owns = self._downloader is None
        try:
            outcomes = await downloader.download_many(tasks)
        finally:
            if owns:
                await downloader.close()

        results: List[Dict[str, Any]] = []
        for item, outcome in zip(targets, outcomes):
            if isinstance(outcome, BaseException):
                results.append({"name": item["name"], "ok": False, "error": str(outcome)})
            else:
                results.append(
                    {"name": item["name"], "ok": True, "skipped": outcome.skipped}
                )

        event_bus.publish(
            EventNames.MODS_UPDATED, version_id=instance_id, project_type=project_type
        )
        return {
            "primary": primary.get("name"),
            "type": PROJECT_TYPES[project_type],
            "source": source,
            "dir": str(dest_dir),
            "files": results,
        }

    async def _resolve_required(
        self, primary: Dict[str, Any], mc_version: Optional[str], loader: str,
        source: str, slug: str,
    ) -> List[Dict[str, Any]]:
        """解析 required 依赖并返回对应文件（最多 10 个）"""
        required = [
            dep for dep in primary.get("dependencies", [])
            if dep.get("dependency_type") == "required"
        ]
        resolved: List[Dict[str, Any]] = []
        for dep in required[:10]:
            dep_id = dep.get("project_id")
            if not dep_id:
                continue
            try:
                dep_files = await self.versions(str(dep_id), "mod", mc_version, loader, source)
            except Exception as exc:
                logger.warning("依赖解析失败 %s: %s", dep_id, exc)
                continue
            if dep_files:
                resolved.append(dep_files[0])
        return resolved

    # ------------------------------------------------------------------
    # 整合包
    # ------------------------------------------------------------------
    async def install_modpack(
        self,
        archive: Path,
        instance_id: str,
        progress=None,
    ) -> Dict[str, Any]:
        """安装 .mrpack 到指定实例"""
        return await self._modpack.install(archive, instance_id, progress)

    # ------------------------------------------------------------------
    # 本地已安装资源
    # ------------------------------------------------------------------
    async def list_installed(
        self, instance_id: str, project_type: str = "mod"
    ) -> List[Dict[str, Any]]:
        directory = self.target_dir(instance_id, project_type)
        if not directory.is_dir():
            return []
        items = []
        for file in sorted(directory.iterdir()):
            if not file.is_file():
                continue
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

    async def toggle(self, instance_id: str, file_name: str, enable: bool) -> bool:
        if enable:
            return await self._storage.enable_mod(instance_id, file_name)
        return await self._storage.disable_mod(instance_id, file_name)


__all__ = ["ModService", "TYPE_DIRS", "CLASS_IDS"]
