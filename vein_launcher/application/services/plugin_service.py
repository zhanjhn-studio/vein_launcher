"""应用层 - 插件服务：加载插件、注入能力、桥接游戏事件到 MLC"""

from __future__ import annotations

import logging
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

        self._register_capabilities()

    # ------------------------------------------------------------------
    @property
    def host(self) -> PluginHost:
        return self._host

    def root_for(self, plugin_id: str) -> Path:
        return ensure_dir(self._loader.root / sanitize(plugin_id))

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
            return [
                {"name": c.name, "dir": c.is_dir()} for c in sorted(target.iterdir())
            ]

        async def config_read(plugin_id: str) -> Dict[str, Any]:
            return settings_manager.get().model_dump()

        async def config_write(plugin_id: str, key: str, value: Any) -> bool:
            settings = settings_manager.get()
            if not hasattr(settings, key):
                raise KeyError(key)
            setattr(settings, key, value)
            settings_manager.save()
            return True

        async def ui_notify(plugin_id: str, title: str, message: str) -> bool:
            event_bus.publish("ui.notify", title=title, message=message)
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

        async def mlc_player_info(plugin_id: str) -> Dict[str, Any]:
            return self._mlc.player_info()

        async def mlc_mod_load(plugin_id: str) -> Dict[str, Any]:
            return self._mlc.mod_load()

        async def mlc_plugin_search(plugin_id: str, keyword: str = "") -> Dict[str, Any]:
            return self._mlc.plugin_search(keyword)

        reg.register("file.readText", "file.read", read_text)
        reg.register("file.writeText", "file.write", write_text)
        reg.register("file.listDir", "file.read", list_dir)
        reg.register("config.read", "config.read", config_read)
        reg.register("config.write", "config.write", config_write)
        reg.register("ui.notify", "ui.notify", ui_notify)
        reg.register("network.http.getJson", "network.http", http_json)
        reg.register("download.queueTask", "download.queue", queue_task)
        reg.register("game.launch", "game.launch", game_launch)
        reg.register("mlc.launch", "game.launch", game_launch)
        reg.register("mlc.world.info", "mlc.world", mlc_world_info)
        reg.register("mlc.world.create", "mlc.world", mlc_world_create)
        reg.register("mlc.player.info", "mlc.player", mlc_player_info)
        reg.register("mlc.mod.load", "mlc.mod", mlc_mod_load)
        reg.register("mlc.plugin.search", "mlc.plugin", mlc_plugin_search)

    # ------------------------------------------------------------------
    async def start(self) -> None:
        """安装 demo、启动宿主、激活插件"""
        plugins = self._loader.scan()
        if not plugins:
            logger.info("没有可用插件")
            return

        await self._host.start()
        self._install_event_bridge()

        for plugin in plugins:
            if not plugin.manifest.activate_on_startup:
                continue
            try:
                self._registry.add_root(self.root_for(plugin.manifest.name))
                await self._host.load(plugin)
                self._plugins[plugin.manifest.name] = plugin
            except Exception as exc:
                logger.error("插件加载失败 %s：%s", plugin.manifest.name, exc)

    async def stop(self) -> None:
        await self._host.stop()
        self._plugins.clear()

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


__all__ = ["PluginService"]
