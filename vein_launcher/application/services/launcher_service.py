"""应用层 - 启动服务

职责：把「版本 JSON + 账号 + 配置」翻译成一条 Java 命令行并执行。
命令行构建是纯函数式的，便于单元测试。
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import GameLaunchError, JavaNotFoundError
from vein_launcher.common.utils.path_utils import get_assets_dir, get_libraries_dir, get_version_dir
from vein_launcher.domain.models.account import MicrosoftAccount, OfflineAccount
from vein_launcher.infrastructure.process.game_process import GameProcess
from vein_launcher.infrastructure.process.java_detector import JavaDetector, JavaInstallation
from vein_launcher.infrastructure.storage.file_storage import FileStorage
from vein_launcher.application.services.version_service import VersionService

logger = logging.getLogger(__name__)


@dataclass
class LaunchOptions:
    """一次启动的全部可变参数"""

    version_id: str
    username: str = "Player"
    uuid: str = ""
    access_token: str = "0"
    user_type: str = "legacy"
    memory_min: int = 2048
    memory_max: int = 4096
    width: int = 0
    height: int = 0
    fullscreen: bool = False
    jvm_args: List[str] = field(default_factory=list)
    game_dir: Optional[Path] = None
    extra_game_args: List[str] = field(default_factory=list)


class LauncherService:
    """构建并执行启动命令"""

    def __init__(
        self,
        version_service: VersionService,
        detector: Optional[JavaDetector] = None,
        process: Optional[GameProcess] = None,
        storage: Optional[FileStorage] = None,
    ):
        self._versions = version_service
        self._detector = detector or JavaDetector()
        self._process = process or GameProcess()
        self._storage = storage or FileStorage()

    @property
    def process(self) -> GameProcess:
        return self._process

    # ------------------------------------------------------------------
    # 命令构建
    # ------------------------------------------------------------------
    async def build_command(
        self, options: LaunchOptions, java: Optional[JavaInstallation] = None
    ) -> List[str]:
        """构建完整 Java 命令行"""
        merged = await self._versions.fetch_merged(options.version_id)

        if java is None:
            required = int((merged.get("javaVersion") or {}).get("majorVersion", 8))
            installations = await self._detector.detect_all()
            java = self._detector.select_best(required, installations)
            if java is None:
                raise JavaNotFoundError(
                    f"未找到满足 Java {required}+ 的运行时，请安装 JDK 或在设置中指定"
                )

        version_dir = get_version_dir(options.version_id)
        natives_dir = self._storage.natives_dir(options.version_id)
        await self._prepare_natives(merged, natives_dir)

        classpath = self._build_classpath(merged, options.version_id)
        replacements = self._build_replacements(options, merged, classpath, natives_dir)

        jvm_part = self._render_arguments(
            (merged.get("arguments") or {}).get("jvm", []), replacements
        )
        game_part = self._render_game_arguments(merged, replacements)

        command: List[str] = [
            str(java.path),
            f"-Xms{options.memory_min}M",
            f"-Xmx{options.memory_max}M",
        ]
        # 新版权本 JSON 已自带 -Djava.library.path 与 -cp，避免重复注入
        if not any("java.library.path" in arg for arg in jvm_part):
            command.append(f"-Djava.library.path={natives_dir}")
        command += [
            "-Dminecraft.launcher.brand=vein_launcher",
            "-Dfile.encoding=UTF-8",
            *options.jvm_args,
            *jvm_part,
        ]

        has_classpath_flag = any(arg in ("-cp", "-classpath") for arg in jvm_part)
        if not has_classpath_flag:
            command += ["-cp", classpath]

        command.append(merged.get("mainClass", "net.minecraft.client.main.Main"))
        command += game_part
        return command

    def _build_classpath(self, merged: Dict[str, Any], version_id: str) -> str:
        """client jar + 所有库 artifact"""
        entries: List[str] = []
        client = self._storage.client_jar_path(version_id)
        if client.is_file():
            entries.append(str(client))

        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue
            artifact = (lib.get("downloads") or {}).get("artifact")
            if artifact and artifact.get("path"):
                jar = get_libraries_dir() / artifact["path"]
                if jar.is_file():
                    entries.append(str(jar))
        return os.pathsep.join(entries)

    async def _prepare_natives(self, merged: Dict[str, Any], natives_dir: Path) -> None:
        """把带 natives 分类器的 jar 解压到 natives 目录"""
        if not natives_dir.is_dir():
            natives_dir.mkdir(parents=True, exist_ok=True)

        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue
            natives = lib.get("natives") or {}
            key = natives.get("windows")
            if not key:
                continue
            classifier = key.replace("${arch}", "64")
            artifact = ((lib.get("downloads") or {}).get("classifiers") or {}).get(classifier)
            if not artifact or not artifact.get("path"):
                continue
            jar = get_libraries_dir() / artifact["path"]
            if jar.is_file():
                await self._storage.extract_natives(jar, natives_dir)

    def _build_replacements(
        self,
        options: LaunchOptions,
        merged: Dict[str, Any],
        classpath: str,
        natives_dir: Path,
    ) -> Dict[str, str]:
        assets_root = get_assets_dir()
        asset_index = (merged.get("assetIndex") or {}).get("id") or merged.get("assets", "legacy")
        game_dir = options.game_dir or get_version_dir(options.version_id)
        player_uuid = options.uuid or self.offline_uuid(options.username)

        return {
            "auth_player_name": options.username,
            "version_name": options.version_id,
            "game_directory": str(game_dir),
            "assets_root": str(assets_root),
            "game_assets": str(assets_root),
            "assets_index_name": str(asset_index),
            "auth_uuid": player_uuid,
            "auth_access_token": options.access_token,
            "auth_session": options.access_token,
            "clientid": "",
            "auth_xuid": "",
            "user_type": options.user_type,
            "version_type": merged.get("type", "release"),
            "natives_directory": str(natives_dir),
            "classpath": classpath,
            "classpath_separator": os.pathsep,
            "library_directory": str(get_libraries_dir()),
            "launcher_name": "vein_launcher",
            "launcher_version": "0.1.0",
            "resolution_width": str(options.width) if options.width else "",
            "resolution_height": str(options.height) if options.height else "",
        }

    def _render_game_arguments(
        self, merged: Dict[str, Any], repl: Dict[str, str]
    ) -> List[str]:
        """新版 arguments.game；旧版回退 minecraftArguments"""
        args = self._render_arguments(
            (merged.get("arguments") or {}).get("game", []), repl
        )
        if not args and merged.get("minecraftArguments"):
            template = merged["minecraftArguments"]
            args = [self._substitute(token, repl) for token in template.split() if token]
        return args

    @staticmethod
    def _render_arguments(entries: Sequence[Any], repl: Dict[str, str]) -> List[str]:
        """渲染 arguments 数组（支持字符串与带 rules 的对象）"""
        result: List[str] = []
        for entry in entries:
            if isinstance(entry, str):
                rendered = LauncherService._substitute(entry, repl)
                if rendered:
                    result.append(rendered)
                continue
            if not isinstance(entry, dict):
                continue
            if not LauncherService._rules_allow(entry.get("rules")):
                continue
            value = entry.get("value")
            values = value if isinstance(value, list) else [value]
            for item in values:
                if not isinstance(item, str):
                    continue
                rendered = LauncherService._substitute(item, repl)
                if rendered:
                    result.append(rendered)
        return result

    @staticmethod
    def _substitute(text: str, repl: Dict[str, str]) -> str:
        for key, value in repl.items():
            text = text.replace("${" + key + "}", value)
        return text

    @staticmethod
    def _rules_allow(rules: Optional[List[Dict[str, Any]]]) -> bool:
        if not rules:
            return True
        allowed = False
        for rule in rules:
            os_rule = rule.get("os") or {}
            if os_rule and os_rule.get("name") != "windows":
                continue
            if os_rule.get("arch") and os_rule.get("arch") not in ("x86_64", "amd64"):
                continue
            allowed = rule.get("action", "allow") == "allow"
        return allowed

    # ------------------------------------------------------------------
    # 启动
    # ------------------------------------------------------------------
    async def launch(self, options: LaunchOptions) -> int:
        """构建命令并启动，返回 PID"""
        cfg = settings_manager.get()
        if options.memory_max <= 0:
            options.memory_max = cfg.launch.memory_max
        if not options.width:
            options.width = cfg.launch.resolution_width
        if not options.height:
            options.height = cfg.launch.resolution_height

        command = await self.build_command(options)
        pid = await self._process.launch(command, cwd=get_version_dir(options.version_id))
        return pid

    async def launch_with_account(self, version_id: str, account=None) -> int:
        """便捷入口：从账号对象生成选项"""
        cfg = settings_manager.get()
        if isinstance(account, MicrosoftAccount):
            options = LaunchOptions(
                version_id=version_id,
                username=account.username,
                uuid=(account.mc_selected_profile or "").replace("-", ""),
                access_token=account.mc_access_token or "0",
                user_type="msa",
                memory_min=cfg.launch.memory_min,
                memory_max=cfg.launch.memory_max,
                jvm_args=list(cfg.launch.jvm_args),
            )
        else:
            name = getattr(account, "username", "Player") if account else "Player"
            options = LaunchOptions(
                version_id=version_id,
                username=name,
                uuid=self.offline_uuid(name),
                memory_min=cfg.launch.memory_min,
                memory_max=cfg.launch.memory_max,
                jvm_args=list(cfg.launch.jvm_args),
            )
        return await self.launch(options)

    @staticmethod
    def offline_uuid(username: str) -> str:
        """离线模式 UUID：md5("OfflinePlayer:" + name)"""
        digest = hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).hexdigest()
        return str(uuid.UUID(digest))


__all__ = ["LauncherService", "LaunchOptions"]
