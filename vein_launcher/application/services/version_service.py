"""应用层 - 版本服务

编排：Mojang API（获取清单/JSON） + 版本继承合并 + 下载器（client/libraries/assets）。
跨层通知只走 event_bus。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import VersionNotFoundError
from vein_launcher.common.utils.path_utils import (
    get_assets_dir,
    get_libraries_dir,
    get_version_dir,
    ensure_dir,
)
from vein_launcher.infrastructure.download.downloader import (
    AsyncDownloader,
    DownloadTask,
)
from vein_launcher.infrastructure.network.mojang_api import MojangAPI
from vein_launcher.infrastructure.network.download_sources import candidates
from vein_launcher.infrastructure.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)

# Mojang 版本 JSON 中需要向子版本覆盖的键
_MERGE_FORCE_KEYS = (
    "id", "type", "mainClass", "assets", "assetIndex", "javaVersion",
    "minecraftArguments", "downloads", "releaseTime", "time",
)


@dataclass
class InstallReport:
    """一次版本安装的统计"""

    version_id: str
    files_total: int = 0
    files_skipped: int = 0
    bytes_downloaded: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class VersionService:
    """版本列表 / 安装 / 卸载"""

    def __init__(
        self,
        mojang: Optional[MojangAPI] = None,
        storage: Optional[FileStorage] = None,
        downloader: Optional[AsyncDownloader] = None,
    ):
        self._mojang = mojang or MojangAPI()
        self._storage = storage or FileStorage()
        self._downloader = downloader
        self._merged_cache: Dict[str, Dict[str, Any]] = {}

    async def close(self) -> None:
        await self._mojang.close()

    # ------------------------------------------------------------------
    # 版本清单
    # ------------------------------------------------------------------
    async def list_remote_versions(
        self, include_snapshots: bool = False, limit: int = 200
    ) -> List[Dict[str, Any]]:
        """远程版本列表（release 优先）"""
        versions = await self._mojang.fetch_version_list()
        result = []
        for item in versions:
            if not include_snapshots and item.get("type") != "release":
                continue
            result.append(
                {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    "url": item.get("url"),
                    "release_time": item.get("releaseTime") or item.get("time", ""),
                    "installed": self._is_installed(item.get("id", "")),
                }
            )
            if len(result) >= limit:
                break
        return result

    def list_installed_versions(self) -> List[Dict[str, Any]]:
        """扫描本地 instances 目录"""
        root = get_version_dir(".").parent
        if not root.is_dir():
            return []
        result = []
        for child in sorted(root.iterdir(), reverse=True):
            if not child.is_dir():
                continue
            json_path = child / f"{child.name}.json"
            if not json_path.is_file():
                continue
            release_time, vtype = "", "release"
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                release_time = data.get("releaseTime", "")
                vtype = data.get("type", "release")
            except (json.JSONDecodeError, OSError):
                pass
            result.append(
                {
                    "id": child.name,
                    "type": vtype,
                    "release_time": release_time,
                    "path": str(child),
                }
            )
        return result

    def _is_installed(self, version_id: str) -> bool:
        return self._storage.version_json_path(version_id).is_file()

    async def remove_version(self, version_id: str) -> bool:
        import shutil

        target = get_version_dir(version_id)
        if not target.is_dir():
            return False
        shutil.rmtree(target, ignore_errors=True)
        self._merged_cache.pop(version_id, None)
        event_bus.publish(EventNames.VERSION_DELETED, version_id=version_id)
        return True

    # ------------------------------------------------------------------
    # 版本 JSON 合并
    # ------------------------------------------------------------------
    async def fetch_merged(self, version_id: str) -> Dict[str, Any]:
        """沿 inheritsFrom 链合并父版本（子覆盖父，库按 name 去重）"""
        if version_id in self._merged_cache:
            return self._merged_cache[version_id]

        chain: List[Dict[str, Any]] = []
        seen: set[str] = set()
        current: Optional[str] = version_id
        while current:
            if current in seen:
                raise VersionNotFoundError(f"循环继承：{version_id}")
            seen.add(current)
            chain.append(await self._mojang.fetch_version(current))
            current = chain[-1].get("inheritsFrom")

        merged: Dict[str, Any] = {}
        libraries: Dict[str, Dict[str, Any]] = {}
        arguments: Dict[str, List[Any]] = {"game": [], "jvm": []}

        for data in reversed(chain):  # 父 -> 子
            for key, value in data.items():
                if key in ("libraries", "arguments", "inheritsFrom"):
                    continue
                if key in _MERGE_FORCE_KEYS or key not in merged:
                    merged[key] = value

            for lib in data.get("libraries", []):
                libraries[lib.get("name", "")] = lib

            for section, items in (data.get("arguments") or {}).items():
                if isinstance(items, list):
                    arguments.setdefault(section, []).extend(items)

            if data.get("minecraftArguments"):
                merged["minecraftArguments"] = data["minecraftArguments"]

        merged["libraries"] = list(libraries.values())
        merged["arguments"] = arguments
        merged["_chain"] = [d.get("id") for d in chain]
        self._merged_cache[version_id] = merged
        return merged

    # ------------------------------------------------------------------
    # 安装
    # ------------------------------------------------------------------
    async def install(
        self,
        version_id: str,
        with_assets: bool = True,
        progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> InstallReport:
        """下载一个完整可启动的版本"""
        report = InstallReport(version_id=version_id)
        event_bus.publish(EventNames.VERSION_DOWNLOAD_START, version_id=version_id)

        merged = await self.fetch_merged(version_id)
        version_dir = ensure_dir(get_version_dir(version_id))

        # 1) 写入版本 JSON
        json_path = version_dir / f"{version_id}.json"
        json_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        tasks: List[DownloadTask] = []

        # 2) client jar
        client = (merged.get("downloads") or {}).get("client") or {}
        if client.get("url"):
            tasks.append(
                self._make_task(
                    client["url"],
                    self._storage.client_jar_path(version_id),
                    client.get("sha1"),
                    client.get("size"),
                )
            )

        # 3) libraries + natives
        natives_tasks = self._collect_library_tasks(merged)
        tasks.extend(natives_tasks)

        # 4) assets
        asset_tasks: List[DownloadTask] = []
        if with_assets:
            asset_tasks = await self._collect_asset_tasks(merged)

        all_tasks = tasks + asset_tasks
        report.files_total = len(all_tasks)

        if progress:
            progress("准备下载", 0, report.files_total)

        downloader = self._downloader or AsyncDownloader()
        own_downloader = self._downloader is None
        try:
            await self._run_batch(downloader, tasks, report, progress, "依赖库")
            if asset_tasks:
                await self._run_batch(downloader, asset_tasks, report, progress, "资源文件")
        finally:
            if own_downloader:
                await downloader.close()

        if report.errors:
            event_bus.publish(
                EventNames.VERSION_DOWNLOAD_ERROR,
                version_id=version_id,
                errors=report.errors[:10],
            )
        else:
            event_bus.publish(
                EventNames.VERSION_DOWNLOAD_COMPLETE, version_id=version_id
            )
        return report

    async def _run_batch(
        self,
        downloader: AsyncDownloader,
        tasks: Sequence[DownloadTask],
        report: InstallReport,
        progress: Optional[Callable[[str, int, int], None]],
        label: str,
    ) -> None:
        """分批并发下载，聚合进度与错误"""
        if not tasks:
            return

        batch_size = 24
        done = report.files_total - len(tasks)
        for start in range(0, len(tasks), batch_size):
            batch = list(tasks[start : start + batch_size])
            results = await downloader.download_many(batch)
            for result in results:
                if isinstance(result, BaseException):
                    report.errors.append(str(result))
                else:
                    report.bytes_downloaded += result.bytes_written
                    if result.skipped:
                        report.files_skipped += 1
            done += len(batch)
            if progress:
                progress(label, done, report.files_total)
            event_bus.publish(
                EventNames.VERSION_DOWNLOAD_PROGRESS,
                version_id=report.version_id,
                phase=label,
                done=done,
                total=report.files_total,
                percent=round(done * 100 / max(report.files_total, 1), 1),
            )

    # ------------------------------------------------------------------
    # 依赖收集
    # ------------------------------------------------------------------
    def _collect_library_tasks(self, merged: Dict[str, Any]) -> List[DownloadTask]:
        """收集库文件与 natives 解压任务"""
        tasks: List[DownloadTask] = []
        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue

            downloads = lib.get("downloads") or {}
            artifact = downloads.get("artifact")
            if artifact and artifact.get("url"):
                rel = artifact.get("path") or self._maven_to_path(lib.get("name", ""))
                tasks.append(
                    self._make_task(
                        artifact["url"],
                        get_libraries_dir() / rel,
                        artifact.get("sha1"),
                        artifact.get("size"),
                    )
                )

            # natives（Windows win64 分类器）
            classifiers = downloads.get("classifiers") or {}
            natives = lib.get("natives") or {}
            classifier_key = natives.get("windows")
            if classifier_key:
                key = classifier_key.replace("${arch}", "64")
                artifact = classifiers.get(key)
                if artifact and artifact.get("url"):
                    rel = artifact.get("path") or self._maven_to_path(lib.get("name", ""))
                    tasks.append(
                        self._make_task(
                            artifact["url"],
                            get_libraries_dir() / rel,
                            artifact.get("sha1"),
                            artifact.get("size"),
                        )
                    )
        return tasks

    async def _collect_asset_tasks(self, merged: Dict[str, Any]) -> List[DownloadTask]:
        """收集 assets 对象文件（objects/xx/hash）"""
        asset_index = merged.get("assetIndex") or {}
        if not asset_index.get("url"):
            return []

        objects = await self._storage.download_assets_index(
            asset_index.get("id", "legacy"), asset_index["url"]
        )
        if not isinstance(objects, dict):
            return []

        base = "https://resources.download.minecraft.net"
        tasks: List[DownloadTask] = []
        for _name, meta in objects.items():
            if not isinstance(meta, dict):
                continue
            digest = meta.get("hash")
            if not digest:
                continue
            prefix = digest[:2]
            tasks.append(
                self._make_task(
                    f"{base}/{prefix}/{digest}",
                    get_assets_dir() / "objects" / prefix / digest,
                    digest,
                    meta.get("size"),
                )
            )
        return tasks

    @staticmethod
    def _make_task(
        url: str,
        dest: Path,
        sha1: Optional[str] = None,
        size: Optional[int] = None,
    ) -> DownloadTask:
        """按下载源策略生成任务：首选地址 + 备用镜像列表"""
        urls = candidates(url)
        return DownloadTask(
            url=urls[0],
            dest=dest,
            expected_sha1=sha1,
            size=size,
            mirrors=tuple(urls[1:]),
        )

    @staticmethod
    def _maven_to_path(coord: str) -> str:
        parts = coord.split(":")
        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = f"-{parts[3]}" if len(parts) > 3 else ""
        return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}{classifier}.jar"

    @staticmethod
    def _rules_allow(rules: Optional[List[Dict[str, Any]]]) -> bool:
        """Mojang rules 求值：默认不允许，按顺序应用匹配规则"""
        if not rules:
            return True
        allowed = False
        for rule in rules:
            action = rule.get("action", "allow")
            os_rule = rule.get("os") or {}
            if os_rule and os_rule.get("name") != "windows":
                continue
            if "features" in rule:
                continue
            allowed = action == "allow"
        return allowed


__all__ = ["VersionService", "InstallReport"]
