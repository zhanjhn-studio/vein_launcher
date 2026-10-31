"""应用层 - 实例内容管理

管理单个版本目录下的：
- mods / resourcepacks / shaderpacks / datapacks / modpacks（启用、禁用、删除）
- saves 存档列表（交给 MC2 读取种子等信息）

禁用方式沿用 Minecraft 生态惯例：文件重命名为 `<name>.disabled`。
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.utils.path_utils import resolve_version_dir
from vein_launcher.infrastructure.mc2.world_scanner import WorldScanner

logger = logging.getLogger(__name__)

CONTENT_DIRS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
    "modpack": "modpacks",
}

DISABLED_SUFFIX = ".disabled"


class InstanceError(RuntimeError):
    pass


def _norm_name(name: str) -> str:
    name = str(name or "").strip()
    # 只允许单个文件名，禁止路径穿越
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise InstanceError("非法的文件名")
    return name


class InstanceService:
    def __init__(self, versions_root: Optional[Path] = None):
        self._scanner = WorldScanner(versions_root or Path())

    # ------------------------------------------------------------------
    def base_dir(self, version_id: str) -> Path:
        path = resolve_version_dir(str(version_id))
        if not path.is_dir():
            raise InstanceError(f"版本不存在：{version_id}")
        return path

    def list_contents(self, version_id: str) -> Dict[str, List[Dict[str, Any]]]:
        base = self.base_dir(version_id)
        result: Dict[str, List[Dict[str, Any]]] = {}
        for kind, folder in CONTENT_DIRS.items():
            entries: List[Dict[str, Any]] = []
            directory = base / folder
            if directory.is_dir():
                for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
                    if item.name.startswith("."):
                        continue
                    disabled = item.name.endswith(DISABLED_SUFFIX)
                    display = item.name[: -len(DISABLED_SUFFIX)] if disabled else item.name
                    try:
                        size = item.stat().st_size if item.is_file() else 0
                    except OSError:
                        size = 0
                    entries.append(
                        {
                            "name": display,
                            "enabled": not disabled,
                            "size": size,
                            "dir": item.is_dir(),
                        }
                    )
            result[kind] = entries
        return result

    def _resolve_target(self, version_id: str, kind: str, name: str) -> Path:
        if kind not in CONTENT_DIRS:
            raise InstanceError(f"未知的内容类型：{kind}")
        name = _norm_name(name)
        directory = self.base_dir(version_id) / CONTENT_DIRS[kind]
        enabled = directory / name
        disabled = directory / f"{name}{DISABLED_SUFFIX}"
        if enabled.exists():
            return enabled
        if disabled.exists():
            return disabled
        raise InstanceError(f"文件不存在：{name}")

    def set_enabled(self, version_id: str, kind: str, name: str, enabled: bool) -> Dict[str, Any]:
        target = self._resolve_target(version_id, kind, name)
        directory = target.parent
        is_disabled = target.name.endswith(DISABLED_SUFFIX)
        if enabled and is_disabled:
            dest = directory / target.name[: -len(DISABLED_SUFFIX)]
            target.rename(dest)
            logger.info("已启用 %s → %s", target.name, dest.name)
            return {"name": dest.name, "enabled": True}
        if not enabled and not is_disabled:
            dest = directory / f"{target.name}{DISABLED_SUFFIX}"
            target.rename(dest)
            logger.info("已禁用 %s → %s", target.name, dest.name)
            return {"name": dest.name, "enabled": False}
        return {"name": target.name, "enabled": enabled}

    def delete(self, version_id: str, kind: str, name: str) -> Dict[str, Any]:
        target = self._resolve_target(version_id, kind, name)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        logger.info("已删除 %s", target)
        return {"deleted": True, "name": target.name}

    # ------------------------------------------------------------------
    def list_worlds(self, version_id: str) -> List[Dict[str, Any]]:
        base = self.base_dir(version_id)
        saves = base / "saves"
        worlds: List[Dict[str, Any]] = []
        if not saves.is_dir():
            return worlds
        for world in sorted(saves.iterdir(), key=lambda p: p.name.lower()):
            if not world.is_dir():
                continue
            info = self._scanner.read_world(str(version_id), world)
            if info:
                worlds.append(info)
        return worlds

    def delete_world(self, version_id: str, folder: str) -> Dict[str, Any]:
        folder = _norm_name(folder)
        target = self.base_dir(version_id) / "saves" / folder
        if not target.is_dir():
            raise InstanceError(f"存档不存在：{folder}")
        shutil.rmtree(target)
        logger.info("已删除存档 %s", target)
        return {"deleted": True}


__all__ = ["CONTENT_DIRS", "InstanceError", "InstanceService"]
