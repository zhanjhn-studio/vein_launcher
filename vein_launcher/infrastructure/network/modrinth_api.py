"""基础设施层 - Modrinth API 实现（模组市场主通道）"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from vein_launcher.domain.repositories.network_repo import ModrinthAPIRepository
from vein_launcher.infrastructure.network.api_client import ApiClient, HttpRepositoryMixin

logger = logging.getLogger(__name__)

MODRINTH_BASE = "https://api.modrinth.com/v2"


class ModrinthAPI(HttpRepositoryMixin, ModrinthAPIRepository):
    """Modrinth 搜索 / 项目 / 版本 / 依赖"""

    def __init__(self, client: Optional[ApiClient] = None):
        self._client = client or ApiClient(headers={"Accept": "application/json"})
        self._owns_client = client is None

    async def __aenter__(self) -> "ModrinthAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def search_mods(
        self,
        query: str,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        game_versions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索模组；tags 形如 ["fabric"]，game_versions 形如 ["1.20.4"]"""
        facets: List[List[str]] = []
        facets.append(["project_type:mod"])
        for tag in tags or []:
            facets.append([f"categories:{tag}"])
        for ver in game_versions or []:
            facets.append([f"versions:{ver}"])

        params = {
            "query": query or "",
            "limit": min(max(limit, 1), 100),
            "index": "relevance",
            "facets": json.dumps(facets, separators=(",", ":")),
        }
        data = await self._client.get_json(f"{MODRINTH_BASE}/search", params=params)
        return list(data.get("hits", []))

    async def get_project(self, project_slug: str) -> Dict[str, Any]:
        """项目详情"""
        return await self._client.get_json(f"{MODRINTH_BASE}/project/{quote(project_slug)}")

    async def get_mod_versions(
        self,
        project_slug: str,
        game_version: Optional[str] = None,
        loaders: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """某模组的文件列表（按发布时间倒序）"""
        params: Dict[str, Any] = {}
        if game_version:
            params["game_versions"] = json.dumps([game_version])
        if loaders:
            params["loaders"] = json.dumps(loaders)
        url = f"{MODRINTH_BASE}/project/{quote(project_slug)}/version"
        data = await self._client.get_json(url, params=params or None)
        versions = list(data) if isinstance(data, list) else []
        return sorted(versions, key=lambda v: v.get("date_published", ""), reverse=True)

    async def get_version(self, version_id: str) -> Dict[str, Any]:
        """单个文件版本详情（含 dependencies）"""
        return await self._client.get_json(f"{MODRINTH_BASE}/version/{quote(version_id)}")

    # -------------------- 结果映射（统一为 UI 友好的 dict） --------------------
    @staticmethod
    def to_mod_summary(hit: Dict[str, Any]) -> Dict[str, Any]:
        """把搜索结果映射成稳定的 UI 数据结构"""
        return {
            "source": "modrinth",
            "slug": hit.get("slug", ""),
            "project_id": hit.get("project_id", ""),
            "title": hit.get("title", ""),
            "description": hit.get("description", ""),
            "icon_url": hit.get("icon_url") or "",
            "downloads": hit.get("downloads", 0),
            "follows": hit.get("follows", 0),
            "categories": hit.get("categories", []),
            "versions": hit.get("versions", []),
            "author": hit.get("author", ""),
            "page_url": f"https://modrinth.com/mod/{hit.get('slug', '')}",
        }

    @staticmethod
    def to_mod_file(version: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """把 version 对象的主文件映射为可下载结构"""
        files = version.get("files") or []
        primary = next((f for f in files if f.get("primary")), files[0] if files else None)
        if not primary:
            return None
        return {
            "file_id": version.get("id", ""),
            "name": primary.get("filename", ""),
            "url": primary.get("url", ""),
            "size": primary.get("size", 0),
            "sha1": (primary.get("hashes") or {}).get("sha1", ""),
            "sha512": (primary.get("hashes") or {}).get("sha512", ""),
            "version_number": version.get("version_number", ""),
            "game_versions": version.get("game_versions", []),
            "loaders": version.get("loaders", []),
            "release_type": version.get("version_type", "release"),
            "date_published": version.get("date_published", ""),
            "dependencies": version.get("dependencies", []),
        }


__all__ = ["ModrinthAPI", "MODRINTH_BASE"]
