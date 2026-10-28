"""基础设施层 - 通用异步 HTTP 客户端

统一封装 aiohttp 的会话管理、UA、代理、超时与重试，
供 Mojang / Fabric / Modrinth / CurseForge 各 API 实现复用。
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import aiohttp

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.exceptions import VeinError

logger = logging.getLogger(__name__)

DEFAULT_UA = "VeinLauncher/0.1.0 (Minecraft Java Launcher; +https://github.com/zhanjhn-studio/vein_launcher)"


class ApiError(VeinError):
    """网络 API 调用失败"""

    def __init__(self, message: str, url: str = "", status: int = 0):
        super().__init__(message)
        self.url = url
        self.status = status


class HttpRepositoryMixin:
    """为 Domain 仓储抽象类补齐 get_json / stream_download 两个基础实现

    Domain 层的 AbstractNetworkRepository 要求这两个方法，
    各具体 API 类通过本 mixin 获得默认实现，避免重复代码。
    """

    _client: "ApiClient"

    async def get_json(self, url: str) -> Any:
        return await self._client.get_json(url)

    async def stream_download(self, url: str, save_path: str, progress_callback=None) -> bool:
        from vein_launcher.infrastructure.download.downloader import download_file

        result = await download_file(url, Path(save_path), progress_callback=progress_callback)
        return bool(result)


class ApiClient:
    """轻量异步 HTTP 客户端

    用法：
        async with ApiClient() as api:
            data = await api.get_json("https://launchermeta.mojang.com/...")
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_UA,
        timeout: float = 30.0,
        retries: int = 3,
        headers: Optional[Mapping[str, str]] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self._ua = user_agent
        self._timeout = timeout
        self._retries = max(0, retries)
        self._headers: Dict[str, str] = {"User-Agent": user_agent, **dict(headers or {})}
        self._session = session
        self._owns_session = session is None
        self._closed = False

    # -------------------------- 生命周期 --------------------------
    async def __aenter__(self) -> "ApiClient":
        await self.session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def session(self) -> aiohttp.ClientSession:
        """获取（或惰性创建）会话"""
        if self._session is not None and not self._session.closed:
            return self._session
        if self._closed:
            raise ApiError("ApiClient 已关闭")
        cfg = settings_manager.get().network
        proxy = self._proxy_url(cfg)
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout, sock_connect=15),
            headers=self._headers,
            proxy=proxy,
        )
        self._owns_session = True
        return self._session

    async def close(self) -> None:
        """关闭自建会话"""
        self._closed = True
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    @staticmethod
    def _proxy_url(cfg) -> Optional[str]:
        """根据配置生成代理 URL"""
        if not cfg.proxy_enabled or not cfg.proxy_host:
            return None
        scheme = "socks5" if cfg.proxy_type.upper() == "SOCKS5" else "http"
        port = cfg.proxy_port or (1080 if scheme == "socks5" else 8080)
        return f"{scheme}://{cfg.proxy_host}:{port}"

    # -------------------------- 原语请求 --------------------------
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """执行请求（带重试）；返回的响应由调用方负责读取"""
        session = await self.session()
        last_exc: Optional[BaseException] = None

        for attempt in range(self._retries + 1):
            try:
                resp = await session.request(method, url, **kwargs)
                if resp.status >= 500 or resp.status == 429:
                    body = await resp.text()
                    resp.release()
                    last_exc = ApiError(
                        f"服务端错误 HTTP {resp.status}", url=url, status=resp.status
                    )
                    logger.warning(
                        "请求失败(%s/%s) %s %s -> %s %s",
                        attempt + 1, self._retries + 1, method, url, resp.status, body[:200],
                    )
                else:
                    return resp
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                logger.warning("请求异常(%s/%s) %s -> %s", attempt + 1, self._retries + 1, url, exc)

            if attempt < self._retries:
                await asyncio.sleep(min(1.5 ** attempt, 6.0))

        if isinstance(last_exc, ApiError):
            raise last_exc
        raise ApiError(f"请求失败：{last_exc}", url=url)

    # -------------------------- 便捷方法 --------------------------
    async def get_json(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """GET 并解析 JSON"""
        async with await self.request("GET", url, params=params, headers=headers) as resp:
            if resp.status != 200:
                raise ApiError(f"HTTP {resp.status}", url=url, status=resp.status)
            try:
                return await resp.json(content_type=None)
            except ValueError as exc:
                raise ApiError(f"JSON 解析失败：{exc}", url=url, status=resp.status) from exc

    async def get_text(self, url: str, headers: Optional[Mapping[str, str]] = None) -> str:
        """GET 并返回文本"""
        async with await self.request("GET", url, headers=headers) as resp:
            if resp.status != 200:
                raise ApiError(f"HTTP {resp.status}", url=url, status=resp.status)
            return await resp.text()

    async def get_bytes(self, url: str) -> bytes:
        """GET 并返回二进制（小文件场景）"""
        async with await self.request("GET", url) as resp:
            if resp.status != 200:
                raise ApiError(f"HTTP {resp.status}", url=url, status=resp.status)
            return await resp.read()

    async def post_json(
        self,
        url: str,
        json_body: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """POST JSON 并解析响应"""
        merged = {**self._headers, **(headers or {})}
        async with await self.request("POST", url, json=json_body, headers=merged) as resp:
            if resp.status not in (200, 201, 204):
                text = await resp.text()
                raise ApiError(f"HTTP {resp.status}: {text[:200]}", url=url, status=resp.status)
            if resp.status == 204:
                return None
            try:
                return await resp.json(content_type=None)
            except ValueError:
                return None

    async def download_to(self, url: str, dest: Path) -> int:
        """简单的流式落盘（复杂场景请使用 AsyncDownloader）"""
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with await self.request("GET", url) as resp:
            if resp.status != 200:
                raise ApiError(f"HTTP {resp.status}", url=url, status=resp.status)
            written = 0
            with dest.open("wb") as fh:
                async for chunk in resp.content.iter_chunked(64 * 1024):
                    fh.write(chunk)
                    written += len(chunk)
            return written


__all__ = ["ApiClient", "ApiError", "DEFAULT_UA"]
