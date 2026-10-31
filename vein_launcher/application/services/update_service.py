"""应用层 - 一键更新

从 GitHub Releases 读取最新版本，下载发布资产（安装包/压缩包），并交给系统执行。
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from vein_launcher.common.utils.path_utils import ensure_dir, get_root_dir

logger = logging.getLogger(__name__)

REPO = "zhanjhn-studio/vein_launcher"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
TIMEOUT = 30
Progress = Callable[[int, int], None]


def parse_version(text: str) -> tuple[int, ...]:
    """'v0.1.0' / '0.1.0-beta' → (0, 1, 0)"""
    numbers = re.findall(r"\d+", str(text or ""))
    return tuple(int(n) for n in numbers[:3]) or (0, 0, 0)


def is_newer(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


class UpdateService:
    def __init__(self, current: str, repo: str = REPO):
        self.current = str(current)
        self._repo = repo
        self._api = f"https://api.github.com/repos/{repo}/releases/latest"
        self._dir = get_root_dir() / "downloads" / "update"

    # ------------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "VeinLauncher-Updater",
            "Accept": "application/vnd.github+json",
        }
        token = os.environ.get("VEIN_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def latest(self) -> Dict[str, Any]:
        github = await self._from_github()
        if not github.get("error"):
            return github
        logger.info("GitHub API 不可用（%s），改用公告源", github.get("error"))
        fallback = await self._from_announcements(github.get("error", ""))
        return fallback

    async def _from_announcements(self, reason: str) -> Dict[str, Any]:
        """GitHub API 被限流/不可达时，退回公告站维护的 update 字段"""
        url = "https://zhanjhn.github.io/vl/public.js"
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT)
            ) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return {"available": False, "current": self.current, "error": reason}
                    data = await resp.json(content_type=None)
        except Exception as exc:
            return {"available": False, "current": self.current, "error": f"{reason} / {exc}"}
        update = (data or {}).get("update") or {}
        version = str(update.get("version") or "").lstrip("v")
        if not version:
            return {"available": False, "current": self.current, "error": reason}
        return {
            "available": is_newer(version, self.current),
            "current": self.current,
            "version": version,
            "name": f"v{version}",
            "notes": str(update.get("notes") or ""),
            "html_url": str(update.get("url") or ""),
            "assets": [],
            "source": "announcements",
        }

    async def _from_github(self) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
            async with session.get(self._api, headers=self._headers()) as resp:
                if resp.status == 404:
                    return {"available": False, "current": self.current, "error": "No release yet"}
                if resp.status != 200:
                    return {
                        "available": False,
                        "current": self.current,
                        "error": f"GitHub API HTTP {resp.status}",
                    }
                data = await resp.json(content_type=None)
        if not isinstance(data, dict):
            return {"available": False, "current": self.current, "error": "Bad release payload"}

        version = str(data.get("tag_name") or "").lstrip("v")
        assets: List[Dict[str, Any]] = []
        for asset in data.get("assets") or []:
            if not isinstance(asset, dict):
                continue
            url = str(asset.get("browser_download_url") or "")
            if not url:
                continue
            assets.append(
                {
                    "name": str(asset.get("name") or Path(url).name),
                    "size": int(asset.get("size") or 0),
                    "url": url,
                }
            )
        return {
            "available": is_newer(version, self.current),
            "current": self.current,
            "version": version,
            "name": str(data.get("name") or data.get("tag_name") or ""),
            "notes": str(data.get("body") or ""),
            "published": str(data.get("published_at") or ""),
            "html_url": str(data.get("html_url") or ""),
            "assets": assets,
        }

    # ------------------------------------------------------------------
    async def download(self, url: str, name: str, progress: Optional[Progress] = None) -> Path:
        if not url.startswith("https://"):
            raise ValueError("只允许 https 下载地址")
        ensure_dir(self._dir)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name or "update.bin")
        target = self._dir / safe
        part = target.with_name(target.name + ".part")

        done = part.stat().st_size if part.is_file() else 0
        headers = self._headers()
        if done:
            headers["Range"] = f"bytes={done}-"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, sock_connect=20, sock_read=60)
        ) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status not in (200, 206):
                    raise RuntimeError(f"下载失败 HTTP {resp.status}")
                total = done + int(resp.headers.get("Content-Length") or 0)
                mode = "ab" if resp.status == 206 and done else "wb"
                if mode == "wb":
                    done = 0
                with open(part, mode) as handle:
                    async for chunk in resp.content.iter_chunked(64 * 1024):
                        handle.write(chunk)
                        done += len(chunk)
                        if progress:
                            progress(done, total or done)
        part.replace(target)
        logger.info("更新包已下载：%s（%s 字节）", target, target.stat().st_size)
        return target

    # ------------------------------------------------------------------
    def install(self, path: str) -> Dict[str, Any]:
        """执行更新：exe 直接启动安装程序；zip 解压到 update 目录并打开"""
        target = Path(path)
        if not target.is_file():
            raise FileNotFoundError(path)
        if target.suffix.lower() in (".exe", ".msi"):
            if sys.platform == "win32":
                os.startfile(str(target))  # noqa: S606 - 用户主动点击更新
            else:
                subprocess.Popen([str(target)], close_fds=True)
            return {"started": True, "kind": "installer", "path": str(target)}

        if target.suffix.lower() == ".zip":
            dest = ensure_dir(self._dir / f"extracted-{int(time.time())}")
            with zipfile.ZipFile(target) as archive:
                archive.extractall(dest)
            return {"started": True, "kind": "zip", "path": str(dest)}

        return {"started": False, "kind": "unknown", "path": str(target)}


__all__ = ["REPO", "UpdateService", "is_newer", "parse_version"]
