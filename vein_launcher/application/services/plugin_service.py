"""应用层 - 插件服务

编排：PluginLoader（磁盘） + PluginHost（Node 进程） + CapabilityRegistry（能力）。
同时把启动器事件总线上的事件桥接给所有已激活插件。
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import get_plugin_sandbox_dir, ensure_dir
from vein_launcher.domain.models.plugin import PluginManifest
from vein_launcher.infrastructure.plugin_host.capabilities import (
    CapabilityRegistry,
    PluginPermissionError,
)
from vein_launcher.infrastructure.plugin_host.host import PluginHost, PluginHostError
from vein_launcher.infrastructure.plugin_host.loader import InstalledPlugin, PluginLoader

logger = logging.getLogger(__name__)

# 需要桥接给插件的启动器事件
BRIDGED_EVENTS = (
    EventNames.VERSION_DOWNLOAD_START,
    EventNames.VERSION_DOWNLOAD_PROGRESS,
    EventNames.VERSION_DOWNLOAD_COMPLETE,
    EventNames.VERSION_DOWNLOAD_ERROR,
    EventNames.DOWNLOAD_TASK_START,
    EventNames.DOWNLOAD_TASK_PROGRESS,
    EventNames.DOWNLOAD_TASK_COMPLETE,
    EventNames.DOWNLOAD_TASK_ERROR,
    EventNames.GAME_LAUNCH_START,
    EventNames.GAME_RUNNING,
    EventNames.GAME_LOG_UPDATE,
    EventNames.GAME_EXITED,
    EventNames.ACCOUNT_SELECTED,
    EventNames.MODS_UPDATED,
    EventNames.SETTINGS_UPDATED,
    EventNames.THEME_CHANGED,
)


class PluginService:
    """插件生命周期与能力注入"""

    def __init__(
        self,
        loader: Optional[PluginLoader] = None,
        host: Optional[PluginHost] = None,
        plugins_root: Optional[Path] = None,
    ):
        self._loader = loader or PluginLoader(plugins_root)
        root = Path(self._loader._root)  # noqa: SLF001 - 同包内已知约定
        self._capabilities = CapabilityRegistry(allowed_roots=[root])
        self._host = host or PluginHost(
            plugins_root=root, capabilities=self._capabilities
        )
        self._active: Dict[str, InstalledPlugin] = {}
        self._callbacks: Dict[str, Any] = {}
        self._bridge_installed = False
        self._install_default_capabilities()

    # ------------------------------------------------------------------
    # 能力注入
    # ------------------------------------------------------------------
    def set_callback(self, name: str, handler) -> None:
        """注入业务回调：game.launch / download.queueTask / download.cancel"""
        self._callbacks[name] = handler

    def _install_default_capabilities(self) -> None:
        cap = self._capabilities

        # ---- 文件（受沙箱约束）----
        async def _read_text(path: str) -> str:
            target = cap.check_path(path)
            if not target.is_file():
                raise VeinError(f"文件不存在：{target}")
            return await asyncio.to_thread(target.read_text, encoding="utf-8")

        async def _write_text(path: str, content: str) -> bool:
            target = cap.check_path(path)
            ensure_dir(target.parent)
            await asyncio.to_thread(target.write_text, content, encoding="utf-8")
            return True

        async def _list_dir(path: str) -> List[Dict[str, Any]]:
            target = cap.check_path(path)
            if not target.is_dir():
                raise VeinError(f"目录不存在：{target}")
            return await asyncio.to_thread(self._list_sync, target)

        cap.register("file.readText", "file.read", _read_text, "读取文本文件")
        cap.register("file.writeText", "file.write", _write_text, "写入文本文件")
        cap.register("file.listDir", "file.read", _list_dir, "列出目录")

        # ---- UI 通知 ----
        async def _notify(title: str, message: str, type_: str = "info") -> bool:
            event_bus.publish(
                EventNames.UI_NOTIFY, title=title, message=message, type=type_, source="plugin"
            )
            return True

        cap.register("ui.notify", "ui.notify", _notify, "弹出通知")

        # ---- 配置 ----
        async def _config_read() -> Dict[str, Any]:
            return settings_manager.get().model_dump()

        async def _config_write(key: str, value: Any) -> bool:
            settings = settings_manager.get()
            if not hasattr(settings, key):
                raise VeinError(f"未知配置项：{key}")
            setattr(settings, key, value)
            settings_manager.save()
            event_bus.publish(EventNames.SETTINGS_UPDATED, key=key)
            return True

        cap.register("config.read", "config.read", _config_read, "读取配置")
        cap.register("config.write", "config.write", _config_write, "修改配置")

        # ---- 网络 ----
        async def _http_get_json(url: str) -> Any:
            from vein_launcher.infrastructure.network.api_client import ApiClient

            async with ApiClient() as api:
                return await api.get_json(url)

        cap.register("network.http.getJson", "network.http", _http_get_json, "代理 HTTP GET")

        # ---- 下载 / 游戏（需 Application 注入）----
        async def _queue_task(url: str, save_path: str) -> int:
            handler = self._callbacks.get("download.queueTask")
            if handler is None:
                raise VeinError("下载队列尚未就绪")
            return await handler(url, save_path)

        async def _cancel(task_id: int) -> bool:
            handler = self._callbacks.get("download.cancel")
            if handler is None:
                return False
            return bool(await handler(task_id))

        async def _launch(version_id: str, memory_mb: int) -> Dict[str, Any]:
            handler = self._callbacks.get("game.launch")
            if handler is None:
                raise VeinError("启动服务尚未就绪")
            return await handler(version_id, memory_mb)

        cap.register("download.queueTask", "download.queue", _queue_task, "加入下载队列")
        cap.register("download.cancel", "download.cancel", _cancel, "取消下载")
        cap.register("game.launch", "game.launch", _launch, "启动游戏")

    @staticmethod
    def _list_sync(target: Path) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for child in sorted(target.iterdir()):
            try:
                stat = child.stat()
            except OSError:
                continue
            items.append(
                {
                    "name": child.name,
                    "path": str(child),
                    "isDir": child.is_dir(),
                    "size": 0 if child.is_dir() else stat.st_size,
                }
            )
        return items

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    async def start(self, autoload: bool = True) -> None:
        """启动宿主并激活插件"""
        await self._host.start()
        self._install_event_bridge()

        if not autoload:
            return
        for installed in self._loader.scan():
            if not installed.enabled:
                continue
            try:
                await self.enable(installed.plugin_id)
            except Exception as exc:  # 单个插件失败不影响启动
                logger.error("插件激活失败 %s: %s", installed.plugin_id, exc)
                event_bus.publish(
                    EventNames.PLUGIN_ERROR,
                    plugin_id=installed.plugin_id,
                    error=str(exc),
                )

    async def stop(self) -> None:
        for plugin_id in list(self._active):
            await self.disable(plugin_id)
        await self._host.stop()

    def _install_event_bridge(self) -> None:
        if self._bridge_installed:
            return
        self._bridge_installed = True

        for event_name in BRIDGED_EVENTS:
            event_bus.subscribe(event_name, self._make_bridge(event_name))

    def _make_bridge(self, event_name: str):
        def handler(**kwargs):
            if not self._host.running:
                return
            try:
                asyncio.get_running_loop().create_task(
                    self._host.emit_event(event_name, kwargs)
                )
            except RuntimeError:
                # 没有事件循环时（测试场景）直接忽略
                pass

        return handler

    # ------------------------------------------------------------------
    # 启停插件
    # ------------------------------------------------------------------
    async def enable(self, plugin_id: str) -> InstalledPlugin:
        installed = self._loader.get_installed(plugin_id)
        if not installed:
            raise PluginHostError(f"插件未安装：{plugin_id}")
        if plugin_id in self._active:
            return self._active[plugin_id]

        ensure_dir(get_plugin_sandbox_dir(plugin_id))
        self._capabilities.add_allowed_root(get_plugin_sandbox_dir(plugin_id))

        await self._host.load_plugin(installed.manifest, installed.path)
        self._loader.set_enabled(plugin_id, True)
        self._active[plugin_id] = installed
        event_bus.publish(EventNames.PLUGIN_LIST_UPDATED)
        return installed

    async def disable(self, plugin_id: str) -> None:
        if plugin_id in self._active:
            await self._host.unload_plugin(plugin_id)
            self._active.pop(plugin_id, None)
        self._loader.set_enabled(plugin_id, False)
        event_bus.publish(EventNames.PLUGIN_LIST_UPDATED)

    async def invoke(self, plugin_id: str, method: str, args: Optional[List[Any]] = None) -> Any:
        return await self._host.invoke(plugin_id, method, args or [])

    # ------------------------------------------------------------------
    # 安装 / 卸载
    # ------------------------------------------------------------------
    async def install_from_npm(self, spec: str) -> InstalledPlugin:
        installed = await self._loader.install_from_npm(spec)
        event_bus.publish(EventNames.PLUGIN_LIST_UPDATED)
        return installed

    async def install_from_dir(self, source: Path) -> InstalledPlugin:
        installed = await self._loader.install_from_dir(source)
        event_bus.publish(EventNames.PLUGIN_LIST_UPDATED)
        return installed

    async def uninstall(self, plugin_id: str) -> bool:
        await self.disable(plugin_id)
        ok = self._loader.remove(plugin_id)
        event_bus.publish(EventNames.PLUGIN_LIST_UPDATED)
        return ok

    # ------------------------------------------------------------------
    # 查询（供 UI）
    # ------------------------------------------------------------------
    def list_plugins(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for installed in self._loader.scan():
            manifest = installed.manifest
            result.append(
                {
                    "id": manifest.name,
                    "name": manifest.display_name,
                    "version": manifest.version,
                    "description": manifest.description,
                    "author": manifest.author,
                    "enabled": installed.enabled,
                    "active": manifest.name in self._active,
                    "permissions": list(manifest.permissions),
                    "plugin_type": manifest.plugin_type,
                    "path": str(installed.path),
                    "source": installed.source,
                }
            )
        return result

    def capability_catalog(self) -> List[Dict[str, str]]:
        """供设置页展示「宿主开放能力」"""
        return self._capabilities.describe()

    @property
    def host(self) -> PluginHost:
        return self._host


__all__ = ["PluginService", "BRIDGED_EVENTS"]
