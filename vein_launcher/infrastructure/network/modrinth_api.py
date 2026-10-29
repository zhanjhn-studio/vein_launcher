"""基础设施层 - Modrinth API 客户端"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from vein_launcher.infrastructure.network.http_client import HttpClient

logger = logging.getLogger(__name__)

BASE = "https://api.modrinth.com/v2"


class ModrinthApiClient:
    """Modrinth 搜索 / 项目 / 版本"""

    def __init__(self, http: Optional[HttpClient] = None):
        self._http = http or HttpClient()
        self._owns = http is None

    async def close(self) -> None:
        if self._owns:
            await self._http.close()

    # ------------------------------------------------------------------
    async def search(
        self,
        query: str,
        project_type: str = "mod",
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        limit: int = 20,
        sort: str = "relevance",
    ) -> List[Dict[str, Any]]:
        facets = [[f"project_type:{project_type}"]]
        if loader:
            facets.append([f"categories:{loader}"])
        if game_version:
            facets.append([f"versions:{game_version}"])

        data = await self._http.get_json(
            f"{BASE}/search",
            params={
                "query": query or "",
                "limit": min(max(limit, 1), 100),
                "index": sort,
                "facets": json.dumps(facets, separators=(",", ":")),
            },
        )
        return list(data.get("hits", []))

    async def featured(
        self,
        project_type: str = "mod",
        loader: Optional[str] = None,
        game_version: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """按下载量排序的热门资源（推荐页）"""
        return await self.search(
            "",
            project_type=project_type,
            game_version=game_version,
            loader=loader,
            limit=limit,
            sort="downloads",
        )

    async def project(self, slug: str) -> Dict[str, Any]:
        return await self._http.get_json(f"{BASE}/project/{quote(slug)}")

    async def versions(
        self,
        slug: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if game_version:
            params["game_versions"] = json.dumps([game_version])
        if loader:
            params["loaders"] = json.dumps([loader])
        data = await self._http.get_json(
            f"{BASE}/project/{quote(slug)}/version", params=params or None
        )
        versions = list(data) if isinstance(data, list) else []
        return sorted(versions, key=lambda v: v.get("date_published", ""), reverse=True)

    # ------------------------------------------------------------------
    @staticmethod
    def summary(hit: Dict[str, Any]) -> Dict[str, Any]:
        ptype = hit.get("project_type", "mod")
        return {
            "slug": hit.get("slug", ""),
            "title": hit.get("title", ""),
            "description": hit.get("description", ""),
            "icon": hit.get("icon_url") or "",
            "downloads": hit.get("downloads", 0),
            "author": hit.get("author", ""),
            "type": ptype,
            "url": f"https://modrinth.com/{ptype}/{hit.get('slug', '')}",
        }

    @staticmethod
    def file_of(version: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        files = version.get("files") or []
        primary = next((f for f in files if f.get("primary")), files[0] if files else None)
        if not primary:
            return None
        return {
            "name": primary.get("filename", ""),
            "url": primary.get("url", ""),
            "size": primary.get("size", 0),
            "sha1": (primary.get("hashes") or {}).get("sha1", ""),
            "version": version.get("version_number", ""),
            "game_versions": version.get("game_versions", []),
            "loaders": version.get("loaders", []),
            "dependencies": version.get("dependencies", []),
        }


__all__ = ["ModrinthApiClient", "BASE"]
