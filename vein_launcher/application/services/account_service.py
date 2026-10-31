"""应用层 - 账号服务（离线 + 微软正版，令牌按账号隔离）"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import AccountError
from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir
from vein_launcher.domain.models.account import (
    AccountBase,
    AccountManager,
    LittleSkinAccount,
    MicrosoftAccount,
    OfflineAccount,
)

logger = logging.getLogger(__name__)

ACCOUNTS_FILE = "accounts.json"
DEFAULT_MC_TOKEN_TTL = 86400  # Minecraft 会话 token 默认 24 小时


def _build_account(raw: Dict[str, Any]) -> Optional[AccountBase]:
    """按 account_type 还原具体账号模型（兼容旧文件缺字段）"""
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("account_type") or "offline").lower()
    try:
        if kind == "microsoft":
            return MicrosoftAccount(**raw)
        if kind == "littleskin":
            return LittleSkinAccount(**raw)
        return OfflineAccount(**raw)
    except Exception as exc:  # 单条坏数据不应拖垮整个账号列表
        logger.warning("账号记录解析失败（%s）：%s", kind, exc)
        return None


class AccountService:
    """账号增删改查 + 正版令牌持久化（写回数据目录 accounts.json）"""

    def __init__(self, path: Optional[Path] = None):
        self._path = Path(path) if path else (get_app_data_dir() / ACCOUNTS_FILE)
        self._manager = AccountManager()

    # ------------------------------------------------------------------
    def load(self) -> AccountManager:
        if not self._path.is_file():
            return self._manager
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("账号文件读取失败：%s", exc)
            return self._manager

        accounts: List[AccountBase] = []
        for item in raw.get("accounts", []):
            account = _build_account(item)
            if account is not None:
                accounts.append(account)
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
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    def list(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": acc.account_id,
                "username": acc.username,
                "selected": acc.account_id == self._manager.selected_account_id,
                "type": getattr(acc, "account_type", "offline"),
                "uuid": getattr(acc, "uuid", None),
                "online": bool(
                    getattr(acc, "mc_access_token", None)
                    or getattr(acc, "access_token", None)
                ),
                "server": getattr(acc, "server", None),
                "expires_at": getattr(acc, "mc_expires_at", None),
            }
            for acc in self._manager.accounts
        ]

    def current(self):
        return self._manager.get_selected_account()

    def get(self, account_id: str):
        for acc in self._manager.accounts:
            if acc.account_id == account_id:
                return acc
        return None

    def add_offline(self, username: str) -> Dict[str, Any]:
        username = (username or "").strip()
        if not 3 <= len(username) <= 16:
            raise AccountError("用户名长度需在 3–16 个字符之间")
        if any(a.username.lower() == username.lower() for a in self._manager.accounts):
            raise AccountError("账号已存在")

        account = OfflineAccount(account_id=str(uuid.uuid4()), username=username)
        self._manager.add_account(account)
        self.save()
        return {"id": account.account_id, "username": account.username, "type": "offline"}

    # ------------------------------------------------------------------
    def add_microsoft(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """登录成功后写入微软账号：同一 Minecraft 档案只保留一条，令牌随账号存"""
        ms_uuid = str(profile.get("uuid") or "")
        account: Optional[MicrosoftAccount] = None
        for acc in self._manager.accounts:
            if isinstance(acc, MicrosoftAccount) and ms_uuid and acc.uuid == ms_uuid:
                account = acc
                break
        if account is None:
            account = MicrosoftAccount(
                account_id=str(uuid.uuid4()),
                username=str(profile.get("username") or "Player"),
                uuid=ms_uuid,
            )
            self._manager.add_account(account)

        self._apply_session(account, profile)
        self._manager.select_account(account.account_id)
        self.save()
        logger.info("正版账号已保存：%s", account.username)
        return {
            "id": account.account_id,
            "username": account.username,
            "type": "microsoft",
        }

    def add_littleskin(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """LittleSkin 登录成功：同一皮肤站账号按 uuid 去重，令牌随账号保存"""
        server = str(session.get("server") or "")
        ls_uuid = str(session.get("uuid") or "")
        account: Optional[LittleSkinAccount] = None
        for acc in self._manager.accounts:
            if (
                isinstance(acc, LittleSkinAccount)
                and ls_uuid
                and acc.uuid == ls_uuid
                and acc.server == server
            ):
                account = acc
                break
        if account is None:
            account = LittleSkinAccount(
                account_id=str(uuid.uuid4()),
                username=str(session.get("username") or "Player"),
                uuid=ls_uuid,
                server=server,
            )
            self._manager.add_account(account)

        account.username = str(session.get("username") or account.username)
        account.uuid = ls_uuid or account.uuid
        account.server = server or account.server
        if session.get("access_token"):
            account.access_token = str(session["access_token"])
        if session.get("client_token"):
            account.client_token = str(session["client_token"])
        if session.get("skin_model"):
            account.skin_model = str(session["skin_model"])

        self._manager.select_account(account.account_id)
        self.save()
        logger.info("LittleSkin 账号已保存：%s", account.username)
        return {
            "id": account.account_id,
            "username": account.username,
            "type": "littleskin",
        }

    def update_ms_session(self, account_id: str, session: Dict[str, Any]) -> bool:
        """续期成功后回写令牌"""
        account = self.get(account_id)
        if not isinstance(account, MicrosoftAccount):
            return False
        self._apply_session(account, session)
        self.save()
        return True

    @staticmethod
    def _apply_session(account: MicrosoftAccount, session: Dict[str, Any]) -> None:
        now = int(time.time())
        account.username = str(session.get("username") or account.username)
        account.uuid = str(session.get("uuid") or account.uuid or "")
        account.mc_access_token = str(session.get("access_token") or "")
        account.mc_selected_profile = account.uuid.replace("-", "") or None
        account.mc_expires_at = now + int(
            session.get("expires_in") or DEFAULT_MC_TOKEN_TTL
        )
        if session.get("refresh_token"):
            account.refresh_token = str(session["refresh_token"])
        ms_ttl = int(session.get("ms_expires_in") or 0)
        if ms_ttl:
            account.token_expires_at = now + ms_ttl

    # ------------------------------------------------------------------
    def select(self, account_id: str) -> bool:
        ok = self._manager.select_account(account_id)
        if ok:
            self.save()
        return ok

    def remove(self, account_id: str) -> bool:
        ok = self._manager.remove_account(account_id)
        if ok:
            self.save()
        return ok


__all__ = ["AccountService"]
