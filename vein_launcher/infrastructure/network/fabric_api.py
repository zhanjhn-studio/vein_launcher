"""基础设施层 - Fabric / Quilt Meta API 实现"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from vein_launcher.domain.repositories.network_repo import FabricAPIRepository
from vein_launcher.infrastructure.network.api_client import ApiClient, ApiError, HttpRepositoryMixin

FABRIC_BASE = "https://meta.fabricmc.net/v2"
QUILT_BASE = "https://meta.quiltmc.org/v3"


class FabricAPI(HttpRepositoryMixin, FabricAPIRepository):
    """Fabric 加载器版本与安装 profile"""

    def __init__(self, client: Optional[ApiClient] = None, base: str = FABRIC_BASE):
        self._client = client or ApiClient()
        self._owns_client = client is None
        self._base = base

    async def __aenter__(self) -> "FabricAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def get_loader_versions(self, mc_version: str) -> List[Dict[str, Any]]:
        """某 MC 版本可用的全部 Loader（新版本在前）"""
        url = f"{self._base}/versions/loader/{quote(mc_version)}"
        data = await self._client.get_json(url)
        return list(data) if isinstance(data, list) else []

    async def get_latest_loader(self, mc_version: str) -> Dict[str, Any]:
        """最新稳定 Loader；无稳定版则回退第一个"""
        versions = await self.get_loader_versions(mc_version)
        if not versions:
            raise ApiError(f"未找到 {mc_version} 的 Fabric Loader", url=mc_version)
        for item in versions:
            if item.get("loader", {}).get("stable"):
                return item
        return versions[0]

    async def get_install_profile(self, mc_version: str, loader_version: str) -> Dict[str, Any]:
        """获取 Fabric 安装 profile（版本 JSON 形式）"""
        url = f"{self._base}/versions/loader/{quote(mc_version)}/{quote(loader_version)}/profile/json"
        return await self._client.get_json(url)

    async def get_fabric_api_versions(
        self,
        mc_version: str,
        loader_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fabric API 模组可用版本（借助 Modrinth 更可靠，此处保留 Meta 查询）"""
        url = f"{self._base}/versions/game"
        data = await self._client.get_json(url)
        return [item for item in data if item.get("version") == mc_version]


class QuiltAPI(FabricAPI):
    """Quilt 加载器（API 结构与 Fabric 基本一致）"""

    def __init__(self, client: Optional[ApiClient] = None):
        super().__init__(client=client, base=QUILT_BASE)


__all__ = ["FabricAPI", "QuiltAPI", "FABRIC_BASE", "QUILT_BASE"]
