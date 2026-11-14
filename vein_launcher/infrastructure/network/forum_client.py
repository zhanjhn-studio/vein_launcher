"""Vein 广场（api.zhanjhn.cn）的 HTTP 客户端。

启动器通过后端代发请求，避开 WebView 的 CORS / file:// 限制。
"""

from __future__ import annotations

import hashlib
import socket
from typing import Any, Dict, List, Optional

import aiohttp

BASE = "https://api.zhanjhn.cn"
TIMEOUT = aiohttp.ClientTimeout(total=20, connect=8)


class ForumError(RuntimeError):
    pass


def _device_user_key() -> str:
    try:
        seed = f"{socket.gethostname()}|{socket.gethostbyname(socket.gethostname())}"
    except OSError:
        seed = socket.gethostname()
    return "pc-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


USER_KEY = _device_user_key()


class ForumClient:
    """只读 + 发帖 + 点赞；无登录，作者名由用户填写。"""

    def __init__(self, base: str = BASE) -> None:
        self._base = base.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self._base}{path}"
        hdrs = {"Accept": "application/json", "X-User": USER_KEY}
        if headers:
            hdrs.update(headers)
        try:
            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                async with session.request(method, url, params=params, json=json, headers=hdrs) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        text = await resp.text()
                        raise ForumError(f"HTTP {resp.status}: {text[:200]}")
                    if resp.status >= 400:
                        message = ""
                        if isinstance(data, dict):
                            message = (data.get("error") or {}).get("message") or ""
                        raise ForumError(message or f"HTTP {resp.status}")
                    return data
        except aiohttp.ClientError as exc:
            raise ForumError(f"无法连接广场服务：{exc}") from exc
        except TimeoutError as exc:
            raise ForumError("广场服务超时") from exc

    async def feed(self, sort: str = "hot", tag: str = "", page: int = 1, limit: int = 20) -> Dict[str, Any]:
        params: Dict[str, Any] = {"sort": sort, "page": max(1, int(page)), "limit": min(50, max(1, limit))}
        if tag:
            params["tag"] = tag
        return await self._request("GET", "/api/posts", params=params)

    async def tags(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/api/tags")
        return list(data.get("items") or [])

    async def detail(self, post_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"/api/posts/{int(post_id)}")

    async def create(
        self, title: str, content: str, tags: List[str], author: str, session: str = ""
    ) -> Dict[str, Any]:
        headers = {"X-Author": author}
        if session:
            headers["Authorization"] = f"Bearer {session}"
        return await self._request(
            "POST",
            "/api/posts",
            json={"title": title, "content": content, "tags": tags, "author": author},
            headers=headers,
        )

    async def like(self, post_id: int) -> Dict[str, Any]:
        return await self._request("POST", f"/api/posts/{int(post_id)}/like", json={})

    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/health")


__all__ = ["ForumClient", "ForumError", "USER_KEY"]
