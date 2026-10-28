"""应用层 - 资源下载服务（模组 / 资源包 / 光影 / 数据包 / 整合包）

统一入口：
    search(query, project_type="mod", ...)    搜索
    install(slug, instance_id, project_type)  下载并按类型放入实例目录
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import DownloadError
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir
from vein_launcher.infrastructure.download.downloader import (
    AsyncDownloader,
    DownloadTask,
)
from vein_launcher.infrastructure.network.modrinth_api import PROJECT_TYPES, ModrinthAPI
from vein_launcher.infrastructure.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)

# 资源类型 -> 实例内目录
TYPE_DIRS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
    "modpack": "modpacks",
}

# 需要加载器过滤的类型
LOADER_TYPES = {"mod", "modpack"}


class ModService:
    """资源市场与应用内安装"""

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
        project_type: str = "mod",
        mc_version: Optional[str] = None,
        loader: Optional[str] = "fabric",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """按类型搜索；资源包/光影不传加载器"""
        tags = [loader] if (loader and project_type in LOADER_TYPES) else None
        hits = await self._api.search_mods(
            query,
            limit=limit,
            tags=tags,
            game_versions=[mc_version] if mc_version else None,
            project_type=project_type,
        )
        return [ModrinthAPI.to_mod_summary(hit) for hit in hits]

    async def versions(
        self,
        slug: str,
        project_type: str = "mod",
        mc_version: Optional[str] = None,
        loader: Optional[str] = "fabric",
    ) -> List[Dict[str, Any]]:
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
        """资源在实例中的目标目录"""
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
    ) -> Dict[str, Any]:
        """下载项目主文件（模组自动补 required 依赖）到实例目录"""
        if project_type not in PROJECT_TYPES:
            raise DownloadError(f"不支持的资源类型：{project_type}")

        files = await self.versions(slug, project_type, mc_version or None, loader)
        if not files:
            raise DownloadError(
                f"未找到 {slug} 适配 {mc_version or '任意版本'}/{loader} 的文件"
            )

        primary = files[0]
        targets: List[Dict[str, Any]] = [primary]

        if with_dependencies and project_type == "mod":
            required = [
                dep
                for dep in primary.get("dependencies", [])
                if dep.get("dependency_type") == "required"
            ]
            for dep in required[:10]:
                project_id = dep.get("project_id")
                if not project_id:
                    continue
                try:
                    dep_versions = await self._api.get_mod_versions(
                        project_id, game_version=mc_version, loaders=[loader]
                    )
                except Exception as exc:
                    logger.warning("依赖解析失败 %s: %s", project_id, exc)
                    continue
                if dep_versions:
                    mapped = ModrinthAPI.to_mod_file(dep_versions[0])
                    if mapped:
                        targets.append(mapped)

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
        logger.info(
            "已安装 %s（%s）到 %s：%d/%d 成功",
            slug, project_type, dest_dir, sum(r["ok"] for r in results), len(results),
        )
        return {
            "primary": primary.get("name"),
            "type": PROJECT_TYPES[project_type],
            "dir": str(dest_dir),
            "files": results,
        }

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
        """启停模组（重命名 .disabled.jar）"""
        if enable:
            return await self._storage.enable_mod(instance_id, file_name)
        return await self._storage.disable_mod(instance_id, file_name)


__all__ = ["ModService", "TYPE_DIRS"]
