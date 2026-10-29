"""基础设施层 - 下载队列（并发调度）"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.infrastructure.download.downloader import Downloader

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """一个下载任务"""

    url: str
    dest: Path
    sha1: Optional[str] = None
    size: Optional[int] = None
    done: bool = False
    error: Optional[str] = None


@dataclass
class QueueResult:
    """队列执行结果"""

    tasks: List[DownloadTask] = field(default_factory=list)

    @property
    def ok(self) -> int:
        return sum(1 for t in self.tasks if t.done)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tasks if t.error)


class DownloadQueue:
    """并发下载，进度通过 event_bus 广播"""

    def __init__(self, max_concurrent: int = 4, downloader: Optional[Downloader] = None):
        self._max_concurrent = max(1, max_concurrent)
        self._downloader = downloader or Downloader()
        self._owns = downloader is None
        self._completed = 0
        self._total = 0

    async def close(self) -> None:
        if self._owns:
            await self._downloader.close()

    # ------------------------------------------------------------------
    def _publish(self, task: DownloadTask, downloaded: int, total: int) -> None:
        event_bus.publish(
            EventNames.DOWNLOAD_TASK_PROGRESS,
            url=task.url,
            path=str(task.dest),
            downloaded=downloaded,
            total=total,
            done=self._completed,
            count=self._total,
        )

    async def _run_one(self, task: DownloadTask, semaphore: asyncio.Semaphore) -> None:
        async with semaphore:
            try:
                await self._downloader.download(
                    task.url,
                    task.dest,
                    sha1=task.sha1,
                    size=task.size,
                    progress=lambda d, t: self._publish(task, d, t),
                )
                task.done = True
            except Exception as exc:  # 单任务失败不影响其它任务
                task.error = str(exc)
                logger.error("下载失败 %s：%s", task.url, exc)
                event_bus.publish(EventNames.DOWNLOAD_TASK_ERROR, url=task.url, error=str(exc))
            finally:
                self._completed += 1
                event_bus.publish(
                    EventNames.DOWNLOAD_TASK_COMPLETE,
                    url=task.url,
                    path=str(task.dest),
                    done=self._completed,
                    count=self._total,
                )

    async def run(self, tasks: List[DownloadTask]) -> QueueResult:
        """并发执行全部任务（同一目标只下一次）"""
        unique: List[DownloadTask] = []
        seen = set()
        for task in tasks:
            key = str(task.dest)
            if key in seen:
                continue
            seen.add(key)
            unique.append(task)
        if len(unique) != len(tasks):
            logger.debug("队列去重：%d -> %d", len(tasks), len(unique))

        self._total = len(unique)
        self._completed = 0
        semaphore = asyncio.Semaphore(self._max_concurrent)
        await asyncio.gather(*(self._run_one(task, semaphore) for task in unique))
        return QueueResult(tasks=unique)


__all__ = ["DownloadQueue", "DownloadTask", "QueueResult"]
