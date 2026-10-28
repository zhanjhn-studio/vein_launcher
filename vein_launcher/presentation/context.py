"""表现层 - 应用上下文（服务装配）

一次性构造全部应用服务，并完成插件宿主与其他服务的接线。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Any, Dict, Optional

from vein_launcher.application.services.account_service import AccountService
from vein_launcher.application.services.launcher_service import LauncherService
from vein_launcher.application.services.mod_service import ModService
from vein_launcher.application.services.plugin_service import PluginService
from vein_launcher.application.services.version_service import VersionService
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """所有服务的持有者"""

    accounts: AccountService
    versions: VersionService
    launcher: LauncherService
    mods: ModService
    plugins: PluginService
    _task_ids: Any = None

    @classmethod
    async def create(cls, plugins_root: Optional[Path] = None) -> "AppContext":
        accounts = AccountService()
        accounts.load()

        versions = VersionService()
        launcher = LauncherService(versions)
        mods = ModService()
        plugins = PluginService(plugins_root=plugins_root)

        ctx = cls(
            accounts=accounts,
            versions=versions,
            launcher=launcher,
            mods=mods,
            plugins=plugins,
            _task_ids=count(1),
        )
        ctx._wire_plugin_capabilities()
        return ctx

    # ------------------------------------------------------------------
    def _wire_plugin_capabilities(self) -> None:
        """把插件能力接到真实业务上"""

        async def _launch(version_id: str, memory_mb: int) -> Dict[str, Any]:
            account = self.accounts.current()
            pid = await self.launcher.launch_with_account(version_id, account)
            return {"pid": pid, "version_id": version_id, "memory_mb": memory_mb}

        async def _queue_task(url: str, save_path: str) -> int:
            from vein_launcher.infrastructure.download.downloader import download_file

            task_id = next(self._task_ids)
            asyncio.create_task(download_file(url, Path(save_path)))
            return task_id

        async def _cancel(task_id: int) -> bool:
            return False  # 预留：由下载队列实现取消

        self.plugins.set_callback("game.launch", _launch)
        self.plugins.set_callback("download.queueTask", _queue_task)
        self.plugins.set_callback("download.cancel", _cancel)

    # ------------------------------------------------------------------
    async def startup(self) -> None:
        """应用启动：拉账号、起插件宿主"""
        try:
            await self.plugins.start(autoload=True)
        except Exception as exc:  # 插件宿主故障不应导致启动器无法使用
            logger.error("插件宿主启动失败：%s", exc)
            event_bus.publish(
                EventNames.PLUGIN_ERROR, plugin_id="<host>", error=str(exc)
            )

    async def shutdown(self) -> None:
        """应用退出：停宿主、关连接"""
        await self.plugins.stop()
        await self.mods.close()
        await self.versions.close()


__all__ = ["AppContext"]
