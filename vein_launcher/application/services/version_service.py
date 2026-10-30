"""应用层 - 版本服务（下载与安装）"""

from __future__ import annotations

import json
import logging
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from vein_launcher.common.exceptions import VersionNotFoundError
from vein_launcher.common.utils.path_utils import (
    ensure_dir,
    get_libraries_dir,
    get_version_dir,
    safe_join,
)
from vein_launcher.infrastructure.download.downloader import Downloader
from vein_launcher.infrastructure.download.queue import DownloadQueue, DownloadTask
from vein_launcher.infrastructure.network.api_client import MojangApiClient
from vein_launcher.infrastructure.network.mirror import mirror
from vein_launcher.infrastructure.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)

Progress = Callable[[str, int, int], None]


class VersionService:
    """版本安装 / 查询"""

    def __init__(
        self,
        api: Optional[MojangApiClient] = None,
        storage: Optional[FileStorage] = None,
        downloader: Optional[Downloader] = None,
    ):
        self._api = api or MojangApiClient()
        self._storage = storage or FileStorage()
        self._downloader = downloader
        self._merged_cache: Dict[str, Dict[str, Any]] = {}

    async def close(self) -> None:
        await self._api.close()

    # ------------------------------------------------------------------
    def list_installed(self) -> List[Dict[str, Any]]:
        root = get_version_dir(".").parent
        if not root.is_dir():
            return []
        result = []
        for child in sorted(root.iterdir(), reverse=True):
            json_path = child / f"{child.name}.json"
            if not child.is_dir() or not json_path.is_file():
                continue
            version_type = "release"
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                version_type = data.get("type", "release")
            except (json.JSONDecodeError, OSError):
                pass
            result.append({"id": child.name, "type": version_type})
        return result

    def is_installed(self, version_id: str) -> bool:
        return self._storage.version_json_path(version_id).is_file()

    def delete(self, version_id: str) -> bool:
        target = get_version_dir(version_id)
        if not target.is_dir():
            return False
        shutil.rmtree(target, ignore_errors=True)
        self._merged_cache.pop(version_id, None)
        return True

    # ------------------------------------------------------------------
    async def merged(self, version_id: str) -> Dict[str, Any]:
        """读取本地或远程版本 JSON，并沿 inheritsFrom 合并"""
        if version_id in self._merged_cache:
            return self._merged_cache[version_id]

        chain: List[Dict[str, Any]] = []
        seen: set[str] = set()
        current: Optional[str] = version_id
        while current:
            if current in seen:
                raise VersionNotFoundError(f"循环继承：{version_id}")
            seen.add(current)
            chain.append(await self._load_version_json(current))
            current = chain[-1].get("inheritsFrom")

        merged: Dict[str, Any] = {}
        libraries: Dict[str, Dict[str, Any]] = {}
        arguments: Dict[str, List[Any]] = {"game": [], "jvm": []}

        for data in reversed(chain):  # 父 -> 子
            for key, value in data.items():
                if key in ("libraries", "arguments", "inheritsFrom"):
                    continue
                merged[key] = value
            for lib in data.get("libraries", []):
                libraries[lib.get("name", "")] = lib
            for section, items in (data.get("arguments") or {}).items():
                if isinstance(items, list):
                    arguments.setdefault(section, []).extend(items)

        merged["libraries"] = list(libraries.values())
        merged["arguments"] = arguments
        self._merged_cache[version_id] = merged
        return merged

    async def _load_version_json(self, version_id: str) -> Dict[str, Any]:
        local = self._storage.version_json_path(version_id)
        if local.is_file():
            return json.loads(local.read_text(encoding="utf-8"))
        return await self._api.fetch_version(version_id)

    # ------------------------------------------------------------------
    async def install(self, version_id: str, progress: Optional[Progress] = None) -> Dict[str, Any]:
        """下载并安装指定版本，返回统计"""
        merged = await self.merged(version_id)
        version_dir = ensure_dir(get_version_dir(version_id))

        (version_dir / f"{version_id}.json").write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        tasks: List[DownloadTask] = []

        client = (merged.get("downloads") or {}).get("client") or {}
        if client.get("url"):
            tasks.append(
                DownloadTask(
                    url=mirror(client["url"]),
                    dest=self._storage.client_jar_path(version_id),
                    sha1=client.get("sha1"),
                    size=client.get("size"),
                )
            )

        tasks.extend(self._library_tasks(merged))
        tasks.extend(await self._asset_tasks(merged))

        total = len(tasks)
        if progress:
            progress("准备", 0, total)

        queue = DownloadQueue(downloader=self._downloader)
        try:
            result = await queue.run(tasks)
        finally:
            await queue.close()

        if progress:
            progress("完成", result.ok, total)

        return {
            "version_id": version_id,
            "files": total,
            "ok": result.ok,
            "failed": result.failed,
            "errors": [t.error for t in tasks if t.error][:10],
        }

    async def copy_instance(self, source_id: str, target_name: str) -> str:
        """以已安装版本为父，生成一个自定义名字的实例（不重复下载）"""
        target_name = target_name.strip()
        if not target_name:
            raise VeinError("版本名不能为空")
        safe = "".join(c for c in target_name if c not in '\\/:*?"<>|').strip()
        if not safe:
            raise VeinError("版本名包含非法字符")
        target_dir = get_version_dir(safe)
        if target_dir.exists():
            raise VeinError(f"实例已存在：{safe}")

        merged = await self.merged(source_id)
        merged["id"] = safe
        merged["inheritsFrom"] = source_id
        ensure_dir(target_dir)
        (target_dir / f"{safe}.json").write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("创建自定义实例：%s（继承 %s）", safe, source_id)
        return safe

    def list_files(self, instance_id: str, sub: str = "") -> list:
        base = get_version_dir(instance_id)
        target = safe_join(base, *([p for p in sub.split("/") if p] or ["."]))
        if not target.exists():
            return []
        entries = []
        for child in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                size = child.stat().st_size if child.is_file() else 0
            except OSError:
                size = 0
            entries.append({
                "name": child.name,
                "dir": child.is_dir(),
                "size": size,
                "rel": str(child.relative_to(base)).replace("\\", "/"),
            })
        return entries

    def delete_file(self, instance_id: str, rel: str) -> bool:
        base = get_version_dir(instance_id)
        target = safe_join(base, *rel.split("/"))
        if target == base or not target.exists():
            return False
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        logger.info("删除实例文件：%s", target)
        return True

    # ------------------------------------------------------------------
    def _library_tasks(self, merged: Dict[str, Any]) -> List[DownloadTask]:
        tasks: List[DownloadTask] = []
        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue
            downloads = lib.get("downloads") or {}
            artifact = downloads.get("artifact")
            if artifact and artifact.get("url"):
                path = artifact.get("path") or self._maven_path(lib.get("name", ""))
                if not path:
                    continue
                tasks.append(
                    DownloadTask(
                        url=mirror(artifact["url"]),
                        dest=get_libraries_dir() / path,
                        sha1=artifact.get("sha1"),
                        size=artifact.get("size"),
                    )
                )
        return tasks

    async def _asset_tasks(self, merged: Dict[str, Any]) -> List[DownloadTask]:
        asset_index = merged.get("assetIndex") or {}
        url = asset_index.get("url")
        if not url:
            return []

        index = await self._api.fetch_assets_index(url)
        index_id = str(asset_index.get("id", "legacy"))
        await self._storage.write_bytes(
            self._storage.assets_index_path(index_id),
            json.dumps(index, ensure_ascii=False).encode("utf-8"),
        )

        base = "https://resources.download.minecraft.net"
        virtual = bool(index.get("virtual") or index.get("map_to_resources"))
        tasks: List[DownloadTask] = []
        for name, meta in (index.get("objects") or {}).items():
            digest = meta.get("hash")
            if not digest:
                continue
            url = mirror(f"{base}/{digest[:2]}/{digest}")
            tasks.append(
                DownloadTask(
                    url=url,
                    dest=self._storage.asset_object_path(digest),
                    sha1=digest,
                    size=meta.get("size"),
                )
            )
            # 旧式索引（键为路径名）需要把对象额外落到 virtual/<id>/ 下
            if virtual:
                tasks.append(
                    DownloadTask(
                        url=url,
                        dest=get_assets_dir() / "virtual" / index_id / name,
                        sha1=digest,
                        size=meta.get("size"),
                    )
                )
        return tasks

    # ------------------------------------------------------------------
    @staticmethod
    def _maven_path(coord: str) -> str:
        parts = coord.split(":")
        if len(parts) < 3:
            return ""
        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = f"-{parts[3]}" if len(parts) > 3 else ""
        return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}{classifier}.jar"

    @staticmethod
    def _rules_allow(rules: Optional[List[Dict[str, Any]]]) -> bool:
        if not rules:
            return True
        allowed = False
        for rule in rules:
            os_rule = rule.get("os") or {}
            if os_rule and os_rule.get("name") not in (None, "windows"):
                continue
            allowed = rule.get("action", "allow") == "allow"
        return allowed


__all__ = ["VersionService"]
