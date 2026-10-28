"""应用层 - 账号服务（离线账号）"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import AccountError
from vein_launcher.common.utils.path_utils import get_app_data_dir, ensure_dir
from vein_launcher.domain.models.account import AccountManager, OfflineAccount

logger = logging.getLogger(__name__)

ACCOUNTS_FILE = "accounts.json"


class AccountService:
    """离线账号增删改查（持久化到数据目录）"""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or (get_app_data_dir() / ACCOUNTS_FILE)
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

        accounts = []
        for item in raw.get("accounts", []):
            try:
                accounts.append(OfflineAccount(**item))
            except Exception:
                continue
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
            }
            for acc in self._manager.accounts
        ]

    def current(self):
        return self._manager.get_selected_account()

    def add_offline(self, username: str) -> Dict[str, Any]:
        username = (username or "").strip()
        if not 3 <= len(username) <= 16:
            raise AccountError("用户名长度需在 3–16 个字符之间")
        if any(a.username.lower() == username.lower() for a in self._manager.accounts):
            raise AccountError("账号已存在")

        account = OfflineAccount(account_id=str(uuid.uuid4()), username=username)
        self._manager.add_account(account)
        self.save()
        return {"id": account.account_id, "username": account.username}

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
