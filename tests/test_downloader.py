"""下载器测试 —— 使用本地 HTTP 服务器，零外网依赖

运行：
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import http.server
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path

from vein_launcher.infrastructure.download.downloader import (
    AsyncDownloader,
    DownloadTask,
)

SAMPLE = b"vein-launcher-download-test\n" * 500  # ~14KB
SAMPLE_SHA1 = hashlib.sha1(SAMPLE).hexdigest()


class _Handler(http.server.SimpleHTTPRequestHandler):
    """只服务一个内存文件，支持 Range"""

    payload = SAMPLE

    def do_GET(self):  # noqa: N802
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            start = int(range_header.split("=")[1].split("-")[0])
            body = self.payload[start:]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(self.payload) - 1}/{len(self.payload)}")
        else:
            start = 0
            body = self.payload
            self.send_response(200)

        self.send_header("Content-Length", str(len(body)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # 静音
        pass


class DownloaderTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="vein_test_")
        handler = functools.partial(_Handler, directory=cls.tmpdir)
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.port}/sample.bin"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="vein_dl_", dir=self.tmpdir))
        self.dest = self.work / "sample.bin"

    async def _download(self, **kwargs) -> object:
        async with AsyncDownloader(retry_count=kwargs.pop("retry_count", 0)) as dl:
            return await dl.download(DownloadTask(url=self.url, dest=self.dest, **kwargs))

    async def test_full_download(self):
        result = await self._download(expected_sha1=SAMPLE_SHA1)
        self.assertEqual(self.dest.read_bytes(), SAMPLE)
        self.assertFalse(result.skipped)
        self.assertFalse((self.work / "sample.bin.part").exists())

    async def test_skip_when_verified(self):
        self.dest.write_bytes(SAMPLE)
        result = await self._download(expected_sha1=SAMPLE_SHA1)
        self.assertTrue(result.skipped)

    async def test_resume_from_partial(self):
        part = self.dest.with_name(self.dest.name + ".part")
        part.write_bytes(SAMPLE[:4096])
        result = await self._download(expected_sha1=SAMPLE_SHA1, size=len(SAMPLE))
        self.assertEqual(self.dest.read_bytes(), SAMPLE)
        self.assertFalse(part.exists())
        self.assertEqual(result.bytes_written, len(SAMPLE) - 4096)

    async def test_sha_mismatch_raises_and_cleans(self):
        with self.assertRaises(Exception):
            await self._download(expected_sha1="0" * 40)
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.work / "sample.bin.part").exists())


if __name__ == "__main__":
    unittest.main()
