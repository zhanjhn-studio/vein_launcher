"""基础设施层 - 本地文件存储（路径与目录约定）"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from vein_launcher.common.utils.path_utils import (
    ensure_dir,
    get_assets_dir,
    get_libraries_dir,
    get_version_dir,
)
from vein_launcher.infrastructure.download.sha_checker import sha1_file_async, verify_file

logger = logging.getLogger(__name__)


class FileStorage:
    """Minecraft 目录结构访问"""

    # ------------------------------------------------------------------
    # 版本
    # ------------------------------------------------------------------
    @staticmethod
    def version_dir(version_id: str) -> Path:
        return ensure_dir(get_version_dir(version_id))

    @classmethod
    def version_json_path(cls, version_id: str) -> Path:
        return cls.version_dir(version_id) / f"{version_id}.json"

    @classmethod
    def client_jar_path(cls, version_id: str) -> Path:
        return cls.version_dir(version_id) / f"{version_id}.jar"

    # ------------------------------------------------------------------
    # 依赖库 / 资源
    # ------------------------------------------------------------------
    @staticmethod
    def library_path(maven_coord: str) -> Path:
        """Maven 坐标 -> libraries 下的路径"""
        parts = maven_coord.split(":")
        if len(parts) < 3:
            raise ValueError(f"非法 Maven 坐标：{maven_coord}")
        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = f"-{parts[3]}" if len(parts) > 3 else ""
        return (
            get_libraries_dir()
            / Path(*group.split("."))
            / artifact
            / version
            / f"{artifact}-{version}{classifier}.jar"
        )

    @staticmethod
    def asset_object_path(hash_name: str) -> Path:
        return get_assets_dir() / "objects" / hash_name[:2] / hash_name

    @staticmethod
    def assets_index_path(index_id: str) -> Path:
        return ensure_dir(get_assets_dir() / "indexes") / f"{index_id}.json"

    # ------------------------------------------------------------------
    # 校验
    # ------------------------------------------------------------------
    @staticmethod
    async def verify(path: Path, sha1: Optional[str]) -> bool:
        if not path.is_file():
            return False
        if not sha1:
            return True
        return await verify_file(path, sha1)

    @staticmethod
    async def sha1(path: Path) -> Optional[str]:
        return await sha1_file_async(path)

    @staticmethod
    async def write_bytes(path: Path, data: bytes) -> Path:
        ensure_dir(path.parent)

        def _write() -> None:
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)

        await asyncio.to_thread(_write)
        return path


__all__ = ["FileStorage"]
