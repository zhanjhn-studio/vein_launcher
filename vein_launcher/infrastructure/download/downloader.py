"""基础设施层 - 单文件下载器（断点续传 + SHA-1 校验 + 同目标串行）"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import weakref
from pathlib import Path
from typing import Callable, Optional

import aiohttp

from vein_launcher.common.exceptions import DownloadError, SHA1MismatchError
from vein_launcher.common.utils.path_utils import ensure_dir
from vein_launcher.infrastructure.network.mirror import is_insecure, mark_insecure

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024
ProgressCallback = Callable[[int, int], None]  # downloaded, total

# 可重试的 HTTP 状态：限流 / 网关 / 服务端临时故障；其余 4xx（403/404…）立即失败
RETRYABLE_HTTP = {408, 425, 429, 500, 502, 503, 504}


class HTTPStatusDownloadError(DownloadError):
    """HTTP 状态异常（保留 status 供重试判定；状态码同时写在 message 里）"""

    def __init__(self, message: str, url: str = "", status: int = 0):
        super().__init__(message, url=url)
        self.status = status

# 同一目标文件的并发下载会互相踩踏（WinError 32 / SHA-1 失败），按目标串行
_LOCKS: "weakref.WeakValueDictionary[str, asyncio.Lock]" = weakref.WeakValueDictionary()


def _lock_for(dest: Path) -> asyncio.Lock:
    key = str(dest.resolve())
    lock = _LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _LOCKS[key] = lock
    return lock


class Downloader:
    """单文件下载（并发与队列由 queue.py 负责）"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None, retries: int = 3,
                 timeout: float = 60.0):
        self._session = session
        self._owns_session = session is None
        self._retries = max(0, retries)
        self._timeout = timeout
        self._insecure = False
        self._insecure_session_obj: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "Downloader":
        await self.session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def session(self) -> aiohttp.ClientSession:
        if self._session is not None and not self._session.closed:
            return self._session
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=self._timeout),
            headers={"User-Agent": "VeinLauncher/0.1.0 (Minecraft Launcher)"},
        )
        return self._session

    async def insecure_session(self) -> aiohttp.ClientSession:
        """证书链不完整的镜像节点专用会话（与常规会话并存，不互相影响）"""
        if self._insecure_session_obj is None or self._insecure_session_obj.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self._insecure_session_obj = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=self._timeout),
                headers={"User-Agent": "VeinLauncher/0.1.0 (Minecraft Launcher)"},
                connector=connector,
            )
        return self._insecure_session_obj

    async def close(self) -> None:
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None
        if self._insecure_session_obj is not None and not self._insecure_session_obj.closed:
            await self._insecure_session_obj.close()
        self._insecure_session_obj = None

    # ------------------------------------------------------------------
    async def download(
        self,
        url: str,
        dest: Path,
        sha1: Optional[str] = None,
        size: Optional[int] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Path:
        """下载到 dest；已存在且校验通过则直接返回"""
        dest = Path(dest)
        ensure_dir(dest.parent)

        async with _lock_for(dest):
            # 拿到锁后再检查一次，避免并发任务重复下载同一文件
            if dest.is_file() and self._verify_sync(dest, sha1, size):
                logger.debug("已存在且校验通过：%s", dest)
                return dest

            last_error: Optional[BaseException] = None
            for attempt in range(self._retries + 1):
                try:
                    await self._transfer(url, dest, sha1, size, progress)
                    return dest
                except asyncio.CancelledError:
                    raise
                except SHA1MismatchError as exc:
                    last_error = exc
                    if attempt >= self._retries:
                        break
                    logger.debug("SHA-1 不匹配，重下（%d/%d）：%s", attempt + 1, self._retries + 1, dest.name)
                except HTTPStatusDownloadError as exc:
                    last_error = exc
                    if attempt >= self._retries or exc.status not in RETRYABLE_HTTP:
                        logger.warning("下载失败 %s：HTTP %s", url, exc.status)
                        break
                    logger.debug("HTTP %s，重试（%d/%d）：%s", exc.status, attempt + 1,
                                 self._retries + 1, dest.name)
                    await asyncio.sleep(min(2 ** attempt, 8))
                except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
                    last_error = exc
                    text = str(exc)
                    if not self._insecure and ("CERTIFICATE_VERIFY_FAILED" in text or "SSL" in text):
                        self._insecure = True
                        mark_insecure(url)
                        logger.warning("证书校验失败，改用不校验会话重下：%s", dest.name)
                        continue
                    if attempt >= self._retries:
                        logger.warning("下载失败 %s：%s", url, exc)
                        break
                    logger.debug("下载重试（%d/%d）%s：%s", attempt + 1, self._retries + 1, dest.name, exc)
                    await asyncio.sleep(min(2 ** attempt, 8))

            raise DownloadError(f"下载失败：{last_error}", url=url)

    async def _transfer_segmented(self, url: str, dest: Path, sha1: Optional[str],
                                  progress: Optional[ProgressCallback], size: int,
                                  parts: int = 4, resume_from: int = 0) -> None:
        """多连接 Range 下载：失败由调用方回退单线程。"""
        import shutil

        part_dir = dest.with_name(dest.name + ".parts")
        shutil.rmtree(part_dir, ignore_errors=True)
        part_dir.mkdir(parents=True, exist_ok=True)
        chunk = max(1, size // parts)
        ranges = []
        for index in range(parts):
            start = index * chunk
            end = size - 1 if index == parts - 1 else min(size - 1, start + chunk - 1)
            ranges.append((index, start, end))

        session = await self.session()
        written = [0] * parts
        lock = asyncio.Lock()
        timeout = aiohttp.ClientTimeout(total=120, sock_read=45)

        async def fetch(index: int, start: int, end: int) -> None:
            path = part_dir / f"{index:03d}.bin"
            headers = {"Range": f"bytes={start}-{end}"}
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status != 206:
                    raise RuntimeError("server does not support range requests")
                with path.open("wb") as fh:
                    async for piece in response.content.iter_chunked(CHUNK_SIZE):
                        fh.write(piece)
                        written[index] += len(piece)
                        if progress:
                            async with lock:
                                progress(resume_from + sum(written), size)

        try:
            await asyncio.wait_for(
                asyncio.gather(*(fetch(i, s, e) for i, s, e in ranges)), timeout=180
            )
        except Exception:
            shutil.rmtree(part_dir, ignore_errors=True)
            dest.with_name(dest.name + ".part").unlink(missing_ok=True)
            raise

        hasher = hashlib.sha1()
        with dest.with_name(dest.name + ".part").open("wb") as out:
            for index, _start, _end in ranges:
                with (part_dir / f"{index:03d}.bin").open("rb") as fh:
                    while True:
                        block = fh.read(1024 * 1024)
                        if not block:
                            break
                        out.write(block)
                        hasher.update(block)
        shutil.rmtree(part_dir, ignore_errors=True)

        actual = hasher.hexdigest()
        if sha1 and actual.lower() != sha1.lower():
            dest.with_name(dest.name + ".part").unlink(missing_ok=True)
            raise SHA1MismatchError("SHA-1 校验失败", expected=sha1, actual=actual,
                                    file_path=str(dest))
        os.replace(dest.with_name(dest.name + ".part"), dest)

    async def _transfer(self, url: str, dest: Path, sha1: Optional[str],
                        size: Optional[int], progress: Optional[ProgressCallback]) -> None:
        ensure_dir(dest.parent)
        part = dest.with_name(dest.name + ".part")
        # 上一轮多线程中断留下的分段目录：重下前清掉，避免占空间/误用
        import shutil as _shutil

        _shutil.rmtree(dest.with_name(dest.name + ".parts"), ignore_errors=True)
        try:
            resume_from = part.stat().st_size if part.exists() else 0
        except FileNotFoundError:
            resume_from = 0
        headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}

        insecure = self._insecure or is_insecure(url)
        session = await (self.insecure_session() if insecure else self.session())
        async with session.get(url, headers=headers) as response:
            if response.status == 416:
                part.replace(dest)
                return
            if response.status not in (200, 206):
                raise HTTPStatusDownloadError(
                    f"HTTP {response.status}", url=url, status=response.status
                )

            if response.status == 200:
                resume_from = 0
                part.unlink(missing_ok=True)

            content_length = int(response.headers.get("Content-Length", 0) or 0)
            total = resume_from + content_length
            # 大文件且服务端支持 Range 时，4 连接并行下载；失败自动回退单线程
            if content_length >= 32 * 1024 * 1024 and not insecure:
                try:
                    await self._transfer_segmented(
                        url, dest, sha1, progress, content_length, parts=4, resume_from=0
                    )
                    return
                except Exception as exc:
                    logger.debug("多线程下载失败，回退单线程：%s", exc)
            hasher = hashlib.sha1()
            if resume_from:
                await asyncio.to_thread(self._hash_prefix, part, hasher)

            ensure_dir(part.parent)
            written = resume_from
            with part.open("ab") as fh:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    fh.write(chunk)
                    hasher.update(chunk)
                    written += len(chunk)
                    if progress:
                        progress(written, total or size or written)
                fh.flush()
                os.fsync(fh.fileno())

        actual = hasher.hexdigest()
        if sha1 and actual.lower() != sha1.lower():
            part.unlink(missing_ok=True)
            raise SHA1MismatchError("SHA-1 校验失败", expected=sha1, actual=actual,
                                    file_path=str(dest))
        os.replace(part, dest)

    # ------------------------------------------------------------------
    @staticmethod
    def _hash_prefix(path: Path, hasher) -> None:
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                hasher.update(block)

    @classmethod
    def _verify_sync(cls, path: Path, sha1: Optional[str], size: Optional[int]) -> bool:
        try:
            if sha1:
                hasher = hashlib.sha1()
                cls._hash_prefix(path, hasher)
                return hasher.hexdigest().lower() == sha1.lower()
            if size is not None:
                return path.stat().st_size == size
            return True
        except OSError:
            return False


__all__ = ["Downloader", "ProgressCallback", "HTTPStatusDownloadError", "RETRYABLE_HTTP"]
