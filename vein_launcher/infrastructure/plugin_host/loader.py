"""插件加载器 —— 插件发现、清单解析、安装与启停状态管理

插件目录布局：
    plugins/
      <plugin-name>/
        package.json          # NPM 标准字段 + vein 扩展
        vein_plugin.json      # 可选，独立扩展清单（优先）
        dist/main.js          # main_entry
        data/                 # 插件沙箱目录（读写仅限此处）
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import ensure_dir, get_plugins_dir, sanitize_plugin_id
from vein_launcher.domain.models.plugin import PluginManifest

logger = logging.getLogger(__name__)


class PluginLoadError(VeinError):
    """插件清单不合法或安装失败"""


@dataclass
class InstalledPlugin:
    """已安装插件的磁盘状态"""

    manifest: PluginManifest
    path: Path
    enabled: bool = True
    installed_at: datetime = field(default_factory=datetime.now)
    source: str = "local"

    @property
    def plugin_id(self) -> str:
        return self.manifest.name


class PluginLoader:
    """插件目录扫描与安装"""

    REGISTRY_FILENAME = "plugins.json"

    def __init__(self, root: Optional[Path] = None):
        self._root = Path(root) if root else get_plugins_dir()
        self._registry_path = self._root / self.REGISTRY_FILENAME
        self._state: Dict[str, Dict[str, Any]] = {}
        self._loaded_state = False

    # ------------------------------------------------------------------
    # 状态文件
    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, Dict[str, Any]]:
        if self._loaded_state:
            return self._state
        self._loaded_state = True
        if self._registry_path.is_file():
            try:
                self._state = json.loads(self._registry_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("插件状态文件损坏，已重置：%s", exc)
                self._state = {}
        return self._state

    def _save_state(self) -> None:
        ensure_dir(self._root)
        tmp = self._registry_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(self._registry_path)

    # ------------------------------------------------------------------
    # 扫描与解析
    # ------------------------------------------------------------------
    def scan(self) -> List[InstalledPlugin]:
        """扫描插件根目录，返回解析成功的插件列表"""
        ensure_dir(self._root)
        state = self._load_state()
        result: List[InstalledPlugin] = []

        for child in sorted(self._root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.name == "node_modules":
                continue
            try:
                manifest = self.parse_manifest(child)
            except PluginLoadError as exc:
                # 没有 package.json 的普通目录（如 node_modules 残留）静默跳过
                if "缺少 package.json" in str(exc):
                    logger.debug("跳过非插件目录 %s", child.name)
                else:
                    logger.warning("跳过插件 %s：%s", child.name, exc)
                continue

            record = state.get(manifest.name, {})
            result.append(
                InstalledPlugin(
                    manifest=manifest,
                    path=child,
                    enabled=bool(record.get("enabled", manifest.activate_on_startup or True)),
                    source=record.get("source", "local"),
                )
            )
        return result

    @staticmethod
    def parse_manifest(plugin_dir: Path) -> PluginManifest:
        """解析 package.json（+ 可选 vein_plugin.json）"""
        pkg_path = plugin_dir / "package.json"
        if not pkg_path.is_file():
            raise PluginLoadError("缺少 package.json")

        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PluginLoadError(f"package.json 解析失败：{exc}") from exc

        extra: Dict[str, Any] = dict(pkg.get("vein") or {})
        vein_path = plugin_dir / "vein_plugin.json"
        if vein_path.is_file():
            try:
                extra.update(json.loads(vein_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError as exc:
                raise PluginLoadError(f"vein_plugin.json 解析失败：{exc}") from exc

        name = pkg.get("name")
        if not name:
            raise PluginLoadError("package.json 缺少 name")

        return PluginManifest(
            name=name,
            version=str(pkg.get("version", "0.0.0")),
            description=pkg.get("description", ""),
            author=str(pkg.get("author", extra.get("author", "unknown"))),
            display_name=extra.get("displayName") or pkg.get("displayName") or name,
            license=pkg.get("license"),
            icon_path=extra.get("icon"),
            homepage_url=pkg.get("homepage"),
            repository_url=(pkg.get("repository") or {}).get("url")
            if isinstance(pkg.get("repository"), dict)
            else pkg.get("repository"),
            vein_required_version=extra.get("engines", {}).get("vein", ">=0.1.0")
            if isinstance(extra.get("engines"), dict)
            else extra.get("veinRequiredVersion", ">=0.1.0"),
            main_entry=extra.get("main") or pkg.get("main") or "dist/main.js",
            api_version=str(extra.get("apiVersion", "1.0")),
            permissions=list(extra.get("permissions", [])),
            plugin_type=extra.get("pluginType", "utility"),
            i18n_locales=dict(extra.get("locales", {})),
            activate_on_startup=bool(extra.get("activateOnStartup", False)),
        )

    # ------------------------------------------------------------------
    # 启停
    # ------------------------------------------------------------------
    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        state = self._load_state()
        state.setdefault(plugin_id, {})["enabled"] = enabled
        self._save_state()

    def get_installed(self, plugin_id: str) -> Optional[InstalledPlugin]:
        for plugin in self.scan():
            if plugin.plugin_id == plugin_id:
                return plugin
        return None

    # ------------------------------------------------------------------
    # 安装 / 卸载
    # ------------------------------------------------------------------
    async def install_from_npm(self, package_spec: str) -> InstalledPlugin:
        """用 npm 安装插件包到 plugins/ 目录

        package_spec 形如 "vein-plugin-example" 或 "git+https://..."
        """
        self._root.mkdir(parents=True, exist_ok=True)
        npm = shutil.which("npm")
        if not npm:
            raise PluginLoadError("未找到 npm，请先安装 Node.js")

        logger.info("npm 安装插件：%s", package_spec)
        proc = await asyncio.create_subprocess_exec(
            npm, "install", "--prefix", str(self._root), "--no-audit", "--no-fund", package_spec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        if proc.returncode != 0:
            raise PluginLoadError(
                f"npm 安装失败：{out.decode('utf-8', errors='replace')[-500:]}"
            )

        package_name = package_spec.split("@")[0] if not package_spec.startswith("@") else package_spec
        target = self._root / "node_modules" / package_name
        if not target.is_dir():
            raise PluginLoadError(f"安装后未找到插件目录：{target}")

        manifest = self.parse_manifest(target)
        dest = self._root / sanitize_plugin_id(manifest.name)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(target), str(dest))

        self.set_enabled(manifest.name, True)
        self._load_state().setdefault(manifest.name, {})["source"] = "npm"
        self._save_state()
        return InstalledPlugin(manifest=manifest, path=dest, enabled=True, source="npm")

    async def install_from_dir(self, source: Path) -> InstalledPlugin:
        """从本地目录安装（开发调试用）"""
        source = Path(source)
        manifest = self.parse_manifest(source)
        dest = self._root / sanitize_plugin_id(manifest.name)
        ensure_dir(dest)
        await asyncio.to_thread(
            shutil.copytree, source, dest, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("node_modules", ".git", "data"),
        )
        self.set_enabled(manifest.name, True)
        return InstalledPlugin(manifest=manifest, path=dest, enabled=True, source="local")

    def remove(self, plugin_id: str) -> bool:
        """删除插件目录与状态"""
        installed = self.get_installed(plugin_id)
        if not installed:
            return False
        shutil.rmtree(installed.path, ignore_errors=True)
        self._load_state().pop(plugin_id, None)
        self._save_state()
        return True


__all__ = ["PluginLoader", "InstalledPlugin", "PluginLoadError"]
