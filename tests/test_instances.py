"""实例内容管理测试（模组启停 / 删除 / 目录列表）"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vein_launcher.application.services.instance_service import InstanceError, InstanceService

VERSION = "1.20.1"


class InstanceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.version_dir = self.root / "versions" / VERSION
        for folder in ("mods", "resourcepacks", "shaderpacks", "datapacks", "modpacks", "saves"):
            (self.version_dir / folder).mkdir(parents=True)
        (self.version_dir / "mods" / "sodium.jar").write_bytes(b"x" * 1024)
        (self.version_dir / "mods" / "old.jar.disabled").write_bytes(b"y" * 512)
        self.service = InstanceService()
        self._patcher = patch(
            "vein_launcher.application.services.instance_service.resolve_version_dir",
            side_effect=lambda vid: self.version_dir,
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        self._tmp.cleanup()

    def test_list_contents_marks_disabled(self) -> None:
        data = self.service.list_contents(VERSION)
        mods = {item["name"]: item for item in data["mod"]}
        self.assertIn("sodium.jar", mods)
        self.assertTrue(mods["sodium.jar"]["enabled"])
        self.assertIn("old.jar", mods)
        self.assertFalse(mods["old.jar"]["enabled"])

    def test_disable_and_enable_mod(self) -> None:
        self.service.set_enabled(VERSION, "mod", "sodium.jar", False)
        self.assertTrue((self.version_dir / "mods" / "sodium.jar.disabled").is_file())
        self.assertFalse((self.version_dir / "mods" / "sodium.jar").exists())

        self.service.set_enabled(VERSION, "mod", "sodium.jar", True)
        self.assertTrue((self.version_dir / "mods" / "sodium.jar").is_file())
        self.assertFalse((self.version_dir / "mods" / "sodium.jar.disabled").exists())

    def test_delete_mod_file(self) -> None:
        self.service.delete(VERSION, "mod", "sodium.jar")
        self.assertFalse((self.version_dir / "mods" / "sodium.jar").exists())

    def test_reject_path_traversal(self) -> None:
        with self.assertRaises(InstanceError):
            self.service.set_enabled(VERSION, "mod", "../evil.jar", False)
        with self.assertRaises(InstanceError):
            self.service.delete(VERSION, "mod", "..")

    def test_unknown_kind_rejected(self) -> None:
        with self.assertRaises(InstanceError):
            self.service.list_contents(VERSION)
            self.service.delete(VERSION, "nope", "x.jar")

    def test_missing_version_raises(self) -> None:
        with patch(
            "vein_launcher.application.services.instance_service.resolve_version_dir",
            side_effect=lambda vid: self.root / "missing",
        ):
            with self.assertRaises(InstanceError):
                self.service.list_contents(VERSION)


if __name__ == "__main__":
    unittest.main()
