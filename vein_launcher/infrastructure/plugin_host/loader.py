"""插件加载器：扫描 plugins/ 目录并解析清单"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir

logger = logging.getLogger(__name__)


class PluginLoadError(VeinError):
    """插件清单不合法"""


def plugins_root() -> Path:
    return ensure_dir(get_app_data_dir() / "plugins")


def sanitize(name: str) -> str:
    return name.replace("/", "__").replace("\\", "__").strip()


@dataclass
class PluginManifest:
    name: str
    version: str
    display_name: str
    main: str
    permissions: List[str]
    description: str = ""
    activate_on_startup: bool = False


@dataclass
class InstalledPlugin:
    manifest: PluginManifest
    path: Path

    @property
    def data_dir(self) -> Path:
        return ensure_dir(self.path / "data")


class PluginLoader:
    """插件目录扫描与 demo 安装"""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or plugins_root()

    # ------------------------------------------------------------------
    def scan(self) -> List[InstalledPlugin]:
        ensure_dir(self.root)
        plugins: List[InstalledPlugin] = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                plugins.append(InstalledPlugin(self.parse_manifest(child), child))
            except PluginLoadError as exc:
                logger.debug("跳过 %s：%s", child.name, exc)
        return plugins

    @staticmethod
    def parse_manifest(plugin_dir: Path) -> PluginManifest:
        pkg = plugin_dir / "package.json"
        if not pkg.is_file():
            raise PluginLoadError("缺少 package.json")
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PluginLoadError(f"package.json 解析失败：{exc}") from exc

        name = data.get("name")
        if not name:
            raise PluginLoadError("package.json 缺少 name")

        vein = data.get("vein") or {}
        return PluginManifest(
            name=name,
            version=str(data.get("version", "0.0.0")),
            display_name=vein.get("displayName") or name,
            main=vein.get("main") or data.get("main") or "index.js",
            permissions=list(vein.get("permissions") or []),
            description=data.get("description", ""),
            activate_on_startup=bool(vein.get("activateOnStartup", False)),
        )


__all__ = [
    "PluginLoader",
    "PluginManifest",
    "InstalledPlugin",
    "PluginLoadError",
    "plugins_root",
    "sanitize",
]
