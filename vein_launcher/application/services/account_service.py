"""应用层 - 账号服务（离线账号 + 微软设备码登录骨架）"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import AccountError, AuthenticationError
from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir
from vein_launcher.domain.models.account import AccountBase, AccountManager, OfflineAccount

logger = logging.getLogger(__name__)

ACCOUNT_FILE = "accounts.json"


class AccountService:
    """账号增删改查与持久化"""

    def __init__(self, store_path: Optional[Path] = None):
        self._path = store_path or (get_app_data_dir() / ACCOUNT_FILE)
        self._manager = AccountManager()

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def load(self) -> AccountManager:
        if not self._path.is_file():
            return self._manager
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("账号文件损坏，已忽略：%s", exc)
            return self._manager

        accounts: List[AccountBase] = []
        for item in raw.get("accounts", []):
            try:
                if item.get("account_type") == "microsoft":
                    from vein_launcher.domain.models.account import MicrosoftAccount

                    accounts.append(MicrosoftAccount(**item))
                else:
                    accounts.append(OfflineAccount(**item))
            except Exception as exc:  # 单条损坏不影响整体
                logger.warning("跳过损坏账号记录：%s", exc)

        self._manager = AccountManager(
            accounts=accounts, selected_account_id=raw.get("selected")
        )
        return self._manager

    def save(self) -> None:
        ensure_dir(self._path.parent)
        payload = {
            "selected": self._manager.selected_account_id,
            "accounts": [acc.model_dump(mode="json") for acc in self._manager.accounts],
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    @property
    def manager(self) -> AccountManager:
        return self._manager

    def list_accounts(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": acc.account_id,
                "username": acc.username,
                "type": getattr(acc, "account_type", "offline"),
                "selected": acc.account_id == self._manager.selected_account_id,
                "valid": acc.is_valid(),
            }
            for acc in self._manager.accounts
        ]

    def current(self) -> Optional[AccountBase]:
        return self._manager.get_selected_account()

    # ------------------------------------------------------------------
    # 操作
    # ------------------------------------------------------------------
    def add_offline(self, username: str) -> OfflineAccount:
        username = (username or "").strip()
        if not (3 <= len(username) <= 16):
            raise AccountError("用户名长度需在 3~16 个字符之间")
        if any(acc.username.lower() == username.lower() for acc in self._manager.accounts):
            raise AccountError(f"账号已存在：{username}")

        account = OfflineAccount(
            account_id=str(uuid.uuid4()),
            username=username,
        )
        self._manager.add_account(account)
        self.save()
        event_bus.publish(EventNames.ACCOUNT_ADDED, account_id=account.account_id)
        return account

    def remove(self, account_id: str) -> bool:
        ok = self._manager.remove_account(account_id)
        if ok:
            self.save()
            event_bus.publish(EventNames.ACCOUNT_REMOVED, account_id=account_id)
        return ok

    def select(self, account_id: str) -> bool:
        ok = self._manager.select_account(account_id)
        if ok:
            self.save()
            event_bus.publish(EventNames.ACCOUNT_SELECTED, account_id=account_id)
        return ok

    # ------------------------------------------------------------------
    # 微软设备码登录（需要 Azure 应用 client_id）
    # ------------------------------------------------------------------
    async def microsoft_device_login(
        self,
        client_id: str,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """发起设备码流程，返回 {user_code, verification_uri} 后由 UI 展示

        真正的 token 轮询在 `poll_device_token` 中完成。
        """
        if not client_id:
            raise AuthenticationError("未配置微软应用 client_id")

        from vein_launcher.infrastructure.network.api_client import ApiClient, ApiError

        url = f"https://login.microsoftonline.com/consumer/oauth2/v2.0/devicecode"
        try:
            async with ApiClient(retries=1) as api:
                return await api.post_json(
                    url,
                    {"client_id": client_id, "scope": "XboxLive.signin offline_access"},
                )
        except ApiError as exc:
            raise AuthenticationError(f"设备码获取失败：{exc}") from exc

    async def poll_device_token(
        self, client_id: str, device_code: str, timeout: float = 300.0
    ) -> Dict[str, Any]:
        """轮询 token 端点（未完成 Xbox/Minecraft 链路时仅返回 OAuth token）"""
        from vein_launcher.infrastructure.network.api_client import ApiClient, ApiError

        url = "https://login.microsoftonline.com/consumer/oauth2/v2.0/token"
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device_code,
        }
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with ApiClient(retries=0) as api:
                    token = await api.post_json(url, payload)
                event_bus.publish(EventNames.ACCOUNT_LOGIN_SUCCESS)
                return token
            except ApiError:
                await asyncio.sleep(5)
        raise AuthenticationError("设备码登录超时")


__all__ = ["AccountService"]
