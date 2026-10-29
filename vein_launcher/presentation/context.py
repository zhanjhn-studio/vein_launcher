"""表现层 - 应用上下文（服务装配）"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from vein_launcher.application.services.account_service import AccountService
from vein_launcher.application.services.launcher_service import LauncherService
from vein_launcher.application.services.loader_service import LoaderService
from vein_launcher.application.services.modpack_service import ModpackService
from vein_launcher.application.services.plugin_service import PluginService
from vein_launcher.application.services.version_service import VersionService
from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir, get_version_dir
from vein_launcher.infrastructure.download.downloader import Downloader
from vein_launcher.infrastructure.network.api_client import MojangApiClient
from vein_launcher.infrastructure.network.modrinth_api import ModrinthApiClient
from vein_launcher.infrastructure.process.java_detector import JavaDetector
from vein_launcher.mlc.service import MlcService

logger = logging.getLogger(__name__)

VERSION = "0.0.1"

SUBDIRS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
    "plugin": "plugins",
    "modpack": "modpacks",
}


class AppContext:
    """所有后端子服务"""

    def __init__(self) -> None:
        self.version = VERSION
        self.data_dir = ensure_dir(get_app_data_dir())

        self.versions_api = MojangApiClient()
        self.versions = VersionService(api=self.versions_api)
        self.launcher = LauncherService(self.versions)
        self.accounts = AccountService()
        self.accounts.load()
        self.modrinth = ModrinthApiClient()
        self.detector = JavaDetector()
        self.loaders = LoaderService(self.versions, detector=self.detector)
        self.modpacks = ModpackService()

        # MLC 控制层 + 插件宿主（核心特色）
        self.mlc = MlcService(self.launcher)
        self.mlc.install_bridge()
        self.plugins = PluginService(self.mlc, self.launcher)

    # ------------------------------------------------------------------
    @staticmethod
    def instance_sub_dir(instance_id: str, project_type: str) -> Path:
        return get_version_dir(instance_id) / SUBDIRS.get(project_type, "mods")

    @staticmethod
    async def modrinth_download(url: str, dest: Path, sha1: Optional[str]) -> None:
        async with Downloader() as downloader:
            await downloader.download(url, dest, sha1=sha1 or None)

    # ------------------------------------------------------------------
    async def startup(self) -> None:
        try:
            await self.plugins.start()
        except Exception as exc:
            logger.error("插件宿主启动失败：%s", exc)

    async def close(self) -> None:
        await self.plugins.stop()
        await self.loaders.close()
        await self.versions.close()
        await self.modrinth.close()


__all__ = ["AppContext", "VERSION", "SUBDIRS"]
