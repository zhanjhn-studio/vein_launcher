"""路径工具：VeinLauncher 根目录布局（对标 PCL）

运行时（打包后）根目录位于 exe 同级：<exe_dir>/VeinLauncher
开发态位于仓库根：<repo>/VeinLauncher

VeinLauncher/
├── democrat/   社区/广场数据（预留）
├── plugin/     Node 插件
├── log/        分类日志
├── config/     启动器配置
├── minecraft/  游戏版本与资源
└── downloads/  下载缓存
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

ROOT_NAME = "VeinLauncher"
SUBDIRS = ("democrat", "plugin", "log", "config", "minecraft", "downloads")
_LAYOUT_READY = False


def _exe_base() -> Path:
    """打包后取 exe 目录；开发态取仓库根"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # vein_launcher/common/utils/path_utils.py -> parents[3] = 仓库根
    return Path(__file__).resolve().parents[3]


def get_root_dir() -> Path:
    return _exe_base() / ROOT_NAME


def get_democrat_dir() -> Path:
    return get_root_dir() / "democrat"


def get_plugin_dir() -> Path:
    return get_root_dir() / "plugin"


def get_log_dir() -> Path:
    return get_root_dir() / "log"


def get_config_dir() -> Path:
    return get_root_dir() / "config"


def _minecraft_override_file() -> Path:
    return get_config_dir() / "minecraft_dir.json"


def get_minecraft_dir() -> Path:
    """默认 <root>/minecraft；用户可在设置里指定自己的 .minecraft 目录"""
    override = _minecraft_override_file()
    if override.is_file():
        try:
            data = json.loads(override.read_text(encoding="utf-8"))
            path = Path(str(data.get("path", "")).strip())
            if path and path.is_dir():
                return path
        except (OSError, json.JSONDecodeError):
            pass
    return get_root_dir() / "minecraft"


def set_minecraft_dir(path: str | None) -> Path:
    """设置或清除 .minecraft 目录；传空则恢复默认"""
    override = _minecraft_override_file()
    if not path:
        override.unlink(missing_ok=True)
        return get_root_dir() / "minecraft"
    target = Path(path).expanduser()
    if not target.is_dir():
        raise ValueError(f"目录不存在：{target}")
    for sub in ("instances", "assets", "libraries"):
        ensure_dir(target / sub) if sub == "instances" else None
    override.parent.mkdir(parents=True, exist_ok=True)
    override.write_text(
        json.dumps({"path": str(target)}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def get_downloads_dir() -> Path:
    return get_root_dir() / "downloads"


def get_app_data_dir() -> Path:
    """兼容旧调用：返回根目录"""
    return get_root_dir()


def get_instance_root() -> Path:
    return get_minecraft_dir() / "instances"


def resolve_version_dir(version_id: str) -> Path:
    """优先实例目录，其次标准 .minecraft/versions（兼容用户自装版本）"""
    primary = get_version_dir(version_id)
    if (primary / f"{version_id}.json").is_file():
        return primary
    try:
        legacy = get_minecraft_dir() / "versions" / version_id
        if (legacy / f"{version_id}.json").is_file():
            return legacy
    except Exception:
        pass
    return primary


def get_version_dir(version_id: str) -> Path:
    return get_instance_root() / version_id


def get_assets_dir() -> Path:
    return get_minecraft_dir() / "assets"


def get_libraries_dir() -> Path:
    return get_minecraft_dir() / "libraries"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def bootstrap_layout() -> Dict[str, Path]:
    """创建根目录与全部子目录（幂等），并尝试迁移旧版 APPDATA 数据"""
    global _LAYOUT_READY
    root = ensure_dir(get_root_dir())
    created: Dict[str, Path] = {"root": root}
    for name in SUBDIRS:
        created[name] = ensure_dir(root / name)
    for sub in ("instances", "assets", "libraries"):
        ensure_dir(get_minecraft_dir() / sub)

    if not _LAYOUT_READY:
        _LAYOUT_READY = True
        _migrate_legacy(root)
        logger.info("目录布局就绪：%s", root)
    return created


def _migrate_legacy(root: Path) -> None:
    """把旧版 %APPDATA%\\VeinLauncher 数据搬进新根目录（只做一次）"""
    marker = root / "config" / ".migrated"
    if marker.is_file():
        return
    appdata = os.environ.get("APPDATA")
    old = Path(appdata) / ROOT_NAME if appdata else None
    if not old or not old.is_dir() or old.resolve() == root.resolve():
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("noop\n", encoding="utf-8")
        return

    mapping = {
        "instances": get_minecraft_dir() / "instances",
        "assets": get_assets_dir(),
        "libraries": get_libraries_dir(),
        "plugins": get_plugin_dir(),
    }
    moved = 0
    for src_name, dst in mapping.items():
        src = old / src_name
        if not src.is_dir() or dst.exists() and any(dst.iterdir()):
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                for child in src.iterdir():
                    shutil.move(str(child), str(dst / child.name))
            else:
                shutil.move(str(src), str(dst))
            moved += 1
        except OSError as exc:
            logger.warning("旧数据迁移失败 %s：%s", src, exc)

    for name in ("config.json", "plugins_state.json"):
        src = old / name
        if src.is_file():
            try:
                shutil.copy2(src, get_config_dir() / name)
            except OSError:
                pass

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(f"migrated at {time.strftime('%Y-%m-%d %H:%M:%S')} items={moved}\n", encoding="utf-8")
    logger.info("旧版数据迁移完成：%d 项", moved)


def safe_join(base: Path, *paths: str) -> Path:
    full_path = base.joinpath(*paths).resolve()
    try:
        full_path.relative_to(base.resolve())
        return full_path
    except ValueError as exc:
        raise ValueError(f"路径穿越检测失败：{full_path}") from exc


def get_relative_path(full_path: Path, base: Path) -> str:
    try:
        return str(full_path.relative_to(base))
    except ValueError:
        return str(full_path)
