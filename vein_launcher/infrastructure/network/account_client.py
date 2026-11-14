"""Vein 账户 API 客户端（account.zhanjhn.cn）。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

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

    async def register(self, device_key: str, name: str, inventory: dict, session: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/client/register",
                                   json={"device_key": device_key, "name": name, "inventory": inventory},
                                   session=session)

    async def heartbeat(self, device_key: str, inventory: dict, session: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/client/heartbeat",
                                   json={"device_key": device_key, "inventory": inventory},
                                   session=session)

    async def commands(self, device_key: str, session: str) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/api/client/commands",
                                   params={"device_key": device_key}, session=session)
        return list(data.get("items") or [])

    async def rooms(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/api/rooms")
        return list(data.get("items") or [])

    async def create_room(self, session: str, name: str, version: str, host: str,
                          password: str = "", public: bool = True, max_players: int = 8) -> Dict[str, Any]:
        return await self._request("POST", "/api/rooms", session=session, json={
            "name": name, "version": version, "host": host,
            "password": password, "public": public, "max_players": max_players,
        })

    async def join_room(self, session: str, room_no: str, password: str = "") -> Dict[str, Any]:
        return await self._request("POST", f"/api/rooms/{room_no}/join", session=session, json={"password": password})

    async def close_room(self, session: str, room_no: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/rooms/{room_no}/close", session=session, json={})

    async def result(self, command_id: int, ok: bool, result: dict, session: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/client/result",
                                   json={"id": command_id, "ok": ok, "result": result},
                                   session=session)


__all__ = ["AccountClient", "AccountError"]
