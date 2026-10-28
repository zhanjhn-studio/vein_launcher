"""基础设施层 - Mojang 官方 API 实现（支持官方源 / 镜像源自动切换）"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vein_launcher.domain.repositories.network_repo import MojangAPIRepository
from vein_launcher.infrastructure.network.api_client import (
    ApiClient,
    ApiError,
    HttpRepositoryMixin,
)
from vein_launcher.infrastructure.network.download_sources import (
    candidates,
    manifest_candidates,
)

logger = logging.getLogger(__name__)

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
VERSION_MANIFEST_V2 = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


class MojangAPI(HttpRepositoryMixin, MojangAPIRepository):
    """Mojang 版本清单 / 版本 JSON / 资源索引"""

    def __init__(
        self,
        client: Optional[ApiClient] = None,
        source: Optional[str] = None,
        mirror_base: Optional[str] = None,
    ):
        self._client = client or ApiClient()
        self._owns_client = client is None
        self._manifest_cache: Optional[Dict[str, Any]] = None
        self._source = source
        self._mirror_base = mirror_base

    async def __aenter__(self) -> "MojangAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def _manifest(self) -> Dict[str, Any]:
        """拉取版本清单（按下载源策略依次尝试，内存缓存）"""
        if self._manifest_cache is not None:
            return self._manifest_cache

        errors: List[str] = []
        for url in manifest_candidates(self._source, self._mirror_base):
            try:
                self._manifest_cache = await self._client.get_json(url)
                logger.info("版本清单来源：%s", url)
                return self._manifest_cache
            except ApiError as exc:
                errors.append(f"{url} -> {exc}")

        # 最后兜底老地址
        try:
            self._manifest_cache = await self._client.get_json(MANIFEST_URL)
            return self._manifest_cache
        except ApiError as exc:
            errors.append(str(exc))

        raise ApiError("所有版本清单地址均不可用：" + " | ".join(errors[:3]))

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
            if item.get("id") != version_id:
                continue
            last_error: Optional[Exception] = None
            for url in candidates(item["url"], self._source, self._mirror_base):
                try:
                    return await self._client.get_json(url)
                except ApiError as exc:
                    last_error = exc
                    logger.warning("版本 JSON 下载失败 %s：%s", url, exc)
            raise ApiError(f"版本 JSON 获取失败：{version_id}（{last_error}）")
        raise ApiError(f"未找到版本：{version_id}")

    async def fetch_assets_index(self, index_id: str) -> Dict[str, Any]:
        """拉取 assets 索引；index_id 支持传完整 URL"""
        if index_id.startswith("http"):
            return await self._client.get_json(index_id)
        url = f"https://launchermeta.mojang.com/v1/packages/{index_id}/{index_id}.json"
        return await self._client.get_json(url)


__all__ = ["MojangAPI", "MANIFEST_URL", "VERSION_MANIFEST_V2"]
