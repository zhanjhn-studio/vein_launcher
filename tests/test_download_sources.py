"""下载源重写与候选排序测试"""

from __future__ import annotations

import unittest

from vein_launcher.infrastructure.network.download_sources import (
    BMCLAPI,
    OFFICIAL,
    candidates,
    get_source,
    manifest_candidates,
    rewrite,
)


class RewriteTest(unittest.TestCase):
    def test_manifest_rewrite(self):
        url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.assertEqual(
            rewrite(url, BMCLAPI),
            "https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json",
        )

    def test_version_json_rewrite(self):
        url = "https://piston-meta.mojang.com/v1/packages/abc/1.20.4.json"
        self.assertEqual(
            rewrite(url, BMCLAPI),
            "https://bmclapi2.bangbang93.com/v1/packages/abc/1.20.4.json",
        )

    def test_library_rewrite_adds_maven_prefix(self):
        url = "https://libraries.minecraft.net/net/fabricmc/fabric-loader/0.15.7/fabric-loader-0.15.7.jar"
        self.assertEqual(
            rewrite(url, BMCLAPI),
            "https://bmclapi2.bangbang93.com/maven/net/fabricmc/fabric-loader/0.15.7/fabric-loader-0.15.7.jar",
        )

    def test_assets_rewrite_adds_assets_prefix(self):
        url = "https://resources.download.minecraft.net/ab/abcdef"
        self.assertEqual(
            rewrite(url, BMCLAPI),
            "https://bmclapi2.bangbang93.com/assets/ab/abcdef",
        )

    def test_unknown_host_passthrough(self):
        url = "https://cdn.modrinth.com/data/abc/versions/1/file.jar"
        self.assertEqual(rewrite(url, BMCLAPI), url)

    def test_official_source_is_identity(self):
        url = "https://piston-meta.mojang.com/v1/packages/abc/1.20.4.json"
        self.assertEqual(rewrite(url, OFFICIAL), url)


class CandidatesTest(unittest.TestCase):
    URL = "https://resources.download.minecraft.net/ab/abcdef"

    def test_auto_prefers_official_then_mirror(self):
        result = candidates(self.URL, preferred="auto")
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0].startswith("https://resources.download.minecraft.net"))
        self.assertTrue(result[1].startswith("https://bmclapi2.bangbang93.com/assets"))

    def test_official_only(self):
        self.assertEqual(candidates(self.URL, preferred="official"), [self.URL])

    def test_mirror_only(self):
        result = candidates(self.URL, preferred="bmclapi")
        self.assertEqual(len(result), 1)
        self.assertIn("bmclapi", result[0])

    def test_unrewritable_returns_single(self):
        url = "https://cdn.modrinth.com/data/a/b.jar"
        self.assertEqual(candidates(url, preferred="auto"), [url])

    def test_manifest_candidates(self):
        self.assertEqual(len(manifest_candidates("auto")), 2)
        self.assertEqual(len(manifest_candidates("official")), 1)

    def test_custom_mirror_base(self):
        result = candidates(self.URL, preferred="bmclapi", mirror_base="https://mirror.example.com")
        self.assertEqual(result, ["https://mirror.example.com/assets/ab/abcdef"])

    def test_get_source_unknown_falls_back_official(self):
        self.assertEqual(get_source("nope").id, "official")


if __name__ == "__main__":
    unittest.main()
