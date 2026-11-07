"""authlib-injector 获取：LittleSkin / 皮肤站账号进游戏必需。

优先用官方 artifact 元数据拿最新 jar，失败则退回 GitHub latest 下载。
网络被 TLS 中间人拦截时退回不校验会话（与下载器一致）。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

META_URL = "https://authlib-injector.yushi.moe/artifact/latest.json"
GITHUB_URL = "https://github.com/yushijinhun/authlib-injector/releases/latest/download/authlib-injector.jar"
MIN_SIZE = 100_000


def target_path() -> Path:
    from vein_launcher.common.utils.path_utils import get_root_dir

    return get_root_dir() / "downloads" / "authlib-injector.jar"


async def ensure_authlib_injector(force: bool = False) -> Optional[Path]:
    """返回本地 jar 路径；下载失败返回 None（不抛异常，避免阻塞启动）"""
    import aiohttp

    target = target_path()
    if not force and target.is_file() and target.stat().st_size > MIN_SIZE:
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    urls = [GITHUB_URL]
    timeout = aiohttp.ClientTimeout(total=180)

    async def _fetch(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.info("authlib-injector 下载失败（%s）：HTTP %s", url, resp.status)
                    return None
                return await resp.read()
        except aiohttp.ClientSSLError:
            logger.warning("authlib-injector 证书校验失败，改用不校验会话重试：%s", url)
            try:
                async with session.get(url, ssl=False) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.read()
            except Exception as exc:
                logger.info("authlib-injector 重试失败：%s", exc)
                return None
        except Exception as exc:
            logger.info("authlib-injector 请求失败（%s）：%s", url, exc)
            return None

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(META_URL) as resp:
                    if resp.status == 200:
                        meta = await resp.json(content_type=None)
                        download_url = meta.get("download_url") if isinstance(meta, dict) else None
                        if download_url:
                            urls.insert(0, str(download_url))
            except Exception as exc:
                logger.info("authlib-injector 版本信息获取失败：%s", exc)

            for url in urls:
                data = await _fetch(session, url)
                if data and len(data) > MIN_SIZE:
                    target.write_bytes(data)
                    logger.info("authlib-injector 已就绪：%s（%.0f KB）", target, len(data) / 1024)
                    return target
    except Exception as exc:
        logger.warning("authlib-injector 下载异常：%s", exc)
    return None


__all__ = ["ensure_authlib_injector", "target_path"]
