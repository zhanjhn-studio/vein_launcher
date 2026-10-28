"""启动命令构建测试（不联网、不需要 Java）"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from vein_launcher.application.services.launcher_service import (
    LauncherService,
    LaunchOptions,
)
from vein_launcher.infrastructure.process.java_detector import JavaInstallation

FAKE_MERGED = {
    "id": "1.20.4",
    "type": "release",
    "mainClass": "net.minecraft.client.main.Main",
    "assets": "12",
    "assetIndex": {"id": "12", "url": "http://example.invalid/12.json"},
    "javaVersion": {"majorVersion": 17},
    "libraries": [],
    "arguments": {
        "jvm": [
            {"rules": [{"action": "allow", "os": {"name": "windows"}}],
             "value": ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]},
        ],
        "game": [
            "--username", "${auth_player_name}",
            "--version", "${version_name}",
            "--gameDir", "${game_directory}",
            "--assetsDir", "${assets_root}",
            "--assetIndex", "${assets_index_name}",
            "--uuid", "${auth_uuid}",
            "--accessToken", "${auth_access_token}",
            "--userType", "${user_type}",
        ],
    },
}


class _FakeVersionService:
    async def fetch_merged(self, version_id: str):
        return FAKE_MERGED

    def list_installed_versions(self):
        return []


class LauncherCommandTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = LauncherService(_FakeVersionService())  # type: ignore[arg-type]
        self.java = JavaInstallation(
            path=Path(sys.executable), major=17, full_version="17.0.9",
            vendor="Test", arch="64",
        )

    async def test_main_class_and_single_classpath(self):
        cmd = await self.service.build_command(
            LaunchOptions(version_id="1.20.4", username="Steve"), java=self.java
        )
        self.assertIn("net.minecraft.client.main.Main", cmd)
        self.assertEqual(cmd.count("-cp"), 1, "不应重复注入 -cp")

    async def test_placeholders_replaced(self):
        cmd = await self.service.build_command(
            LaunchOptions(
                version_id="1.20.4", username="Alex", uuid="abc123", access_token="tok",
            ),
            java=self.java,
        )
        joined = " ".join(cmd)
        self.assertIn("--username Alex", joined)
        self.assertIn("--uuid abc123", joined)
        self.assertIn("--accessToken tok", joined)
        self.assertNotIn("${", joined, "存在未替换的占位符")

    async def test_memory_flags(self):
        cmd = await self.service.build_command(
            LaunchOptions(version_id="1.20.4", memory_min=1024, memory_max=8192),
            java=self.java,
        )
        self.assertIn("-Xms1024M", cmd)
        self.assertIn("-Xmx8192M", cmd)

    async def test_offline_uuid_stable(self):
        first = LauncherService.offline_uuid("Steve")
        second = LauncherService.offline_uuid("Steve")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 36)
        self.assertNotEqual(first, LauncherService.offline_uuid("Alex"))

    async def test_rules_filter_linux_only_args(self):
        merged = dict(FAKE_MERGED)
        merged["arguments"] = {
            "jvm": [],
            "game": [
                {"rules": [{"action": "allow", "os": {"name": "linux"}}],
                 "value": "--linux-only"},
                "--keep-me",
            ],
        }
        self.service._versions.fetch_merged = lambda vid: _async(merged)  # type: ignore
        cmd = await self.service.build_command(
            LaunchOptions(version_id="1.20.4"), java=self.java
        )
        self.assertIn("--keep-me", cmd)
        self.assertNotIn("--linux-only", cmd)


async def _async(value):
    return value


if __name__ == "__main__":
    unittest.main()
