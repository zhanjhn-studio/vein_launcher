"""应用层 - 插件服务：加载插件、注入能力、桥接游戏事件到 MLC"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.utils.path_utils import ensure_dir
from vein_launcher.infrastructure.download.downloader import Downloader
from vein_launcher.infrastructure.plugin_host.capabilities import CapabilityRegistry
from vein_launcher.infrastructure.plugin_host.host import PluginHost
from vein_launcher.infrastructure.plugin_host.loader import (
    InstalledPlugin,
    PluginLoader,
    plugins_root,
    sanitize,
)
from vein_launcher.mlc.service import MlcService

logger = logging.getLogger(__name__)

EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "plugins_examples"


class PluginService:
    """插件生命周期与能力注入"""

    def __init__(self, mlc: MlcService, launcher, loader: Optional[PluginLoader] = None):
        self._mlc = mlc
        self._launcher = launcher
        self._loader = loader or PluginLoader()
        self._registry = CapabilityRegistry(allowed_roots=[self._loader.root])
        self._host = PluginHost(self._registry)
        self._plugins: Dict[str, InstalledPlugin] = {}
        self._installed_event_bridge = False
        self._state_file = ensure_dir(self._loader.root.parent) / "plugins_state.json"
        self._enabled: Dict[str, bool] = self._load_state()

        self._register_capabilities()

    # ------------------------------------------------------------------
    @property
    def host(self) -> PluginHost:
        return self._host

    def root_for(self, plugin_id: str) -> Path:
        return ensure_dir(self._loader.root / sanitize(plugin_id))

    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, bool]:
        try:
            if self._state_file.is_file():
                return json.loads(self._state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("插件状态文件读取失败，使用默认值")
        return {}

    def _save_state(self) -> None:
        try:
            self._state_file.write_text(
                json.dumps(self._enabled, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            logger.exception("插件状态保存失败")

    def _is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, True)

    # ------------------------------------------------------------------
    def _safe_path(self, plugin_id: str, raw: str) -> Path:
        root = self.root_for(plugin_id).resolve()
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise PermissionError(f"越权路径：{resolved}") from exc
        return resolved

    # ------------------------------------------------------------------
    def _register_capabilities(self) -> None:
        reg = self._registry

        async def read_text(plugin_id: str, path: str) -> str:
            target = self._safe_path(plugin_id, path)
            if not target.is_file():
                raise FileNotFoundError(str(target))
            return target.read_text(encoding="utf-8")

        async def write_text(plugin_id: str, path: str, content: str) -> bool:
            target = self._safe_path(plugin_id, path)
            ensure_dir(target.parent)
            target.write_text(content, encoding="utf-8")
            return True

        async def list_dir(plugin_id: str, path: str = ".") -> List[Dict[str, Any]]:
            target = self._safe_path(plugin_id, path)
            if not target.is_dir():
                raise NotADirectoryError(str(target))
            return [{"name": c.name, "dir": c.is_dir()} for c in sorted(target.iterdir())]

        async def config_read(plugin_id: str) -> Dict[str, Any]:
            return settings_manager.get().model_dump()

        async def config_write(plugin_id: str, key: str, value: Any) -> bool:
            settings = settings_manager.get()
            if not hasattr(settings, key):
                raise KeyError(key)
            setattr(settings, key, value)
            settings_manager.save()
            return True

        async def ui_render(plugin_id: str, tree: Any) -> bool:
            event_bus.publish("plugin.ui", plugin_id=plugin_id, tree=tree)
            return True

        async def ui_notify(plugin_id: str, title: str, message: str) -> bool:
            event_bus.publish("ui.notify", title=title, message=message)
            return True

        async def ui_open_page(plugin_id: str, page: str) -> bool:
            """请求前端切换到指定页面（前端只认 NAV 里的 key，越界即忽略）"""
            key = str(page or "").strip()
            if not key or len(key) > 32:
                raise ValueError(f"非法页面标识：{page!r}")
            event_bus.publish("ui.open_page", page=key, plugin_id=plugin_id)
            return True

        async def http_json(plugin_id: str, url: str) -> Any:
            from vein_launcher.infrastructure.network.http_client import HttpClient

            async with HttpClient() as client:
                return await client.get_json(url)

        async def queue_task(plugin_id: str, url: str, save_path: str) -> str:
            target = self._safe_path(plugin_id, save_path)
            async with Downloader() as downloader:
                await downloader.download(url, target)
            return str(target)

        async def game_launch(plugin_id: str, version_id: str, username: str = "Player") -> Dict[str, Any]:
            return await self._mlc.launch(version_id, username)

        async def mlc_world_info(plugin_id: str, version_id: str) -> Dict[str, Any]:
            return self._mlc.world_info(version_id)

        async def mlc_world_create(plugin_id: str, version_id: str, name: str) -> Dict[str, Any]:
            return self._mlc.world_create(version_id, name)

        async def mlc_player_info(plugin_id: str, version_id: str = "", world: str = "") -> Dict[str, Any]:
            return self._mlc.player_info(version_id, world)

        async def mlc_world_detail(plugin_id: str, version_id: str, world: str) -> Dict[str, Any]:
            return self._mlc.world_detail(version_id, world)

        async def mlc_state(plugin_id: str) -> Dict[str, Any]:
            return self._mlc.state()

        async def mlc_mod_load(plugin_id: str, version_id: str = "", path: str = "") -> Dict[str, Any]:
            return self._mlc.mod_load(version_id, path)

        async def mlc_plugin_search(plugin_id: str, keyword: str = "") -> Dict[str, Any]:
            return self._mlc.plugin_search(keyword)

        reg.register("file.readText", "file.read", read_text)
        reg.register("file.writeText", "file.write", write_text)
        reg.register("file.listDir", "file.read", list_dir)
        reg.register("config.read", "config.read", config_read)
        reg.register("config.write", "config.write", config_write)
        reg.register("ui.notify", "ui.notify", ui_notify)
        reg.register("ui.openPage", "ui.open_page", ui_open_page)
        reg.register("ui.render", "ui.lua", ui_render)
        reg.register("network.http.getJson", "network.http", http_json)
        reg.register("download.queueTask", "download.queue", queue_task)
        reg.register("game.launch", "game.launch", game_launch)
        reg.register("mlc.launch", "game.launch", game_launch)
        reg.register("mlc.state", "mlc.state", mlc_state)
        reg.register("mlc.world.info", "mlc.world", mlc_world_info)
        reg.register("mlc.world.create", "mlc.world", mlc_world_create)
        reg.register("mlc.world.detail", "mlc.world", mlc_world_detail)
        reg.register("mlc.player.info", "mlc.player", mlc_player_info)
        reg.register("mlc.mod.load", "mlc.mod", mlc_mod_load)
        reg.register("mlc.plugin.search", "mlc.plugin", mlc_plugin_search)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    async def start(self) -> None:
        plugins = self._loader.scan()
        if not plugins:
            logger.info("没有可用插件")
            return

        await self._host.start()
        self._install_event_bridge()

        for plugin in plugins:
            if not self._is_enabled(plugin.manifest.name):
                continue
            if not plugin.manifest.activate_on_startup:
                continue
            await self._load_one(plugin)

    async def stop(self) -> None:
        await self._host.stop()
        self._plugins.clear()

    async def _load_one(self, plugin: InstalledPlugin) -> None:
        try:
            self._registry.add_root(self.root_for(plugin.manifest.name))
            await self._host.load(plugin)
            self._plugins[plugin.manifest.name] = plugin
            logger.info("插件已加载：%s", plugin.manifest.name)
        except Exception as exc:
            logger.error("插件加载失败 %s：%s", plugin.manifest.name, exc)

    # ------------------------------------------------------------------
    # 管理接口（供插件页使用）
    # ------------------------------------------------------------------
    def state(self) -> Dict[str, Any]:
        plugins = []
        for plugin in self._loader.scan():
            name = plugin.manifest.name
            plugins.append(
                {
                    "name": name,
                    "version": plugin.manifest.version,
                    "displayName": plugin.manifest.display_name,
                    "description": plugin.manifest.description,
                    "permissions": plugin.manifest.permissions,
                    "enabled": self._is_enabled(name),
                    "loaded": name in self._plugins,
                    "path": str(plugin.path),
                    "dataDir": str(plugin.data_dir),
                }
            )
        return {
            "host": {
                "running": self._host.running,
                "pid": self._host.pid,
                "node": self._host.node_path,
                "restarts": getattr(self._host, "_restarts", 0),
            },
            "root": str(self._loader.root),
            "plugins": plugins,
            "examples": self.examples(),
            "capabilities": self._registry.describe(),
        }

    def examples(self) -> List[Dict[str, str]]:
        """可安装的内置示例插件（扫描 plugins_examples/）"""
        items: List[Dict[str, str]] = []
        if not EXAMPLES_DIR.is_dir():
            return items
        installed = {p.manifest.name for p in self._loader.scan()}
        for child in sorted(EXAMPLES_DIR.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                manifest = PluginLoader.parse_manifest(child)
            except Exception as exc:
                logger.debug("示例清单解析失败 %s：%s", child.name, exc)
                continue
            items.append(
                {
                    "name": child.name,
                    "displayName": manifest.display_name,
                    "description": manifest.description,
                    "installed": manifest.name in installed or child.name in installed,
                }
            )
        return items

    def capabilities(self) -> List[Dict[str, str]]:
        """宿主开放的全部能力及其所需权限"""
        return self._registry.describe()

    async def set_enabled(self, name: str, enabled: bool) -> Dict[str, Any]:
        plugin = next((p for p in self._loader.scan() if p.manifest.name == name), None)
        if plugin is None:
            raise KeyError(f"插件不存在：{name}")

        self._enabled[name] = bool(enabled)
        self._save_state()

        if enabled:
            if not self._host.running:
                await self._host.start()
                self._install_event_bridge()
            await self._load_one(plugin)
        else:
            await self._host.unload(name)
            self._plugins.pop(name, None)
        return {"ok": True, "enabled": bool(enabled)}

    async def reload(self, name: str) -> Dict[str, Any]:
        plugin = next((p for p in self._loader.scan() if p.manifest.name == name), None)
        if plugin is None:
            raise KeyError(f"插件不存在：{name}")
        await self._host.unload(name)
        self._plugins.pop(name, None)
        if not self._host.running:
            await self._host.start()
            self._install_event_bridge()
        await self._load_one(plugin)
        return {"ok": True}

    def logs(self, limit: int = 200) -> List[str]:
        return self._host.recent_logs(limit)

    def install_example(self, name: str) -> Dict[str, Any]:
        source = EXAMPLES_DIR / name
        if not source.is_dir():
            raise FileNotFoundError(f"示例不存在：{name}")
        target = self._loader.root / sanitize(name)
        if target.exists():
            raise FileExistsError(f"插件已存在：{name}")
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("node_modules", "data"))
        self._enabled[name] = True
        self._save_state()
        logger.info("已安装示例插件：%s", name)
        return {"ok": True, "name": name}

    # ------------------------------------------------------------------
    def _install_event_bridge(self) -> None:
        if self._installed_event_bridge:
            return
        self._installed_event_bridge = True

        mapping = {
            EventNames.GAME_LOG_UPDATE: "mlc.game.log",
            EventNames.GAME_EXITED: "mlc.game.exit",
            EventNames.DOWNLOAD_TASK_PROGRESS: "mlc.download.progress",
        }
        for event_name, topic in mapping.items():
            event_bus.subscribe(event_name, self._forward(topic))

    def _forward(self, topic: str):
        def handler(**payload: Any) -> None:
            if not self._host.running:
                return
            try:
                import asyncio

                asyncio.get_running_loop().create_task(self._host.emit(topic, payload))
            except RuntimeError:
                pass

        return handler


__all__ = ["PluginService", "EXAMPLES_DIR"]
