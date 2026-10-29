"""基础设施层 - Mojang API 客户端

对应架构：infrastructure/network/api_client.py
基于 http_client.HttpClient，负责 Mojang 版本相关接口：
- 版本清单（version_manifest_v2.json）
- 单个版本 JSON（含 libraries / assetIndex 等）
- assets 索引

不包含：下载、缓存落盘、镜像切换（均不在当前需求内）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vein_launcher.infrastructure.network.http_client import HttpClient, HttpClientError
from vein_launcher.infrastructure.network.mirror import candidates, mirror

logger = logging.getLogger(__name__)

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


class MojangApiClient:
    """Mojang 版本 API"""

    def __init__(self, http: Optional[HttpClient] = None):
        self._http = http or HttpClient()
        self._manifest: Optional[Dict[str, Any]] = None

    async def __aenter__(self) -> "MojangApiClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    async def fetch_manifest(self) -> Dict[str, Any]:
        """版本清单（内存缓存一次，镜像优先）"""
        if self._manifest is None:
            last: Optional[Exception] = None
            for url in candidates(MANIFEST_URL):
                try:
                    logger.debug("拉取版本清单：%s", url)
                    self._manifest = await self._http.get_json(url)
                    break
                except Exception as exc:  # 镜像失败自动回退官方
                    last = exc
                    logger.warning("版本清单源失败 %s：%s", url, exc)
            if self._manifest is None:
                raise HttpClientError(f"版本清单获取失败：{last}", url=MANIFEST_URL)
        return self._manifest

    async def fetch_version_list(self) -> List[Dict[str, Any]]:
        """版本列表（Mojang 返回顺序：新版本在前）"""
        manifest = await self.fetch_manifest()
        return list(manifest.get("versions", []))

    async def fetch_latest(self) -> Dict[str, str]:
        """latest.release / latest.snapshot"""
        manifest = await self.fetch_manifest()
        return dict(manifest.get("latest", {}))

    async def fetch_version(self, version_id: str) -> Dict[str, Any]:
        """按版本 ID 取完整版本 JSON"""
        manifest = await self.fetch_manifest()
        for item in manifest.get("versions", []):
            if item.get("id") == version_id:
                url = item.get("url")
                if not url:
                    raise HttpClientError(f"版本缺少下载地址：{version_id}", url="")
                return await self._http.get_json(mirror(url))
        raise HttpClientError(f"未找到版本：{version_id}", url=MANIFEST_URL)

    async def fetch_assets_index(self, url: str) -> Dict[str, Any]:
        """取 assets 索引 JSON（传入 assetIndex.url）"""
        if not url:
            raise HttpClientError("assets 索引地址为空", url="")
        return await self._http.get_json(mirror(url))


__all__ = ["MojangApiClient", "MANIFEST_URL"]
