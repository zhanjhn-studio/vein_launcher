"""Vein 账户 API 客户端（account.zhanjhn.cn）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp

BASE = "https://account.zhanjhn.cn"
TIMEOUT = aiohttp.ClientTimeout(total=20, connect=8)


class AccountError(RuntimeError):
    pass


class AccountClient:
    def __init__(self, base: str = BASE) -> None:
        self._base = base.rstrip("/")

    async def _request(self, method: str, path: str, *, json: Optional[dict] = None,
                       params: Optional[dict] = None, session: str = "") -> Any:
        headers = {"Accept": "application/json"}
        if session:
            headers["Authorization"] = f"Bearer {session}"
        try:
            async with aiohttp.ClientSession(timeout=TIMEOUT) as http:
                async with http.request(method, f"{self._base}{path}", json=json,
                                        params=params, headers=headers) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        raise AccountError(f"HTTP {resp.status}")
                    if resp.status >= 400:
                        message = ""
                        if isinstance(data, dict):
                            message = (data.get("error") or {}).get("message") or ""
                        raise AccountError(message or f"HTTP {resp.status}")
                    return data
        except aiohttp.ClientError as exc:
            raise AccountError(f"无法连接账户服务：{exc}") from exc
        except TimeoutError as exc:
            raise AccountError("账户服务超时") from exc

    async def start(self, token: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/device/start", json={"token": token})

    async def poll(self, token: str) -> Dict[str, Any]:
        return await self._request("GET", "/api/device/poll", params={"token": token})

    async def me(self, session: str) -> Dict[str, Any]:
        return await self._request("GET", "/api/me", session=session)

    async def logout(self, session: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/logout", json={}, session=session)


__all__ = ["AccountClient", "AccountError"]
