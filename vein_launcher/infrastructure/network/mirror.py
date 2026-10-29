"""下载源镜像（BMCLAPI）：官方地址 → 国内镜像

用途：Mojang 官方源在本机不可达时，自动改走 BMCLAPI 镜像。
所有 URL 只做字符串前缀替换，不改变文件内容；SHA-1 仍按官方清单校验。
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

BMCLAPI = "https://bmclapi2.bangbang93.com"

# 顺序敏感：先匹配更具体的 libraries / assets
RULES = (
    ("https://libraries.minecraft.net", f"{BMCLAPI}/maven"),
    ("https://resources.download.minecraft.net", f"{BMCLAPI}/assets"),
    ("https://piston-meta.mojang.com", BMCLAPI),
    ("https://launchermeta.mojang.com", BMCLAPI),
    ("https://launcher.mojang.com", BMCLAPI),
    ("https://piston-data.mojang.com", BMCLAPI),
)

# env: auto（默认，镜像优先）/ mirror（只用镜像）/ official（只用官方）
MODE = os.environ.get("VEIN_DOWNLOAD_SOURCE", "auto").lower()

from urllib.parse import urlparse

# 已确认证书链不完整的镜像节点（进程内记忆，避免每次先失败再降级）
_INSECURE_HOSTS: set[str] = set()


def is_insecure(url: str) -> bool:
    return urlparse(url).hostname in _INSECURE_HOSTS


def mark_insecure(url: str) -> None:
    host = urlparse(url).hostname
    if host:
        _INSECURE_HOSTS.add(host)


def mirror(url: str) -> str:
    """返回该地址对应的镜像地址；无对应规则则原样返回"""
    if MODE == "official":
        return url
    for official, mirrored in RULES:
        if url.startswith(official):
            return url.replace(official, mirrored, 1)
    return url


def candidates(url: str) -> list[str]:
    """按优先级返回候选地址（镜像 → 官方，或反向）"""
    mirrored = mirror(url)
    if MODE == "official":
        return [url]
    if MODE == "mirror":
        return [mirrored]
    return ([mirrored, url] if mirrored != url else [url])


__all__ = ["mirror", "candidates", "is_insecure", "mark_insecure", "BMCLAPI", "MODE"]
