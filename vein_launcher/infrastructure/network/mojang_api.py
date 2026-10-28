"""基础设施层 - Mojang 官方 API 实现"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vein_launcher.domain.repositories.network_repo import MojangAPIRepository
from vein_launcher.infrastructure.network.api_client import ApiClient, ApiError, HttpRepositoryMixin

logger = logging.getLogger(__name__)

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
VERSION_MANIFEST_V2 = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"


class MojangAPI(HttpRepositoryMixin, MojangAPIRepository):
    """Mojang 版本清单 / 版本 JSON / 资源索引"""

    def __init__(self, client: Optional[ApiClient] = None):
        self._client = client or ApiClient()
        self._owns_client = client is None
        self._manifest_cache: Optional[Dict[str, Any]] = None

    async def __aenter__(self) -> "MojangAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def _manifest(self) -> Dict[str, Any]:
        """拉取版本清单（内存缓存）"""
        if self._manifest_cache is None:
            try:
                self._manifest_cache = await self._client.get_json(VERSION_MANIFEST_V2)
            except ApiError:
                # 回退旧版清单地址
                self._manifest_cache = await self._client.get_json(MANIFEST_URL)
        return self._manifest_cache

    async def fetch_version_list(self) -> List[Dict[str, Any]]:
        """所有版本（新的在前）"""
        manifest = await self._manifest()
        return list(manifest.get("versions", []))

    async def fetch_latest(self) -> Dict[str, str]:
        """latest.release / latest.snapshot"""
        manifest = await self._manifest()
        return dict(manifest.get("latest", {}))

    async def fetch_version(self, version_id: str) -> Dict[str, Any]:
        """按版本 ID 拉取完整版本 JSON（含 inheritsFrom/libraries/assetIndex）"""
        manifest = await self._manifest()
        for item in manifest.get("versions", []):
            if item.get("id") == version_id:
                return await self._client.get_json(item["url"])
        raise ApiError(f"未找到版本：{version_id}")

    async def fetch_assets_index(self, index_id: str) -> Dict[str, Any]:
        """拉取 assets 索引；index_id 支持传完整 URL"""
        if index_id.startswith("http"):
            return await self._client.get_json(index_id)
        # 兜底：从资源 CDN 约定地址尝试
        url = f"https://launchermeta.mojang.com/v1/packages/{index_id}/{index_id}.json"
        return await self._client.get_json(url)


__all__ = ["MojangAPI", "MANIFEST_URL", "VERSION_MANIFEST_V2"]
