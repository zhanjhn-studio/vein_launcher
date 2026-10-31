"""皮肤管理离线测试（PNG 校验 / 存储 / 皮肤站纹理解析）"""

from __future__ import annotations

import base64
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from vein_launcher.application.services.skin_service import (
    SkinError,
    SkinService,
    png_size,
    validate_skin,
)
from vein_launcher.infrastructure.network.littleskin import extract_skin


def make_png(width: int, height: int) -> bytes:
    raw = b"".join(b"\x00" + b"\x00" * (width * 4) for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


class PngTests(unittest.TestCase):
    def test_reads_dimensions(self) -> None:
        self.assertEqual(png_size(make_png(64, 64)), (64, 64))
        self.assertEqual(png_size(make_png(64, 32)), (64, 32))

    def test_rejects_non_png(self) -> None:
        self.assertIsNone(png_size(b"not a png at all"))
        with self.assertRaises(SkinError):
            validate_skin(b"GIF89a")

    def test_rejects_wrong_dimensions(self) -> None:
        with self.assertRaises(SkinError):
            validate_skin(make_png(32, 32))

    def test_accepts_standard_skin(self) -> None:
        self.assertEqual(validate_skin(make_png(64, 64)), (64, 64))


class SkinServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.skins = SkinService(
            root=Path(self._tmp.name) / "skins",
            meta=Path(self._tmp.name) / "skins.json",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_apply_and_read_state(self) -> None:
        state = self.skins.apply_bytes("acc-1", make_png(64, 64), model="slim")
        self.assertTrue(state["has"])
        self.assertEqual(state["model"], "slim")
        self.assertTrue(state["data_url"].startswith("data:image/png;base64,"))
        self.assertEqual(state["size"], [64, 64])

        reloaded = SkinService(root=self.skins.root, meta=self.skins._meta_path)
        again = reloaded.state("acc-1")
        self.assertTrue(again["has"])
        self.assertEqual(again["model"], "slim")

    def test_two_accounts_do_not_share_skin(self) -> None:
        self.skins.apply_bytes("a", make_png(64, 64))
        self.skins.apply_bytes("b", make_png(64, 32), model="classic")
        self.assertEqual(self.skins.state("a")["size"], [64, 64])
        self.assertEqual(self.skins.state("b")["size"], [64, 32])

    def test_clear_removes_file_and_meta(self) -> None:
        self.skins.apply_bytes("acc", make_png(64, 64))
        self.skins.clear("acc")
        self.assertFalse(self.skins.state("acc")["has"])
        self.assertNotIn("acc", self.skins.list())

    def test_import_from_file(self) -> None:
        source = Path(self._tmp.name) / "myskin.png"
        source.write_bytes(make_png(64, 64))
        state = self.skins.apply_file("acc", str(source))
        self.assertTrue(state["has"])
        self.assertEqual(state["source"], "local")

    def test_invalid_model_falls_back_to_classic(self) -> None:
        state = self.skins.apply_bytes("acc", make_png(64, 64), model="weird")
        self.assertEqual(state["model"], "classic")


class ExtractSkinTests(unittest.TestCase):
    def test_reads_skin_url_and_model(self) -> None:
        payload = {
            "textures": {
                "SKIN": {
                    "url": "https://littleskin.cn/textures/abc",
                    "metadata": {"model": "slim"},
                }
            }
        }
        profile = {
            "properties": [
                {"name": "textures", "value": base64.b64encode(json.dumps(payload).encode()).decode()}
            ]
        }
        skin = extract_skin(profile)
        self.assertEqual(skin["url"], "https://littleskin.cn/textures/abc")
        self.assertEqual(skin["model"], "slim")

    def test_missing_textures_returns_empty(self) -> None:
        self.assertEqual(extract_skin({}), {})
        self.assertEqual(extract_skin({"properties": []}), {})


if __name__ == "__main__":
    unittest.main()
