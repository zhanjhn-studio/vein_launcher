"""下载源管理 —— 官方 / BMCLAPI 镜像 / 自定义镜像

Mojang 资源分布在多个域名：
- launchermeta.mojang.com / piston-meta.mojang.com   版本清单与版本 JSON
- piston-data.mojang.com                             客户端 jar
- libraries.minecraft.net                            Maven 依赖
- resources.download.minecraft.net                   assets 对象

镜像（BMCLAPI）按相同路径镜像以上内容，只替换主机名：
- 清单/JSON : https://bmclapi2.bangbang93.com/v1/...
- Maven     : https://bmclapi2.bangbang93.com/maven/...
- assets    : https://bmclapi2.bangbang93.com/assets/{前两位}/{hash}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

from vein_launcher.common.config.settings import settings_manager


@dataclass(frozen=True, slots=True)
class DownloadSource:
    """一个可用的下载源"""

    id: str
    name: str
    homepage: str
    manifest_url: str
    meta_base: str
    maven_base: str
    assets_base: str

    @property
    def label(self) -> str:
        return f"{self.name}（{self.homepage}）"


OFFICIAL = DownloadSource(
    id="official",
    name="官方源",
    homepage="mojang.com",
    manifest_url="https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    meta_base="https://piston-meta.mojang.com",
    maven_base="https://libraries.minecraft.net",
    assets_base="https://resources.download.minecraft.net",
)

BMCLAPI = DownloadSource(
    id="bmclapi",
    name="BMCLAPI 镜像",
    homepage="bangbang93.com",
    manifest_url="https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json",
    meta_base="https://bmclapi2.bangbang93.com",
    maven_base="https://bmclapi2.bangbang93.com/maven",
    assets_base="https://bmclapi2.bangbang93.com/assets",
)

KNOWN_SOURCES: Dict[str, DownloadSource] = {
    OFFICIAL.id: OFFICIAL,
    BMCLAPI.id: BMCLAPI,
}

# 官方主机 -> 镜像里的路径前缀
_HOST_RULES: Dict[str, str] = {
    "launchermeta.mojang.com": "",
    "piston-meta.mojang.com": "",
    "piston-data.mojang.com": "",
    "libraries.minecraft.net": "/maven",
    "resources.download.minecraft.net": "/assets",
}


def get_source(source_id: Optional[str] = None, mirror_base: Optional[str] = None) -> DownloadSource:
    """按 ID 取下载源；未知 ID 回退官方源"""
    cfg = settings_manager.get().download
    key = source_id or cfg.source
    if key == "auto":
        key = "official"

    if key == "bmclapi":
        base = (mirror_base or cfg.mirror_base).rstrip("/")
        if base != BMCLAPI.manifest_url.rsplit("/mc/", 1)[0]:
            return DownloadSource(
                id="bmclapi",
                name="自定义镜像",
                homepage=base,
                manifest_url=f"{base}/mc/game/version_manifest_v2.json",
                meta_base=base,
                maven_base=f"{base}/maven",
                assets_base=f"{base}/assets",
            )
        return BMCLAPI

    return KNOWN_SOURCES.get(key, OFFICIAL)


def rewrite(url: str, source: DownloadSource) -> str:
    """把官方 URL 重写到指定源；无法识别的主机原样返回"""
    if not url.startswith("http"):
        return url

    parts = urlsplit(url)
    host = parts.netloc.lower()
    if host not in _HOST_RULES:
        return url

    prefix = _HOST_RULES[host]
    if prefix == "/maven":
        # maven_base 已包含 /maven 前缀
        new_url = f"{source.maven_base.rstrip('/')}{parts.path}"
    elif prefix == "/assets":
        # assets_base 已包含 /assets 前缀
        new_url = f"{source.assets_base.rstrip('/')}{parts.path}"
    else:
        new_url = f"{source.meta_base.rstrip('/')}{parts.path}"

    return urlunsplit((parts.scheme, urlsplit(new_url).netloc, urlsplit(new_url).path, parts.query, ""))


def candidates(url: str, preferred: Optional[str] = None, mirror_base: Optional[str] = None) -> List[str]:
    """返回该 URL 的候选地址（按策略排序，去重）

    preferred:
        auto      -> 官方 → 镜像（失败自动切换）
        official  -> 仅官方
        bmclapi   -> 仅镜像
    """
    cfg = settings_manager.get().download
    strategy = preferred or cfg.source
    official_url = url
    mirror_url = rewrite(url, get_source("bmclapi", mirror_base))

    if official_url == mirror_url:  # 无法重写（如 Modrinth CDN）
        return [official_url]

    if strategy == "official":
        return [official_url]
    if strategy == "bmclapi":
        return [mirror_url]
    # auto：官方优先，镜像兜底
    return [official_url, mirror_url]


def manifest_candidates(preferred: Optional[str] = None, mirror_base: Optional[str] = None) -> List[str]:
    """版本清单的候选地址（独立策略 version_list_source）"""
    cfg = settings_manager.get().download
    strategy = preferred or cfg.version_list_source
    if strategy == "official":
        return [OFFICIAL.manifest_url]
    if strategy == "bmclapi":
        return [rewrite(OFFICIAL.manifest_url, get_source("bmclapi", mirror_base))]
    return [
        OFFICIAL.manifest_url,
        rewrite(OFFICIAL.manifest_url, get_source("bmclapi", mirror_base)),
    ]


def describe_sources() -> List[Tuple[str, str]]:
    """给 UI 用的下载源清单：(id, 显示名)"""
    return [(s.id, s.name) for s in KNOWN_SOURCES.values()]


__all__ = [
    "BMCLAPI",
    "OFFICIAL",
    "DownloadSource",
    "KNOWN_SOURCES",
    "candidates",
    "describe_sources",
    "get_source",
    "manifest_candidates",
    "rewrite",
]
