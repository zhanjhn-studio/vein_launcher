"""CurseForge 客户端映射与下载地址回退测试（不联网）"""

from __future__ import annotations

import unittest

from vein_launcher.infrastructure.network.curseforge_api import (
    CLASS_IDS,
    LOADER_TYPES,
    CurseForgeAPI,
)


class CurseForgeMappingTest(unittest.TestCase):
    def test_class_ids_cover_four_types(self):
        self.assertEqual(CLASS_IDS["mod"], 6)
        self.assertEqual(CLASS_IDS["modpack"], 4471)
        self.assertEqual(CLASS_IDS["resourcepack"], 12)
        self.assertEqual(CLASS_IDS["shader"], 6552)
        self.assertNotIn("datapack", CLASS_IDS)

    def test_loader_enum(self):
        self.assertEqual(LOADER_TYPES["forge"], 1)
        self.assertEqual(LOADER_TYPES["fabric"], 4)
        self.assertEqual(LOADER_TYPES["quilt"], 5)
        self.assertEqual(LOADER_TYPES["neoforge"], 6)

    def test_project_type_supported(self):
        self.assertTrue(CurseForgeAPI.project_type_supported("mod"))
        self.assertFalse(CurseForgeAPI.project_type_supported("datapack"))

    def test_download_url_prefers_api_value(self):
        item = {"id": 1234567, "fileName": "a.jar", "downloadUrl": "https://cdn/a.jar"}
        self.assertEqual(CurseForgeAPI.resolve_download_url(item), "https://cdn/a.jar")

    def test_download_url_falls_back_to_cdn(self):
        item = {"id": 3456789, "fileName": "create-1.0.jar", "downloadUrl": None}
        self.assertEqual(
            CurseForgeAPI.resolve_download_url(item),
            "https://edge.forgecdn.net/files/3456/789/create-1.0.jar",
        )

    def test_download_url_missing_fields(self):
        self.assertIsNone(CurseForgeAPI.resolve_download_url({"id": None}))
        self.assertIsNone(CurseForgeAPI.resolve_download_url({"id": 1}))

    def test_to_mod_file(self):
        item = {
            "id": 999,
            "fileName": "mod.jar",
            "downloadUrl": "https://cdn/mod.jar",
            "fileLength": 2048,
            "displayName": "My Mod 1.0",
            "gameVersions": ["1.20.4", "Fabric"],
            "releaseType": 2,
            "dependencies": [{"modId": 42, "relationType": 3}],
        }
        mapped = CurseForgeAPI.to_mod_file(item)
        self.assertEqual(mapped["name"], "mod.jar")
        self.assertEqual(mapped["size"], 2048)
        self.assertEqual(mapped["release_type"], "beta")
        self.assertEqual(mapped["dependencies"][0]["project_id"], 42)
        self.assertEqual(mapped["dependencies"][0]["dependency_type"], "required")

    def test_to_mod_summary_versions(self):
        item = {
            "id": 7,
            "name": "Foo",
            "summary": "desc",
            "downloadCount": 123,
            "latestFilesIndexes": [
                {"gameVersion": "1.20.4"},
                {"gameVersion": "1.20.4"},
                {"gameVersion": "1.21"},
            ],
            "authors": [{"name": "A"}],
            "logo": {"thumbnailUrl": "https://img"},
            "links": {"websiteUrl": "https://cf/foo"},
        }
        summary = CurseForgeAPI.to_mod_summary(item)
        self.assertEqual(summary["versions"], ["1.20.4", "1.21"])
        self.assertEqual(summary["downloads"], 123)
        self.assertEqual(summary["author"], "A")

    def test_missing_api_key_raises(self):
        api = CurseForgeAPI(api_key="")
        with self.assertRaises(Exception):
            api._headers("")


if __name__ == "__main__":
    unittest.main()
