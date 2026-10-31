"""应用层 - 整合包安装（.mrpack）"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir
from vein_launcher.infrastructure.download.downloader import Downloader

logger = logging.getLogger(__name__)

INDEX_NAME = "modrinth.index.json"


class ModpackService:
    """解析 MRPack 并安装到实例目录"""

    def __init__(self, downloader: Optional[Downloader] = None):
        self._downloader = downloader

    # ------------------------------------------------------------------
    @staticmethod
    def read_index(archive: Path) -> Dict[str, Any]:
        archive = Path(archive)
        if not archive.is_file():
            raise VeinError(f"整合包不存在：{archive}")
        try:
            with zipfile.ZipFile(archive) as zf:
                if INDEX_NAME not in zf.namelist():
                    raise VeinError("不是 Modrinth 整合包：缺少 modrinth.index.json")
                return json.loads(zf.read(INDEX_NAME).decode("utf-8"))
        except zipfile.BadZipFile as exc:
            raise VeinError(f"整合包损坏：{exc}") from exc

    # ------------------------------------------------------------------
    async def install(self, archive: Path, instance_id: str) -> Dict[str, Any]:
        index = self.read_index(archive)
        instance_dir = ensure_dir(get_version_dir(instance_id))

        overrides = await asyncio.to_thread(self._extract_overrides, archive, instance_dir)

        files = [
            f for f in index.get("files", [])
            if (f.get("env") or {}).get("client") != "unsupported"
        ]

        tasks = []
        for item in files:
            rel = item.get("path") or ""
            downloads = item.get("downloads") or []
            if not rel or not downloads:
                continue
            target = (instance_dir / rel).resolve()
            try:
                target.relative_to(instance_dir.resolve())
            except ValueError:
                logger.warning("跳过越界条目：%s", rel)
                continue
            tasks.append(
                (
                    downloads[0],
                    target,
                    (item.get("hashes") or {}).get("sha1"),
                )
            )

        downloader = self._downloader or Downloader()
        owns = self._downloader is None
        ok = failed = 0
        try:
            for url, target, sha1 in tasks:
                try:
                    await downloader.download(url, target, sha1=sha1)
                    ok += 1
                except Exception as exc:
                    failed += 1
                    logger.error("整合包文件失败 %s：%s", target.name, exc)
        finally:
            if owns:
                await downloader.close()

        deps = index.get("dependencies") or {}
        return {
            "name": index.get("name", ""),
            "minecraft": deps.get("minecraft"),
            "loader": next((k for k in deps if k != "minecraft"), None),
            "overrides": overrides,
            "files": len(tasks),
            "ok": ok,
            "failed": failed,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_overrides(archive: Path, instance_dir: Path) -> int:
        count = 0
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                for prefix in ("overrides/", "client-overrides/"):
                    if not member.startswith(prefix) or member.endswith("/"):
                        continue
                    rel = member[len(prefix):]
                    target = (instance_dir / rel).resolve()
                    try:
                        target.relative_to(instance_dir.resolve())
                    except ValueError:
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    count += 1
        return count


__all__ = ["ModpackService"]
