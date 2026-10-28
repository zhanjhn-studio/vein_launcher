"""基础设施层 - CurseForge API 客户端（需要 API Key）"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vein_launcher.infrastructure.network.http_client import HttpClient, HttpClientError

logger = logging.getLogger(__name__)

BASE = "https://api.curseforge.com/v1"
MINECRAFT_GAME_ID = 432

# Minecraft 分类
CLASS_IDS = {"mod": 6, "modpack": 4471, "resourcepack": 12, "shader": 6552}
LOADER_TYPES = {"forge": 1, "fabric": 4, "quilt": 5, "neoforge": 6}


class CurseForgeApiClient:
    """CurseForge 搜索 / 文件列表"""

    def __init__(self, api_key: str = "", http: Optional[HttpClient] = None):
        self._api_key = api_key
        self._http = http or HttpClient()
        self._owns = http is None

    async def close(self) -> None:
        if self._owns:
            await self._http.close()

    def _headers(self) -> Dict[str, str]:
        if not self._api_key:
            raise HttpClientError("CurseForge 需要 API Key")
        return {"x-api-key": self._api_key}

    async def search(
        self,
        query: str,
        project_type: str = "mod",
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        class_id = CLASS_IDS.get(project_type)
        if class_id is None:
            raise HttpClientError(f"CurseForge 不支持类型：{project_type}")

        params: Dict[str, Any] = {
            "gameId": MINECRAFT_GAME_ID,
            "classId": class_id,
            "searchFilter": query or "",
            "pageSize": min(max(limit, 1), 50),
            "sortField": 2,
            "sortOrder": "desc",
        }
        if game_version:
            params["gameVersion"] = game_version
        if loader in LOADER_TYPES:
            params["modLoaderType"] = LOADER_TYPES[loader]

        data = await self._http.get_json(
            f"{BASE}/mods/search", params=params, headers=self._headers()
        )
        return list(data.get("data", []))

    async def files(
        self,
        mod_id: int,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if game_version:
            params["gameVersion"] = game_version
        if loader in LOADER_TYPES:
            params["modLoaderType"] = LOADER_TYPES[loader]
        data = await self._http.get_json(
            f"{BASE}/mods/{mod_id}/files", params=params or None, headers=self._headers()
        )
        return list(data.get("data", []))

    # ------------------------------------------------------------------
    @staticmethod
    def download_url(item: Dict[str, Any]) -> Optional[str]:
        url = item.get("downloadUrl")
        if url:
            return url
        file_id, name = item.get("id"), item.get("fileName")
        if not file_id or not name:
            return None
        return f"https://edge.forgecdn.net/files/{file_id // 1000}/{file_id % 1000}/{name}"

    @staticmethod
    def summary(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "slug": str(item.get("id", "")),
            "title": item.get("name", ""),
            "description": item.get("summary", ""),
            "icon": (item.get("logo") or {}).get("thumbnailUrl", ""),
            "downloads": item.get("downloadCount", 0),
            "author": ", ".join(a.get("name", "") for a in item.get("authors", [])),
            "type": "mod",
            "url": (item.get("links") or {}).get("websiteUrl", ""),
        }


__all__ = ["CurseForgeApiClient", "CLASS_IDS", "LOADER_TYPES"]
