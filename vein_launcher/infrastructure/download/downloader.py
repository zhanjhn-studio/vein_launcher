"""基础设施层 - 单文件下载器（断点续传 + SHA-1 校验）"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Callable, Optional

import aiohttp

from vein_launcher.common.exceptions import DownloadError, SHA1MismatchError
from vein_launcher.common.utils.path_utils import ensure_dir

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024
ProgressCallback = Callable[[int, int], None]  # downloaded, total


class Downloader:
    """单文件下载（并发与队列由 queue.py 负责）"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None, retries: int = 3,
                 timeout: float = 60.0):
        self._session = session
        self._owns_session = session is None
        self._retries = max(0, retries)
        self._timeout = timeout

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

    async def close(self) -> None:
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

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
            except SHA1MismatchError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning("下载失败（%d/%d）%s -> %s", attempt + 1, self._retries + 1, url, exc)
                if attempt < self._retries:
                    await asyncio.sleep(min(2 ** attempt, 8))
        raise DownloadError(f"下载失败：{last_error}", url=url)

    async def _transfer(self, url: str, dest: Path, sha1: Optional[str],
                        size: Optional[int], progress: Optional[ProgressCallback]) -> None:
        part = dest.with_name(dest.name + ".part")
        resume_from = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}

        session = await self.session()
        async with session.get(url, headers=headers) as response:
            if response.status == 416:
                part.replace(dest)
                return
            if response.status not in (200, 206):
                raise DownloadError(f"HTTP {response.status}", url=url, status=response.status)

            if response.status == 200:
                resume_from = 0
                if part.exists():
                    part.unlink()

            total = resume_from + int(response.headers.get("Content-Length", 0) or 0)
            hasher = hashlib.sha1()
            if resume_from:
                await asyncio.to_thread(self._hash_prefix, part, hasher)

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
        if sha1:
            hasher = hashlib.sha1()
            cls._hash_prefix(path, hasher)
            return hasher.hexdigest().lower() == sha1.lower()
        if size is not None:
            return path.stat().st_size == size
        return True


__all__ = ["Downloader", "ProgressCallback"]
