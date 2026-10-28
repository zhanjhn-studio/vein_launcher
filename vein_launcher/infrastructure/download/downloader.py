"""基础设施层 - 异步文件下载器（断点续传 + 限速 + SHA-1 校验）

职责边界：
- 只负责「单个文件」的可靠下载：HTTP Range 续传、重试、限速、哈希校验、原子落盘。
- 队列调度、并发编排、任务可视化分别由 queue.py / Application 层承担。
- 跨层通知一律通过 event_bus 发布事件，不直接调用上层。

设计要点：
1. 先写 `*.part` 临时文件，校验通过后 os.replace 原子替换，避免半成品被误用。
2. 续传时先对已存在的前缀重新计算 SHA-1，再继续追加，保证最终哈希正确。
3. 服务端忽略 Range（返回 200）时自动回退为全量重下。
4. 限速基于令牌桶，按块消费，不会阻塞事件循环。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Deque, Iterable, List, Optional, Sequence, Tuple

import aiohttp

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import DownloadError, SHA1MismatchError
from vein_launcher.common.utils.path_utils import ensure_dir

logger = logging.getLogger(__name__)

# 单次读取块大小：64 KiB，兼顾吞吐与限速粒度
CHUNK_SIZE = 64 * 1024
# 进度回调最小间隔（秒），避免高频刷 UI
PROGRESS_INTERVAL = 0.1
# 默认 User-Agent，Mojang 对空 UA 可能返回 403
DEFAULT_USER_AGENT = "VeinLauncher/0.1.0 (Minecraft Java Launcher; +https://github.com/zhanjhn-studio/vein_launcher)"

# 进度回调签名：(已下载字节, 总字节, 当前速度 B/s)
ProgressCallback = Callable[[int, int, float], None]
# 通用协程回调（用于 download_many 的批量进度）
AsyncCallback = Callable[[int, int], Awaitable[None]]


@dataclass(slots=True)
class DownloadTask:
    """一个待下载文件的描述（纯数据，无行为以外的副作用）"""

    url: str
    """主下载地址"""

    dest: Path
    """最终落盘路径"""

    expected_sha1: Optional[str] = None
    """期望的 SHA-1（小写十六进制）；为空则跳过校验"""

    size: Optional[int] = None
    """期望文件大小（字节），仅用于「已完成」快速判定与进度总量兜底"""

    mirrors: Tuple[str, ...] = ()
    """备用镜像地址，主地址重试耗尽后依次尝试"""

    def part_path(self) -> Path:
        """临时文件路径，约定为 `${dest}.part`"""
        return self.dest.with_name(self.dest.name + ".part")

    def all_urls(self) -> Tuple[str, ...]:
        """按优先级返回全部候选地址（去重且保持顺序）"""
        ordered: List[str] = []
        for url in (self.url, *self.mirrors):
            if url and url not in ordered:
                ordered.append(url)
        return tuple(ordered)


@dataclass(slots=True)
class DownloadResult:
    """单个文件的下载结果"""

    url: str
    path: Path
    bytes_written: int
    skipped: bool = False
    """True 表示目标文件已存在且校验通过，未发生网络传输"""
    sha1: Optional[str] = None
    elapsed: float = 0.0

    @property
    def speed(self) -> float:
        """平均速度（B/s），耗时为 0 时返回 0"""
        return self.bytes_written / self.elapsed if self.elapsed > 0 else 0.0


class SpeedLimiter:
    """异步令牌桶限速器

    用法：
        limiter = SpeedLimiter(rate_mbps=10)   # 10 MB/s；0 表示不限速
        await limiter.acquire(len(chunk))
    """

    def __init__(self, rate_mbps: int = 0):
        self._rate = max(0, int(rate_mbps)) * 1024 * 1024
        self._tokens = float(self._rate)
        self._last_refill = time.monotonic()

    @property
    def enabled(self) -> bool:
        """是否启用了限速"""
        return self._rate > 0

    async def acquire(self, amount: int) -> None:
        """申请 amount 字节的配额，必要时挂起等待"""
        if not self.enabled or amount <= 0:
            return
        # 单次申请不得超过 0.1 秒的配额，保证平滑与及时响应取消
        step = max(1, self._rate // 10)
        remaining = amount
        while remaining > 0:
            chunk = min(remaining, step)
            await self._consume(chunk)
            remaining -= chunk

    async def _consume(self, need: int) -> None:
        while True:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(float(self._rate), self._tokens + elapsed * self._rate)
            self._last_refill = now
            if self._tokens >= need:
                self._tokens -= need
                return
            await asyncio.sleep((need - self._tokens) / self._rate)


class _ProgressReporter:
    """节流 + 平滑速度统计的进度上报器"""

    def __init__(self, task: DownloadTask, callback: Optional[ProgressCallback] = None):
        self._task = task
        self._callback = callback
        self._last_emit = 0.0
        self._samples: Deque[Tuple[float, int]] = deque(maxlen=64)

    def update(self, downloaded: int, total: int) -> None:
        """记录一次进度，按间隔节流后回调与发布事件"""
        now = time.monotonic()
        self._samples.append((now, downloaded))
        if now - self._last_emit < PROGRESS_INTERVAL and downloaded < total:
            return
        self._last_emit = now
        speed = self._compute_speed(now)
        if self._callback is not None:
            try:
                self._callback(downloaded, total, speed)
            except Exception as exc:  # 回调异常不得中断下载
                logger.warning("下载进度回调异常：%s", exc)
        event_bus.publish(
            EventNames.DOWNLOAD_TASK_PROGRESS,
            url=self._task.url,
            path=str(self._task.dest),
            downloaded=downloaded,
            total=total,
            speed=speed,
        )

    def _compute_speed(self, now: float) -> float:
        """基于最近 1 秒滑动窗口估算瞬时速度"""
        if not self._samples:
            return 0.0
        window_start = now - 1.0
        oldest = next((s for s in self._samples if s[0] >= window_start), self._samples[-1])
        span = now - oldest[0]
        if span <= 0:
            return 0.0
        return max(0.0, (self._samples[-1][1] - oldest[1]) / span)


class AsyncDownloader:
    """异步下载器

    典型用法：
        async with AsyncDownloader() as dl:
            await dl.download(DownloadTask(url, Path("a.jar"), expected_sha1="..."))

    并发用法：
        async with AsyncDownloader(max_concurrent=8) as dl:
            results = await dl.download_many(tasks)
    """

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrent: Optional[int] = None,
        retry_count: Optional[int] = None,
        speed_limit_mbps: Optional[int] = None,
        chunk_size: int = CHUNK_SIZE,
        timeout_total: Optional[float] = None,
    ):
        cfg = settings_manager.get().download
        self._max_concurrent = max_concurrent if max_concurrent is not None else cfg.max_concurrent
        self._retry_count = retry_count if retry_count is not None else cfg.retry_count
        self._speed_limit_mbps = (
            speed_limit_mbps if speed_limit_mbps is not None else cfg.max_speed_mbps
        )
        self._chunk_size = chunk_size
        self._timeout_total = timeout_total

        self._session = session
        self._owns_session = session is None
        self._semaphore = asyncio.Semaphore(max(1, self._max_concurrent))
        self._limiter = SpeedLimiter(self._speed_limit_mbps)
        self._closed = False

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "AsyncDownloader":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """惰性创建会话；复用时重置限速器以匹配最新配置"""
        if self._session is not None and not self._session.closed:
            return self._session
        if self._closed:
            raise DownloadError("下载器已关闭，无法继续使用")

        timeout = aiohttp.ClientTimeout(
            total=self._timeout_total, sock_connect=15, sock_read=120
        )
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            auto_decompress=True,
        )
        self._owns_session = True
        return self._session

    async def close(self) -> None:
        """关闭自建会话；外部注入的会话不由本类关闭"""
        self._closed = True
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    # ------------------------------------------------------------------
    # 单文件下载
    # ------------------------------------------------------------------
    async def download(
        self,
        task: DownloadTask,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> DownloadResult:
        """下载单个文件，返回结果；失败抛出 DownloadError 子类

        自动处理：目录创建、镜像轮询、重试退避、断点续传、哈希校验、原子替换。
        """
        started = time.monotonic()

        # 已完成判定：文件存在且（大小或哈希）匹配，直接短路
        if await self._is_already_complete(task):
            logger.debug("文件已存在且校验通过，跳过下载：%s", task.dest)
            return DownloadResult(
                url=task.url,
                path=task.dest,
                bytes_written=task.dest.stat().st_size if task.dest.exists() else 0,
                skipped=True,
                sha1=task.expected_sha1,
                elapsed=time.monotonic() - started,
            )

        ensure_dir(task.dest.parent)
        urls = task.all_urls()
        if not urls:
            raise DownloadError("下载地址为空", url="")

        last_error: Optional[BaseException] = None
        for url in urls:
            last_error = await self._download_with_retry(url, task, progress_callback)
            if isinstance(last_error, DownloadResult):
                return last_error
            logger.warning("镜像失败，尝试下一个地址：%s", url)

        assert last_error is not None
        event_bus.publish(
            EventNames.DOWNLOAD_TASK_ERROR,
            url=task.url,
            path=str(task.dest),
            error=str(last_error),
        )
        if isinstance(last_error, DownloadError):
            raise last_error
        raise DownloadError(f"下载失败：{last_error}", url=task.url)

    async def _download_with_retry(
        self,
        url: str,
        task: DownloadTask,
        progress_callback: Optional[ProgressCallback],
    ):
        """对同一地址执行带指数退避的重试，成功返回 DownloadResult"""
        async with self._semaphore:
            for attempt in range(self._retry_count + 1):
                try:
                    event_bus.publish(
                        EventNames.DOWNLOAD_TASK_START,
                        url=url,
                        path=str(task.dest),
                        attempt=attempt + 1,
                    )
                    result = await self._transfer(url, task, progress_callback)
                    event_bus.publish(
                        EventNames.DOWNLOAD_TASK_COMPLETE,
                        url=url,
                        path=str(task.dest),
                        bytes_written=result.bytes_written,
                        elapsed=result.elapsed,
                    )
                    return result
                except asyncio.CancelledError:
                    raise
                except SHA1MismatchError as exc:
                    # 哈希不符说明内容本身有问题，重试同一地址无意义，交给镜像轮询
                    logger.error("SHA-1 校验失败，放弃该地址：%s", url)
                    return exc
                except (DownloadError, aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
                    logger.warning(
                        "下载失败（第 %d/%d 次）：%s -> %s",
                        attempt + 1,
                        self._retry_count + 1,
                        url,
                        exc,
                    )
                    if attempt >= self._retry_count:
                        return exc
                    # 指数退避：1s, 2s, 4s ... 上限 8s
                    await asyncio.sleep(min(2 ** attempt, 8.0))
        return DownloadError("重试耗尽", url=url)

    async def _transfer(
        self,
        url: str,
        task: DownloadTask,
        progress_callback: Optional[ProgressCallback],
    ) -> DownloadResult:
        """执行一次实际的 HTTP 传输（含续传与校验）"""
        started = time.monotonic()
        session = await self._ensure_session()
        part = task.part_path()

        resume_from = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={resume_from}-"} if resume_from > 0 else {}

        async with session.get(url, headers=headers, allow_redirects=True) as resp:
            # 416：请求范围越界，说明 .part 已是完整文件
            if resp.status == 416:
                return self._finalize(task, part, task.expected_sha1, 0, started)

            if resp.status not in (200, 206):
                raise DownloadError(
                    f"HTTP {resp.status} {resp.reason}", url=url
                )

            if resp.status == 200:
                # 服务端忽略 Range，必须从头写
                resume_from = 0
                if part.exists():
                    part.unlink()

            content_length = int(resp.headers.get("Content-Length", "0") or 0)
            total = resume_from + content_length if content_length else (task.size or 0)

            hasher = hashlib.sha1()
            if resume_from > 0:
                # 续传前置：对已有前缀补算哈希
                await asyncio.to_thread(self._hash_existing_prefix, part, hasher)

            reporter = _ProgressReporter(task, progress_callback)
            downloaded = resume_from
            written = 0

            with part.open("ab") as fh:
                try:
                    async for chunk in resp.content.iter_chunked(self._chunk_size):
                        await self._limiter.acquire(len(chunk))
                        fh.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)
                        written += len(chunk)
                        reporter.update(downloaded, total or downloaded)
                finally:
                    fh.flush()
                    os.fsync(fh.fileno())

        return self._finalize(task, part, hasher.hexdigest(), written, started)

    def _finalize(
        self,
        task: DownloadTask,
        part: Path,
        actual_sha1: str,
        written: int,
        started: float,
    ) -> DownloadResult:
        """校验哈希并原子替换为最终文件"""
        if task.expected_sha1 and actual_sha1 and actual_sha1.lower() != task.expected_sha1.lower():
            part.unlink(missing_ok=True)
            raise SHA1MismatchError(
                "SHA-1 校验失败",
                expected=task.expected_sha1,
                actual=actual_sha1,
                file_path=str(task.dest),
            )

        os.replace(part, task.dest)
        size = task.dest.stat().st_size
        logger.debug("下载完成：%s (%s 字节)", task.dest, size)
        return DownloadResult(
            url=task.url,
            path=task.dest,
            bytes_written=written if written else size,
            skipped=False,
            sha1=actual_sha1 or None,
            elapsed=time.monotonic() - started,
        )

    @staticmethod
    def _hash_existing_prefix(path: Path, hasher) -> None:
        """以 1 MiB 块同步读取已有文件前缀并喂入哈希器"""
        with path.open("rb") as fh:
            while True:
                block = fh.read(1024 * 1024)
                if not block:
                    break
                hasher.update(block)

    async def _is_already_complete(self, task: DownloadTask) -> bool:
        """判断目标文件是否已完好的二次下载短路条件"""
        dest = task.dest
        if not dest.is_file():
            return False
        # 存在残留 .part 视为未完成，需继续续传
        if task.part_path().exists():
            return False
        if task.expected_sha1:
            actual = await asyncio.to_thread(self._file_sha1, dest)
            return actual.lower() == task.expected_sha1.lower()
        if task.size is not None:
            return dest.stat().st_size == task.size
        return True

    @staticmethod
    def _file_sha1(path: Path) -> str:
        """计算文件 SHA-1"""
        hasher = hashlib.sha1()
        AsyncDownloader._hash_existing_prefix(path, hasher)
        return hasher.hexdigest()

    # ------------------------------------------------------------------
    # 批量下载
    # ------------------------------------------------------------------
    async def download_many(
        self,
        tasks: Sequence[DownloadTask],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[DownloadResult | BaseException]:
        """并发下载多个文件，按输入顺序返回结果或异常（不中断整体流程）"""
        if not tasks:
            return []

        async def run(task: DownloadTask) -> DownloadResult | BaseException:
            try:
                return await self.download(task, progress_callback)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # 单文件失败不影响其余任务
                logger.error("批量下载中任务失败：%s -> %s", task.url, exc)
                return exc

        return list(await asyncio.gather(*(run(t) for t in tasks)))


async def download_file(
    url: str,
    dest: Path,
    expected_sha1: Optional[str] = None,
    size: Optional[int] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> DownloadResult:
    """便捷函数：一次性下载单个文件（内部自建并关闭会话）"""
    task = DownloadTask(
        url=url, dest=Path(dest), expected_sha1=expected_sha1, size=size
    )
    async with AsyncDownloader() as downloader:
        return await downloader.download(task, progress_callback)


__all__ = [
    "AsyncDownloader",
    "DownloadResult",
    "DownloadTask",
    "ProgressCallback",
    "SpeedLimiter",
    "download_file",
]
