"""账号 / 正版令牌 / 启动参数注入的离线单元测试

不访问网络：所有微软认证步骤都用假实现替换。
运行：python -m unittest discover -s tests -v
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from vein_launcher.application.services.account_service import AccountService
from vein_launcher.application.services.launcher_service import LauncherService
from vein_launcher.domain.models.account import (
    MicrosoftAccount,
    OfflineAccount,
    token_needs_refresh,
)
from vein_launcher.infrastructure.network import microsoft_auth as ma
from vein_launcher.presentation.bridge import ApiBridge


def _profile(token: str = "mc-token-1", expires_in: int = 86400) -> dict:
    return {
        "username": "Steve",
        "uuid": "069a79f444e94726a5befca90e38aaf5",
        "access_token": token,
        "refresh_token": "refresh-1",
        "expires_in": expires_in,
        "ms_expires_in": 3600,
        "type": "microsoft",
    }


class AccountServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "accounts.json"
        self.service = AccountService(path=self.path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_offline_round_trip(self) -> None:
        created = self.service.add_offline("Alex")
        self.assertEqual(created["type"], "offline")
        rows = self.service.list()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["selected"])
        self.assertEqual(rows[0]["type"], "offline")
        self.assertFalse(rows[0]["online"])

        reloaded = AccountService(path=self.path).load()
        self.assertEqual(len(reloaded.accounts), 1)
        self.assertIsInstance(reloaded.accounts[0], OfflineAccount)
        self.assertEqual(reloaded.get_selected_account().username, "Alex")

    def test_microsoft_account_persists_token(self) -> None:
        result = self.service.add_microsoft(_profile())
        self.assertEqual(result["type"], "microsoft")

        rows = self.service.list()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "microsoft")
        self.assertTrue(rows[0]["online"])
        self.assertEqual(rows[0]["uuid"], "069a79f444e94726a5befca90e38aaf5")
        self.assertIsNotNone(rows[0]["expires_at"])

        # 重新加载后仍是微软账号，令牌没有丢失
        reloaded = AccountService(path=self.path).load()
        account = reloaded.get_selected_account()
        self.assertIsInstance(account, MicrosoftAccount)
        self.assertEqual(account.mc_access_token, "mc-token-1")
        self.assertEqual(account.refresh_token, "refresh-1")
        self.assertEqual(account.account_type, "microsoft")

    def test_microsoft_login_dedupes_by_uuid(self) -> None:
        self.service.add_microsoft(_profile())
        updated = _profile(token="mc-token-2")
        updated["username"] = "SteveRenamed"
        self.service.add_microsoft(updated)
        rows = self.service.list()
        self.assertEqual(len(rows), 1, "同一 Minecraft 档案不应重复创建账号")
        self.assertEqual(rows[0]["username"], "SteveRenamed")

    def test_two_microsoft_accounts_keep_separate_tokens(self) -> None:
        self.service.add_microsoft(_profile())
        second = _profile(token="mc-token-other")
        second["uuid"] = "11111111222233334444555555555555"
        second["username"] = "Herobrine"
        self.service.add_microsoft(second)

        reloaded = AccountService(path=self.path).load()
        tokens = {a.username: a.mc_access_token for a in reloaded.accounts}
        self.assertEqual(tokens["Steve"], "mc-token-1")
        self.assertEqual(tokens["Herobrine"], "mc-token-other")

    def test_update_ms_session_refreshes_token(self) -> None:
        account_id = self.service.add_microsoft(_profile())["id"]
        session = {
            "access_token": "mc-token-fresh",
            "refresh_token": "refresh-2",
            "expires_in": 86400,
            "username": "Steve",
            "uuid": "069a79f444e94726a5befca90e38aaf5",
        }
        self.assertTrue(self.service.update_ms_session(account_id, session))

        reloaded = AccountService(path=self.path)
        reloaded.load()
        account = reloaded.get(account_id)
        self.assertEqual(account.mc_access_token, "mc-token-fresh")
        self.assertEqual(account.refresh_token, "refresh-2")

    def test_missing_type_defaults_to_offline(self) -> None:
        legacy = {
            "selected": "a1",
            "accounts": [
                {"account_id": "a1", "username": "OldTimer", "selected": False}
            ],
        }
        self.path.write_text(json.dumps(legacy), encoding="utf-8")
        service = AccountService(path=self.path)
        manager = service.load()
        self.assertIsInstance(manager.accounts[0], OfflineAccount)


class TokenExpiryTests(unittest.TestCase):
    def test_token_needs_refresh(self) -> None:
        now = 1_000_000
        self.assertTrue(token_needs_refresh(None, now))
        self.assertTrue(token_needs_refresh(0, now))
        self.assertTrue(token_needs_refresh(now + 60, now), "5 分钟内到期应续期")
        self.assertTrue(token_needs_refresh(now + 600, now))
        self.assertFalse(token_needs_refresh(now + 3600, now))
        self.assertFalse(token_needs_refresh(now + 86400, now))


class RefreshSessionTests(unittest.TestCase):
    def test_refresh_session_builds_mc_session(self) -> None:
        async def fake_refresh(client_id: str, refresh_token: str) -> dict:
            self.assertEqual(client_id, "cid")
            self.assertEqual(refresh_token, "refresh-1")
            return {"access_token": "ms-new", "refresh_token": "refresh-2", "expires_in": 3600}

        async def fake_xbl(token: str) -> dict:
            self.assertEqual(token, "ms-new")
            return {"Token": "xbl-token"}

        async def fake_xsts(token: str) -> dict:
            return {
                "Token": "xsts-token",
                "DisplayClaims": {"xui": [{"uhs": "user-hash"}]},
            }

        async def fake_mc(xsts: dict) -> tuple:
            return "mc-fresh", 86400

        async def fake_profile(token: str) -> dict:
            self.assertEqual(token, "mc-fresh")
            return {"name": "Steve", "id": "069a79f444e94726a5befca90e38aaf5"}

        with patch.multiple(
            ma,
            refresh_ms_token=fake_refresh,
            _xbox_token=fake_xbl,
            _xsts_token=fake_xsts,
            _minecraft_token=fake_mc,
            profile=fake_profile,
        ):
            session = asyncio.run(ma.refresh_session("cid", "refresh-1"))

        self.assertEqual(session["access_token"], "mc-fresh")
        self.assertEqual(session["refresh_token"], "refresh-2", "续期后应保留新 refresh token")
        self.assertEqual(session["expires_in"], 86400)
        self.assertEqual(session["username"], "Steve")
        self.assertEqual(session["type"], "microsoft")


class MsEnsureTokenTests(unittest.TestCase):
    """直接测试 ApiBridge._ms_ensure_token：过期续期 / 续期失败回退 / 未过期不刷新"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.service = AccountService(path=Path(self._tmp.name) / "accounts.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @staticmethod
    def _fake_bridge(service, client_id: str = "cid"):
        class _Fake:
            pass

        fake = _Fake()
        fake._ctx = SimpleNamespace(accounts=service)
        fake._ms_read_client_id = lambda: client_id
        fake._ms_apply_authority = lambda: "consumers"
        return fake

    def test_refreshes_expired_token(self) -> None:
        account_id = self.service.add_microsoft(_profile(token="old-token", expires_in=-10))["id"]
        account = self.service.get(account_id)
        calls = {}

        async def fake_refresh(client_id: str, refresh_token: str) -> dict:
            calls["refresh"] = (client_id, refresh_token)
            return {
                "access_token": "new-token",
                "uuid": account.uuid,
                "refresh_token": "refresh-2",
                "expires_in": 86400,
                "username": "Steve",
            }

        with patch.object(ma, "refresh_session", fake_refresh):
            token = asyncio.run(
                ApiBridge._ms_ensure_token(self._fake_bridge(self.service), account)
            )

        self.assertEqual(token["access_token"], "new-token")
        self.assertEqual(calls["refresh"], ("cid", "refresh-1"))
        stored = self.service.get(account_id)
        self.assertEqual(stored.mc_access_token, "new-token")
        self.assertEqual(stored.refresh_token, "refresh-2")
        self.assertGreater(stored.mc_expires_at, int(__import__("time").time()) + 86000)

    def test_falls_back_to_cached_token_when_refresh_fails(self) -> None:
        account_id = self.service.add_microsoft(_profile(token="old-token", expires_in=-10))["id"]
        account = self.service.get(account_id)

        async def broken_refresh(client_id: str, refresh_token: str) -> dict:
            raise RuntimeError("invalidate")

        with patch.object(ma, "refresh_session", broken_refresh):
            token = asyncio.run(
                ApiBridge._ms_ensure_token(self._fake_bridge(self.service), account)
            )

        self.assertEqual(token["access_token"], "old-token", "续期失败应退回现有令牌")

    def test_does_not_refresh_fresh_token(self) -> None:
        account_id = self.service.add_microsoft(_profile(token="fresh-token", expires_in=3600))["id"]
        account = self.service.get(account_id)

        async def must_not_call(client_id: str, refresh_token: str) -> dict:
            raise AssertionError("令牌未过期时不应触发续期")

        with patch.object(ma, "refresh_session", must_not_call):
            token = asyncio.run(
                ApiBridge._ms_ensure_token(self._fake_bridge(self.service), account)
            )

        self.assertEqual(token["access_token"], "fresh-token")


class LaunchArgTests(unittest.TestCase):
    def test_token_reaches_command_line(self) -> None:
        args = [
            "--username", "${auth_player_name}",
            "--uuid", "${auth_uuid}",
            "--accessToken", "${auth_access_token}",
            "--userType", "${user_type}",
            "--versionType", "${version_type}",
        ]
        repl = {
            "auth_player_name": "Steve",
            "auth_uuid": "069a79f444e94726a5befca90e38aaf5",
            "auth_access_token": "mc-token-1",
            "user_type": "msa",
            "version_type": "release",
        }
        out = LauncherService._render(args, repl)
        self.assertEqual(out[out.index("--accessToken") + 1], "mc-token-1")
        self.assertEqual(out[out.index("--userType") + 1], "msa")
        self.assertEqual(out[out.index("--uuid") + 1], "069a79f444e94726a5befca90e38aaf5")
        self.assertIn("--username", out)

    def test_offline_defaults(self) -> None:
        repl = {"auth_access_token": "0", "user_type": "legacy"}
        out = LauncherService._render(
            ["--accessToken", "${auth_access_token}", "--userType", "${user_type}"], repl
        )
        self.assertEqual(out, ["--accessToken", "0", "--userType", "legacy"])

    def test_unresolved_placeholder_dropped(self) -> None:
        out = LauncherService._render(["--quickPlaySingleplayer", "${quickPlayPath}"], {})
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
