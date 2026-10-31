"""LittleSkin / 通用 Yggdrasil 皮肤站登录

LittleSkin 使用 Yggdrasil 协议提供认证与皮肤：
    https://littleskin.cn/api/yggdrasil

登录成功返回 accessToken / clientToken / selectedProfile，启动游戏时需要
authlib-injector 注入同样的 API 地址，客户端与服务器才能校验身份并加载皮肤。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_SERVER = "https://littleskin.cn/api/yggdrasil"
TIMEOUT = 20
AGENT = {"name": "Minecraft", "version": 1}


class LittleSkinError(RuntimeError):
    pass


def _normalize(server: str) -> str:
    server = (server or DEFAULT_SERVER).strip().rstrip("/")
    if not server:
        server = DEFAULT_SERVER
    return server


async def _post(url: str, payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        async with session.post(url, json=payload) as resp:
            try:
                data = await resp.json(content_type=None)
            except Exception:
                data = {}
            logger.info("LittleSkin %s -> HTTP %s", url.rsplit("/", 1)[-1], resp.status)
            return resp.status, data if isinstance(data, dict) else {}


def _error(status: int, data: Dict[str, Any], action: str) -> LittleSkinError:
    code = str(data.get("error") or "")
    message = str(data.get("errorMessage") or "").strip()
    if code == "ForbiddenOperationException":
        # LittleSkin 对密码错误和令牌失效都返回 403 + ForbiddenOperationException
        hint = "邮箱或密码不正确" if "登录" in action else "登录状态已失效，请重新登录"
    elif code == "IllegalArgumentException":
        hint = message or "请求参数不合法"
    elif status == 401:
        hint = "邮箱或密码不正确"
    elif status == 403:
        hint = "账号被限制，或需要在 LittleSkin 网页完成验证"
    elif status == 400:
        hint = message or "请求参数不合法"
    elif status >= 500:
        hint = "LittleSkin 服务暂时不可用，稍后再试"
    else:
        hint = message or f"HTTP {status}"
    return LittleSkinError(f"{action}失败：{hint}")


def parse_session(server: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """把 Yggdrasil authenticate 响应整理成账号字段（纯函数，便于测试）"""
    profile = data.get("selectedProfile") or {}
    if not profile:
        profiles = data.get("availableProfiles") or []
        profile = profiles[0] if profiles else {}
    uuid = str(profile.get("id") or "")
    username = str(profile.get("name") or data.get("username") or "Player")
    return {
        "server": _normalize(server),
        "username": username,
        "uuid": uuid.replace("-", ""),
        "access_token": str(data.get("accessToken") or ""),
        "client_token": str(data.get("clientToken") or ""),
        "skin_model": str(profile.get("skinModel") or ""),
        "type": "littleskin",
    }


async def authenticate(
    server: str, username: str, password: str, client_token: str = ""
) -> Dict[str, Any]:
    """邮箱 + 密码登录（Yggdrasil authenticate）"""
    server = _normalize(server)
    if not username.strip() or not password:
        raise LittleSkinError("请填写 LittleSkin 邮箱和密码")
    status, data = await _post(
        f"{server}/authserver/authenticate",
        {
            "username": username.strip(),
            "password": password,
            "clientToken": client_token,
            "agent": AGENT,
            "requestUser": True,
        },
    )
    if status != 200:
        raise _error(status, data, "LittleSkin 登录")
    session = parse_session(server, data)
    if not session["access_token"]:
        raise LittleSkinError("LittleSkin 返回的数据缺少 accessToken")
    if not session["uuid"]:
        raise LittleSkinError("该账号还没有创建 Minecraft 角色，请先在 LittleSkin 网站创建角色")
    return session


async def refresh(server: str, access_token: str, client_token: str) -> Dict[str, Any]:
    server = _normalize(server)
    status, data = await _post(
        f"{server}/authserver/refresh",
        {"accessToken": access_token, "clientToken": client_token, "requestUser": True},
    )
    if status != 200:
        raise _error(status, data, "LittleSkin 令牌续期")
    data.setdefault("clientToken", client_token)
    return parse_session(server, data)


async def profile(server: str, access_token: str) -> Dict[str, Any]:
    """查询角色档案（含皮肤模型），失败不影响登录结果"""
    server = _normalize(server)
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as session:
            async with session.get(
                f"{server}/minecraft/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            ) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json(content_type=None)
                return data if isinstance(data, dict) else {}
    except Exception as exc:  # 皮肤模型不是必需信息
        logger.info("LittleSkin 档案查询失败：%s", exc)
        return {}


async def profile_by_uuid(server: str, uuid: str) -> Dict[str, Any]:
    """通过 Yggdrasil 查询角色档案（含 textures 属性，可读出当前皮肤）"""
    server = _normalize(server)
    if not uuid:
        return {}
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as session:
            async with session.get(
                f"{server}/sessionserver/session/minecraft/profile/{uuid}"
            ) as resp:
                if resp.status != 200:
                    logger.info("LittleSkin 角色档案查询 HTTP %s", resp.status)
                    return {}
                data = await resp.json(content_type=None)
                return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.info("LittleSkin 角色档案查询失败：%s", exc)
        return {}


def extract_skin(profile: Dict[str, Any]) -> Dict[str, str]:
    """从角色档案的 textures 属性里取出皮肤 URL 与模型（纯函数）"""
    import base64
    import json as _json

    for prop in profile.get("properties") or []:
        if not isinstance(prop, dict) or prop.get("name") != "textures":
            continue
        try:
            payload = _json.loads(base64.b64decode(prop.get("value") or ""))
        except Exception:
            continue
        skin = ((payload.get("textures") or {}).get("SKIN") or {})
        url = str(skin.get("url") or "")
        if url:
            model = str((skin.get("metadata") or {}).get("model") or "classic").lower()
            return {"url": url, "model": "slim" if model == "slim" else "classic"}
    return {}


async def fetch_texture(url: str) -> bytes:
    if not url:
        raise LittleSkinError("皮肤地址为空")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise LittleSkinError(f"下载皮肤失败 HTTP {resp.status}")
            return await resp.read()


__all__ = [
    "DEFAULT_SERVER",
    "LittleSkinError",
    "authenticate",
    "extract_skin",
    "fetch_texture",
    "parse_session",
    "profile",
    "profile_by_uuid",
    "refresh",
]
