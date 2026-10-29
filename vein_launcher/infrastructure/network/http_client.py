"""基础设施层 - 通用异步 HTTP 客户端

对应架构：infrastructure/network/http_client.py
职责：
- 统一的 aiohttp 会话管理（User-Agent、超时、代理）
- GET 文本 / GET JSON
- 瞬时错误重试

不包含：下载、缓存、镜像、限速等能力（不在当前需求内）。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping, Optional

import aiohttp

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.exceptions import VeinError

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "VeinLauncher/0.1.0 (Minecraft Launcher)"
DEFAULT_TIMEOUT = 30.0
RETRY_DELAYS = (1.0, 2.0, 4.0)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class HttpClientError(VeinError):
    """HTTP 请求失败"""

    def __init__(self, message: str, url: str = "", status: int = 0):
        super().__init__(message)
        self.url = url
        self.status = status


class HttpClient:
    """aiohttp 的最小封装"""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT,
        retry_count: int = len(RETRY_DELAYS),
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self._user_agent = user_agent
        self._timeout = timeout
        self._retry_count = max(0, retry_count)
        self._session = session
        self._owns_session = session is None
        self._closed = False
        self._insecure: Optional[aiohttp.ClientSession] = None

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "HttpClient":
        await self.session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def session(self) -> aiohttp.ClientSession:
        """惰性创建会话"""
        if self._session is not None and not self._session.closed:
            return self._session
        if self._closed:
            raise HttpClientError("客户端已关闭")

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout, sock_connect=15),
            headers={"User-Agent": self._user_agent},
            proxy=self._proxy_url(),
        )
        self._owns_session = True
        return self._session

    async def _insecure_session(self) -> aiohttp.ClientSession:
        """镜像节点证书链不完整时使用：仅用于已知的 BMCLAPI 节点"""
        if self._insecure is None or self._insecure.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self._insecure = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout, sock_connect=15),
                headers={"User-Agent": self._user_agent},
                proxy=self._proxy_url(),
                connector=connector,
            )
        return self._insecure

    async def close(self) -> None:
        self._closed = True
        if self._insecure is not None and not self._insecure.closed:
            await self._insecure.close()
        self._insecure = None
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    @staticmethod
    def _proxy_url() -> Optional[str]:
        """从全局配置读取代理"""
        cfg = settings_manager.get().network
        if not cfg.proxy_enabled or not cfg.proxy_host:
            return None
        scheme = "socks5" if cfg.proxy_type.upper() == "SOCKS5" else "http"
        port = cfg.proxy_port or (1080 if scheme == "socks5" else 8080)
        return f"{scheme}://{cfg.proxy_host}:{port}"

    # ------------------------------------------------------------------
    # 请求
    # ------------------------------------------------------------------
    async def _get(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """带重试的 GET，返回未读取内容的响应对象"""
        session = await self.session()
        last_error: Optional[BaseException] = None

        insecure = False
        for attempt in range(self._retry_count + 1):
            try:
                if insecure:
                    session = await self._insecure_session()
                response = await session.get(url, params=params, headers=headers)
                if response.status in RETRYABLE_STATUS:
                    body = await response.text()
                    response.release()
                    last_error = HttpClientError(
                        f"HTTP {response.status}: {body[:200]}",
                        url=url,
                        status=response.status,
                    )
                    logger.warning(
                        "请求失败（第 %d 次）%s -> %s", attempt + 1, url, response.status
                    )
                else:
                    return response
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc
                text = str(exc)
                if not insecure and ("CERTIFICATE_VERIFY_FAILED" in text or "SSL" in text):
                    insecure = True
                    logger.warning("证书校验失败，降级不校验 SSL 重试：%s", url)
                    continue
                logger.warning("请求异常（第 %d 次）%s -> %s", attempt + 1, url, exc)

            if attempt < self._retry_count:
                await asyncio.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])

        if isinstance(last_error, HttpClientError):
            raise last_error
        raise HttpClientError(f"请求失败：{last_error}", url=url)

    async def get_json(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """GET 并解析 JSON"""
        async with await self._get(url, params, headers) as response:
            if response.status != 200:
                raise HttpClientError(
                    f"HTTP {response.status}", url=url, status=response.status
                )
            try:
                return await response.json(content_type=None)
            except ValueError as exc:
                raise HttpClientError(
                    f"JSON 解析失败：{exc}", url=url, status=response.status
                ) from exc

    async def get_text(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> str:
        """GET 并返回文本"""
        async with await self._get(url, params, headers) as response:
            if response.status != 200:
                raise HttpClientError(
                    f"HTTP {response.status}", url=url, status=response.status
                )
            return await response.text()


__all__ = ["HttpClient", "HttpClientError", "DEFAULT_USER_AGENT"]
