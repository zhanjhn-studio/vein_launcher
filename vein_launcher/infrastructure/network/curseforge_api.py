"""基础设施层 - CurseForge API（需 API Key）

覆盖：Mod / 整合包 / 资源包 / 光影包 四类。
CurseForge 用 classId 区分项目类型，用 modLoaderType 过滤加载器。

注意：部分作者关闭了第三方下载，`downloadUrl` 会返回 null，
此时按 CF 的 CDN 规则拼接：edge.forgecdn.net/files/{id/1000}/{id%1000}/{fileName}
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vein_launcher.domain.repositories.network_repo import CurseForgeAPIRepository
from vein_launcher.infrastructure.network.api_client import (
    ApiClient,
    ApiError,
    HttpRepositoryMixin,
)

logger = logging.getLogger(__name__)

CURSEFORGE_BASE = "https://api.curseforge.com/v1"
MINECRAFT_GAME_ID = 432

# Minecraft 分类 ID
CLASS_IDS = {
    "mod": 6,
    "modpack": 4471,
    "resourcepack": 12,
    "shader": 6552,
}

# 加载器枚举（CF modLoaderType）
LOADER_TYPES = {
    "forge": 1,
    "fabric": 4,
    "quilt": 5,
    "neoforge": 6,
}

RELEASE_TYPES = {1: "release", 2: "beta", 3: "alpha"}


class CurseForgeAPI(HttpRepositoryMixin, CurseForgeAPIRepository):
    """CurseForge 项目搜索 / 文件列表 / 下载地址解析"""

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

    # ------------------------------------------------------------------
    def _headers(self, api_key: str = "") -> Dict[str, str]:
        key = api_key or self._api_key
        if not key:
            raise ApiError("CurseForge 需要 API Key（设置 → 下载 → CurseForge）")
        return {"x-api-key": key}

    @staticmethod
    def project_type_supported(project_type: str) -> bool:
        return project_type in CLASS_IDS

    # ------------------------------------------------------------------
    async def search_projects(
        self,
        query: str,
        api_key: str = "",
        limit: int = 25,
        game_version: Optional[str] = None,
        project_type: str = "mod",
        loader: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """按类型搜索（每页上限 50）"""
        class_id = CLASS_IDS.get(project_type)
        if class_id is None:
            raise ApiError(f"CurseForge 不支持该资源类型：{project_type}")

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
        if loader and loader in LOADER_TYPES:
            params["modLoaderType"] = LOADER_TYPES[loader]

        data = await self._client.get_json(
            f"{CURSEFORGE_BASE}/mods/search", params=params, headers=self._headers(api_key)
        )
        return list(data.get("data", []))

    async def get_files(
        self,
        mod_id: int,
        api_key: str = "",
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """某项目的文件列表（新→旧）"""
        params: Dict[str, Any] = {}
        if game_version:
            params["gameVersion"] = game_version
        if loader and loader in LOADER_TYPES:
            params["modLoaderType"] = LOADER_TYPES[loader]

        data = await self._client.get_json(
            f"{CURSEFORGE_BASE}/mods/{mod_id}/files",
            params=params or None,
            headers=self._headers(api_key),
        )
        files = list(data.get("data", []))
        return sorted(files, key=lambda f: f.get("fileDate", ""), reverse=True)

    # ------------------------------------------------------------------
    @staticmethod
    def resolve_download_url(item: Dict[str, Any]) -> Optional[str]:
        """取下载地址；作者关闭第三方下载时按 CDN 规则拼接"""
        url = item.get("downloadUrl")
        if url:
            return url
        file_id = item.get("id")
        name = item.get("fileName")
        if not file_id or not name:
            return None
        return f"https://edge.forgecdn.net/files/{file_id // 1000}/{file_id % 1000}/{name}"

    # ------------------------------------------------------------------
    @staticmethod
    def to_mod_summary(item: Dict[str, Any], project_type: str = "mod") -> Dict[str, Any]:
        """搜索结果 -> 统一 UI 结构"""
        links = item.get("links") or {}
        indexes = item.get("latestFilesIndexes") or []
        versions = sorted(
            {index.get("gameVersion") for index in indexes if index.get("gameVersion")}
        )
        return {
            "source": "curseforge",
            "slug": str(item.get("id", "")),
            "project_id": item.get("id"),
            "project_type": project_type,
            "title": item.get("name", ""),
            "description": item.get("summary", ""),
            "icon_url": (item.get("logo") or {}).get("thumbnailUrl", ""),
            "downloads": item.get("downloadCount", 0),
            "follows": 0,
            "categories": [c.get("name", "") for c in item.get("categories", [])],
            "author": ", ".join(a.get("name", "") for a in item.get("authors", [])),
            "page_url": links.get("websiteUrl", ""),
            "versions": versions,
        }

    @staticmethod
    def to_mod_file(item: Dict[str, Any]) -> Dict[str, Any]:
        """文件 -> 统一下载结构"""
        return {
            "file_id": item.get("id"),
            "name": item.get("fileName", ""),
            "url": CurseForgeAPI.resolve_download_url(item),
            "size": item.get("fileLength", 0),
            "sha1": "",
            "version_number": item.get("displayName", ""),
            "game_versions": item.get("gameVersions", []),
            "release_type": RELEASE_TYPES.get(item.get("releaseType", 1), "release"),
            "dependencies": [
                {
                    "project_id": d.get("modId"),
                    "dependency_type": "required" if d.get("relationType") == 3 else "optional",
                }
                for d in item.get("dependencies", [])
            ],
        }


__all__ = ["CurseForgeAPI", "CLASS_IDS", "LOADER_TYPES", "CURSEFORGE_BASE"]
