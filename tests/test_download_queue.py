"""下载队列进度回调测试（不联网）"""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from vein_launcher.infrastructure.download.queue import DownloadQueue, DownloadTask


class FakeDownloader:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def download(self, url, dest, sha1=None, size=None, progress=None):
        self.urls.append(url)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(b"ok")
        return Path(dest)

    async def close(self) -> None:
        pass


class QueueProgressTests(unittest.TestCase):
    def test_progress_reports_each_completed_task(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        seen: list[tuple[int, int]] = []

        tasks = [
            DownloadTask(url=f"https://example.invalid/{i}", dest=root / f"f{i}.bin")
            for i in range(5)
        ]
        queue = DownloadQueue(
            max_concurrent=2,
            downloader=FakeDownloader(),
            progress=lambda done, total: seen.append((done, total)),
        )
        result = asyncio.run(queue.run(tasks))

        self.assertEqual(result.ok, 5)
        self.assertEqual(result.failed, 0)
        self.assertEqual(len(seen), 5, "每个任务完成都应回调一次进度")
        self.assertEqual(seen[-1], (5, 5))
        self.assertEqual([d for d, _ in seen], [1, 2, 3, 4, 5])

    def test_failed_task_is_counted_not_raised(self) -> None:
        class Boom(FakeDownloader):
            async def download(self, url, dest, sha1=None, size=None, progress=None):
                raise RuntimeError("boom")

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tasks = [DownloadTask(url="https://example.invalid/x", dest=Path(tmp.name) / "x.bin")]
        queue = DownloadQueue(downloader=Boom())
        result = asyncio.run(queue.run(tasks))
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.ok, 0)
        self.assertTrue(tasks[0].error)


if __name__ == "__main__":
    unittest.main()
