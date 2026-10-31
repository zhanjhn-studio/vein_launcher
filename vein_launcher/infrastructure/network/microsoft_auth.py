"""Microsoft 登录（设备码流程 + Xbox Live + Minecraft 认证链）

说明：设备码流程必须使用一个已注册的 Azure 应用（public client, 允许设备码）。
这里不内置任何客户端 ID，需在 设置 → Accounts → Microsoft app id 中填入你自己的应用 ID。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

AUTHORITY = "common"  # common / consumers / organizations / <tenant-id>
DEVICE_CODE_URL = "https://login.microsoftonline.com/{authority}/oauth2/v2.0/devicecode"
TOKEN_URL = "https://login.microsoftonline.com/{authority}/oauth2/v2.0/token"
XBL_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"

SCOPE = "XboxLive.signin offline_access"


class MinecraftAuthError(RuntimeError):
    pass


async def start_device_code(client_id: str) -> Dict[str, Any]:
    if not client_id:
        raise MinecraftAuthError("未配置 Microsoft 应用 ID（设置 → Accounts）")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post(
            DEVICE_CODE_URL.format(authority=AUTHORITY),
            data={"client_id": client_id, "scope": SCOPE},
        ) as resp:
            data = await resp.json(content_type=None)
            if resp.status != 200:
                raise MinecraftAuthError(data.get("error_description") or f"HTTP {resp.status}")
            return data


async def poll_token(client_id: str, device_code: str, timeout: int = 300) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        while loop.time() < deadline:
            form = {
                "client_id": client_id,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
            }
            async with session.post(
                TOKEN_URL.format(authority=AUTHORITY), data=form
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 200:
                    return data
                error = data.get("error")
                if error == "authorization_pending":
                    await asyncio.sleep(int(data.get("interval", 5)))
                    continue
                if error == "slow_down":
                    await asyncio.sleep(int(data.get("interval", 5)) + 2)
                    continue
                raise MinecraftAuthError(data.get("error_description") or str(error))
    raise MinecraftAuthError("登录超时")


async def _xbox_token(ms_access_token: str) -> Dict[str, Any]:
    payload = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={ms_access_token}",
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post(XBL_URL, json=payload) as resp:
            data = await resp.json(content_type=None)
            logger.info("XBL 步骤: HTTP %s", resp.status)
            if resp.status != 200:
                raise MinecraftAuthError(f"Xbox Live 认证失败: {data}")
            return data


async def _xsts_token(xbl_token: str) -> Dict[str, Any]:
    payload = {
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT",
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post(XSTS_URL, json=payload) as resp:
            data = await resp.json(content_type=None)
            logger.info(
                "XSTS 步骤: HTTP %s uhs=%s",
                resp.status,
                data.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs", "?"),
            )
            if resp.status != 200:
                hint = data.get("XErr")
                raise MinecraftAuthError(f"XSTS 授权失败 (XErr={hint})")
            return data


async def _minecraft_token(xsts: Dict[str, Any]) -> str:
    uhs = xsts["DisplayClaims"]["xui"][0]["uhs"]
    payload = {"identityToken": f"XBL3.0 x={uhs};{xsts['Token']}"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post(MC_LOGIN_URL, json=payload) as resp:
            data = await resp.json(content_type=None)
            logger.info("MC login_with_xbox: HTTP %s body=%s", resp.status, str(data)[:400])
            if resp.status != 200 or "access_token" not in data:
                detail = str(data)[:300]
                raise MinecraftAuthError(
                    f"Minecraft 认证失败 HTTP {resp.status}: {detail}"
                )
            return data["access_token"]


async def profile(mc_access_token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {mc_access_token}"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.get(MC_PROFILE_URL, headers=headers) as resp:
            data = await resp.json(content_type=None)
            logger.info("MC profile: HTTP %s body=%s", resp.status, str(data)[:300])
            if resp.status != 200:
                raise MinecraftAuthError("无法获取 Minecraft 档案（可能未购买游戏）")
            return data


async def login_with_device_code(client_id: str, device_code: str) -> Dict[str, Any]:
    token = await poll_token(client_id, device_code)
    xbl = await _xbox_token(token["access_token"])
    xsts = await _xsts_token(xbl["Token"])
    mc_token = await _minecraft_token(xsts)
    prof = await profile(mc_token)
    return {
        "username": prof.get("name", "Player"),
        "uuid": prof.get("id", ""),
        "access_token": mc_token,
        "refresh_token": token.get("refresh_token", ""),
        "type": "microsoft",
    }
