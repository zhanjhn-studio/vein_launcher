"""插件权限与沙箱测试（不需要 Node.js）"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vein_launcher.infrastructure.plugin_host.capabilities import (
    CapabilityNotFoundError,
    CapabilityRegistry,
    PluginPermissionError,
)


async def _echo(value: str) -> str:
    return value


class CapabilityRegistryTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="vein_cap_"))
        self.sandbox = self.root / "sandbox"
        self.sandbox.mkdir()
        self.registry = CapabilityRegistry(allowed_roots=[self.sandbox])
        self.registry.register("file.readText", "file.read", _echo, "读文件")

    async def test_permitted_call(self):
        result = await self.registry.execute("demo", ["file.read"], "file.readText", ["x"])
        self.assertEqual(result, "x")

    async def test_permission_denied(self):
        with self.assertRaises(PluginPermissionError):
            await self.registry.execute("demo", [], "file.readText", ["x"])

    async def test_unknown_capability(self):
        with self.assertRaises(CapabilityNotFoundError):
            await self.registry.execute("demo", ["file.read"], "nope", [])

    async def test_path_inside_sandbox(self):
        target = self.sandbox / "a.txt"
        self.assertEqual(self.registry.check_path(str(target)), target.resolve())

    async def test_path_escape_blocked(self):
        with self.assertRaises(PluginPermissionError):
            self.registry.check_path(r"C:\Windows\win.ini")

    async def test_relative_path_anchored(self):
        resolved = self.registry.check_path("data/file.txt")
        self.assertTrue(str(resolved).startswith(str(self.sandbox.resolve())))


if __name__ == "__main__":
    unittest.main()
