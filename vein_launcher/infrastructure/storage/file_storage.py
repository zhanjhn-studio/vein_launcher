"""基础设施层 - 本地文件仓储实现

实现 Domain 层定义的 Assets / Libraries / Mods 三个仓储接口，
所有路径统一使用 pathlib，禁止字符串拼接。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import SHA1MismatchError
from vein_launcher.common.utils.path_utils import (
    ensure_dir,
    get_assets_dir,
    get_libraries_dir,
    get_version_dir,
)
from vein_launcher.domain.repositories.file_repo import (
    AssetsRepository,
    LibraryRepository,
    ModRepository,
)

logger = logging.getLogger(__name__)


class FileStorage(AssetsRepository, LibraryRepository, ModRepository):
    """本地文件仓储综合实现"""

    # ------------------------------------------------------------------
    # 基础文件操作
    # ------------------------------------------------------------------
    async def save_file(
        self,
        file_path: Path,
        content_bytes: bytes,
        expected_sha1: Optional[str] = None,
    ) -> bool:
        if expected_sha1:
            actual = hashlib.sha1(content_bytes).hexdigest()
            if actual.lower() != expected_sha1.lower():
                raise SHA1MismatchError(
                    "SHA-1 校验失败",
                    expected=expected_sha1,
                    actual=actual,
                    file_path=str(file_path),
                )
        await asyncio.to_thread(self._write_atomic, file_path, content_bytes)
        return True

    @staticmethod
    def _write_atomic(path: Path, data: bytes) -> None:
        ensure_dir(path.parent)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    async def load_file(self, file_path: Path) -> Optional[bytes]:
        if not file_path.is_file():
            return None
        return await asyncio.to_thread(file_path.read_bytes)

    async def exists(self, file_path: Path) -> bool:
        return file_path.is_file()

    async def sha1_hash(self, file_path: Path) -> Optional[str]:
        if not file_path.is_file():
            return None
        return await asyncio.to_thread(self._sha1_sync, file_path)

    @staticmethod
    def _sha1_sync(path: Path) -> str:
        hasher = hashlib.sha1()
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                hasher.update(block)
        return hasher.hexdigest()

    async def delete_file(self, file_path: Path) -> bool:
        try:
            if file_path.is_file():
                file_path.unlink()
            return True
        except OSError as exc:
            logger.error("删除文件失败 %s: %s", file_path, exc)
            return False

    async def ensure_dir(self, dir_path: Path) -> None:
        await asyncio.to_thread(ensure_dir, dir_path)

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------
    async def download_assets_index(self, index_id: str, url: str) -> Dict[str, Any]:
        """下载并缓存 assets/indexes/{id}.json，返回 objects 字典"""
        index_path = get_assets_dir() / "indexes" / f"{index_id}.json"
        if index_path.is_file():
            try:
                data = json.loads(index_path.read_text(encoding="utf-8"))
                return data.get("objects", data)
            except json.JSONDecodeError:
                pass

        from vein_launcher.infrastructure.network.api_client import ApiClient

        async with ApiClient() as api:
            data = await api.get_json(url)

        await asyncio.to_thread(self._write_text_atomic, index_path, json.dumps(data))
        return data.get("objects", data)

    @staticmethod
    def _write_text_atomic(path: Path, text: str) -> None:
        ensure_dir(path.parent)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)

    async def get_asset_file_path(self, hash_name: str) -> Path:
        """objects/ab/cdef.../abcdef..."""
        prefix = hash_name[:2]
        return get_assets_dir() / "objects" / prefix / hash_name

    # ------------------------------------------------------------------
    # Libraries
    # ------------------------------------------------------------------
    async def get_library_cache_path(self, maven_coord: str) -> Path:
        """Maven 坐标 -> libraries 下的路径

        例：net.fabricmc:fabric-loader:0.15.0 -> net/fabricmc/fabric-loader/0.15.0/fabric-loader-0.15.0.jar
        """
        parts = maven_coord.split(":")
        if len(parts) < 3:
            raise ValueError(f"非法 Maven 坐标：{maven_coord}")
        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = parts[3] if len(parts) > 3 else None

        group_path = Path(*group.split("."))
        file_name = f"{artifact}-{version}"
        if classifier:
            file_name += f"-{classifier}"
        file_name += ".jar"
        return get_libraries_dir() / group_path / artifact / version / file_name

    async def extract_natives(
        self,
        jar_path: Path,
        target_dir: Path,
        exclude_patterns: Optional[List[str]] = None,
    ) -> bool:
        """解压 natives jar（跳过 META-INF 等非必要文件）"""
        exclude = tuple(exclude_patterns or ("META-INF/",))

        def _extract() -> None:
            ensure_dir(target_dir)
            with zipfile.ZipFile(jar_path) as zf:
                for member in zf.namelist():
                    if member.endswith("/") or any(member.startswith(p) for p in exclude):
                        continue
                    zf.extract(member, target_dir)

        try:
            await asyncio.to_thread(_extract)
            return True
        except (OSError, zipfile.BadZipFile) as exc:
            logger.error("解压 natives 失败 %s: %s", jar_path, exc)
            return False

    # ------------------------------------------------------------------
    # 版本目录
    # ------------------------------------------------------------------
    def version_dir(self, version_id: str) -> Path:
        return get_version_dir(version_id)

    def version_json_path(self, version_id: str) -> Path:
        directory = get_version_dir(version_id)
        return directory / f"{version_id}.json"

    def client_jar_path(self, version_id: str) -> Path:
        return get_version_dir(version_id) / f"{version_id}.jar"

    def natives_dir(self, version_id: str) -> Path:
        return get_version_dir(version_id) / "natives"

    # ------------------------------------------------------------------
    # Mods
    # ------------------------------------------------------------------
    async def get_version_mods_dir(self, version_id: str) -> Path:
        directory = get_version_dir(version_id) / "mods"
        await asyncio.to_thread(ensure_dir, directory)
        return directory

    async def list_enabled_mods(self, version_id: str) -> List[str]:
        directory = get_version_dir(version_id) / "mods"
        if not directory.is_dir():
            return []
        return sorted(
            p.name for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() == ".jar" and not p.name.endswith(".disabled.jar")
        )

    async def disable_mod(self, version_id: str, mod_file_name: str) -> bool:
        directory = get_version_dir(version_id) / "mods"
        source = directory / mod_file_name
        if not source.is_file():
            return False
        target = directory / (mod_file_name[: -len(".jar")] + ".disabled.jar")
        try:
            source.replace(target)
            return True
        except OSError as exc:
            logger.error("禁用模组失败 %s: %s", source, exc)
            return False

    async def enable_mod(self, version_id: str, disabled_name: str) -> bool:
        """恢复 .disabled.jar 为 .jar"""
        directory = get_version_dir(version_id) / "mods"
        source = directory / disabled_name
        if not source.is_file() or not disabled_name.endswith(".disabled.jar"):
            return False
        target = directory / disabled_name[: -len(".disabled.jar")] + ".jar"
        try:
            source.replace(target)
            return True
        except OSError:
            return False


__all__ = ["FileStorage"]
