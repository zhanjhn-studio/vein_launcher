"""基础设施层 - CurseForge API 实现（需 API Key）"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from vein_launcher.domain.repositories.network_repo import CurseForgeAPIRepository
from vein_launcher.infrastructure.network.api_client import ApiClient, ApiError, HttpRepositoryMixin

logger = logging.getLogger(__name__)

CURSEFORGE_BASE = "https://api.curseforge.com/v1"
MINECRAFT_GAME_ID = 432
MOD_CLASS_ID = 6


class CurseForgeAPI(HttpRepositoryMixin, CurseForgeAPIRepository):
    """CurseForge 项目搜索 / 文件列表

    注意：CF 强制要求 x-api-key，未配置时调用会抛 ApiError。
    """

    def __init__(self, client: Optional[ApiClient] = None, api_key: str = ""):
        self._client = client or ApiClient(headers={"Accept": "application/json"})
        self._owns_client = client is None
        self._api_key = api_key

    async def __aenter__(self) -> "CurseForgeAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    def _headers(self, api_key: str) -> Dict[str, str]:
        key = api_key or self._api_key
        if not key:
            raise ApiError("CurseForge 需要 API Key，请先在设置中配置")
        return {"x-api-key": key}

    async def search_projects(
        self,
        query: str,
        api_key: str = "",
        limit: int = 25,
        game_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索模组项目（每页上限 50，这里默认 25）"""
        params: Dict[str, Any] = {
            "gameId": MINECRAFT_GAME_ID,
            "classId": MOD_CLASS_ID,
            "searchFilter": query or "",
            "pageSize": min(max(limit, 1), 50),
            "sortField": 2,      # 2 = Popularity
            "sortOrder": "desc",
        }
        if game_version:
            params["gameVersion"] = game_version
        data = await self._client.get_json(
            f"{CURSEFORGE_BASE}/mods/search", params=params, headers=self._headers(api_key)
        )
        return list(data.get("data", []))

    async def get_files(
        self,
        mod_id: int,
        api_key: str = "",
        game_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """某项目的文件列表"""
        params = {"gameVersion": game_version} if game_version else None
        data = await self._client.get_json(
            f"{CURSEFORGE_BASE}/mods/{mod_id}/files",
            params=params,
            headers=self._headers(api_key),
        )
        return list(data.get("data", []))

    @staticmethod
    def to_mod_summary(item: Dict[str, Any]) -> Dict[str, Any]:
        """映射为统一 UI 结构"""
        return {
            "source": "curseforge",
            "slug": str(item.get("id", "")),
            "project_id": item.get("id"),
            "title": item.get("name", ""),
            "description": item.get("summary", ""),
            "icon_url": (item.get("logo") or {}).get("thumbnailUrl", ""),
            "downloads": item.get("downloadCount", 0),
            "categories": [c.get("name", "") for c in item.get("categories", [])],
            "author": ", ".join(a.get("name", "") for a in item.get("authors", [])),
            "page_url": (item.get("links") or {}).get("websiteUrl", ""),
        }

    @staticmethod
    def to_mod_file(item: Dict[str, Any]) -> Dict[str, Any]:
        """映射文件结构"""
        return {
            "file_id": item.get("id"),
            "name": item.get("fileName", ""),
            "url": item.get("downloadUrl", ""),
            "size": item.get("fileLength", 0),
            "sha1": ((item.get("hashes") or [{}])[0] or {}).get("value", ""),
            "version_number": item.get("displayName", ""),
            "game_versions": item.get("gameVersions", []),
            "release_type": {1: "release", 2: "beta", 3: "alpha"}.get(
                item.get("releaseType", 1), "release"
            ),
            "dependencies": [
                {"project_id": d.get("modId"), "relation_type": d.get("relationType")}
                for d in item.get("dependencies", [])
            ],
        }


__all__ = ["CurseForgeAPI", "CURSEFORGE_BASE", "MINECRAFT_GAME_ID"]
