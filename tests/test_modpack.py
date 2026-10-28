"""整合包（.mrpack）解析与覆盖文件测试"""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from vein_launcher.application.services.modpack_service import ModpackService
from vein_launcher.common.exceptions import DownloadError


def build_pack(directory: Path, files=None, overrides=None) -> Path:
    path = directory / "pack.mrpack"
    index = {
        "formatVersion": 1,
        "name": "Test Pack",
        "versionId": "1.0.0",
        "dependencies": {"minecraft": "1.20.4", "fabric-loader": "0.15.7"},
        "files": files or [],
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("modrinth.index.json", json.dumps(index))
        for name, data in (overrides or {}).items():
            zf.writestr(f"overrides/{name}", data)
    return path


class ModpackReadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vein_pack_"))

    def test_read_index(self):
        path = build_pack(self.tmp)
        info = ModpackService.read_index(path)
        self.assertEqual(info.name, "Test Pack")
        self.assertEqual(info.minecraft_version, "1.20.4")
        self.assertEqual(info.loader, "fabric-loader")

    def test_client_files_filters_server_only(self):
        files = [
            {"path": "mods/a.jar", "downloads": ["https://x/a.jar"], "env": {"client": "required"}},
            {"path": "mods/b.jar", "downloads": ["https://x/b.jar"], "env": {"client": "unsupported"}},
            {"path": "mods/c.jar", "downloads": ["https://x/c.jar"], "env": {}},
            {"path": "mods/d.jar", "downloads": ["https://x/d.jar"]},
        ]
        path = build_pack(self.tmp, files=files)
        info = ModpackService.read_index(path)
        names = [f["path"] for f in info.client_files]
        self.assertIn("mods/a.jar", names)
        self.assertNotIn("mods/b.jar", names)
        self.assertIn("mods/c.jar", names)
        self.assertIn("mods/d.jar", names)

    def test_missing_index_raises(self):
        bad = self.tmp / "bad.mrpack"
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("readme.txt", "not a pack")
        with self.assertRaises(DownloadError):
            ModpackService.read_index(bad)

    def test_not_a_zip_raises(self):
        bad = self.tmp / "nope.mrpack"
        bad.write_text("plain text", encoding="utf-8")
        with self.assertRaises(DownloadError):
            ModpackService.read_index(bad)


class ModpackExtractTest(unittest.IsolatedAsyncioTestCase):
    async def test_extract_overrides(self):
        tmp = Path(tempfile.mkdtemp(prefix="vein_pack2_"))
        pack = build_pack(
            tmp,
            overrides={
                "config/a.toml": "key = 1\n",
                "mods/keep.txt": "x",
            },
        )
        instance = tmp / "instance"
        instance.mkdir()

        count = await ModpackService._extract_overrides(pack, instance)

        self.assertEqual(count, 2)
        self.assertTrue((instance / "config/a.toml").is_file())
        self.assertEqual(
            (instance / "config/a.toml").read_text(encoding="utf-8"), "key = 1\n"
        )
        self.assertTrue((instance / "mods/keep.txt").is_file())


if __name__ == "__main__":
    unittest.main()
