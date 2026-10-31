"""更新系统离线测试（版本比较 / zip 解包）"""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from vein_launcher.application.services.update_service import (
    UpdateService,
    is_newer,
    parse_version,
)


class VersionCompareTests(unittest.TestCase):
    def test_parse(self) -> None:
        self.assertEqual(parse_version("v0.1.0"), (0, 1, 0))
        self.assertEqual(parse_version("0.1.0-beta"), (0, 1, 0))
        self.assertEqual(parse_version("1.20.1"), (1, 20, 1))
        self.assertEqual(parse_version(""), (0, 0, 0))

    def test_newer(self) -> None:
        self.assertTrue(is_newer("0.1.0", "0.0.3"))
        self.assertTrue(is_newer("1.0.0", "0.9.9"))
        self.assertFalse(is_newer("0.0.3", "0.0.3"))
        self.assertFalse(is_newer("0.0.2", "0.0.3"))


class InstallTests(unittest.TestCase):
    def test_zip_is_extracted(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        archive = root / "VeinLauncher-0.1.0.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("VeinLauncher/VeinLauncher.exe", b"MZ")
            zf.writestr("README.txt", "hello")

        service = UpdateService("0.0.3")
        service._dir = root / "update"  # type: ignore[attr-defined]
        result = service.install(str(archive))

        self.assertTrue(result["started"])
        self.assertEqual(result["kind"], "zip")
        extracted = Path(result["path"])
        self.assertTrue((extracted / "README.txt").is_file())
        self.assertTrue((extracted / "VeinLauncher" / "VeinLauncher.exe").is_file())

    def test_unknown_file_not_started(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "notes.txt"
        path.write_text("x", encoding="utf-8")
        service = UpdateService("0.0.3")
        service._dir = Path(tmp.name) / "update"  # type: ignore[attr-defined]
        result = service.install(str(path))
        self.assertFalse(result["started"])


if __name__ == "__main__":
    unittest.main()
