"""应用层 - 启动服务（构建命令并启动游戏）"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid as uuid_lib
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.application.services.version_service import VersionService
from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.exceptions import GameLaunchError, JavaNotFoundError
from vein_launcher.common.utils.path_utils import ensure_dir, get_assets_dir, get_libraries_dir, get_version_dir
from vein_launcher.infrastructure.process.game_process import GameProcess
from vein_launcher.infrastructure.process.java_detector import JavaDetector, JavaRuntime

logger = logging.getLogger(__name__)


class LauncherService:
    """把版本 JSON + 账号 + 配置翻译成命令行并执行"""

    def __init__(
        self,
        versions: VersionService,
        detector: Optional[JavaDetector] = None,
        process: Optional[GameProcess] = None,
    ):
        self._versions = versions
        self._detector = detector or JavaDetector()
        self._process = process or GameProcess()

    @property
    def process(self) -> GameProcess:
        return self._process

    # ------------------------------------------------------------------
    async def build_command(
        self,
        version_id: str,
        username: str = "Player",
        java: Optional[JavaRuntime] = None,
    ) -> List[str]:
        merged = await self._versions.merged(version_id)
        cfg = settings_manager.get()

        if java is None:
            required = int((merged.get("javaVersion") or {}).get("majorVersion", 8))
            runtimes = await self._detector.detect()
            java = await self._detector.select(required, runtimes)
            if java is None:
                raise JavaNotFoundError(f"未找到 Java {required}+")

        version_dir = get_version_dir(version_id)
        natives_dir = ensure_dir(version_dir / "natives")
        self._extract_natives(merged, natives_dir)

        classpath = self._classpath(merged, version_id)
        replacements = {
            "auth_player_name": username,
            "version_name": version_id,
            "game_directory": str(version_dir),
            "assets_root": str(get_assets_dir()),
            "assets_index_name": str((merged.get("assetIndex") or {}).get("id", "legacy")),
            "auth_uuid": self.offline_uuid(username),
            "auth_access_token": "0",
            "user_type": "legacy",
            "version_type": merged.get("type", "release"),
            "natives_directory": str(natives_dir),
            "classpath": classpath,
            "library_directory": str(get_libraries_dir()),
            "launcher_name": "vein_launcher",
            "launcher_version": "0.0.1",
            "resolution_width": str(cfg.launch.resolution_width),
            "resolution_height": str(cfg.launch.resolution_height),
        }

        jvm_args = self._render((merged.get("arguments") or {}).get("jvm", []), replacements)
        game_args = self._render((merged.get("arguments") or {}).get("game", []), replacements)

        command = [
            str(java.path),
            f"-Xms{cfg.launch.memory_min}M",
            f"-Xmx{cfg.launch.memory_max}M",
            *cfg.launch.jvm_args,
            *jvm_args,
        ]
        has_cp = any(arg in ("-cp", "-classpath") for arg in jvm_args)
        if not has_cp:
            command += ["-cp", classpath]
        command.append(merged.get("mainClass", "net.minecraft.client.main.Main"))
        command += game_args
        return command

    async def launch(self, version_id: str, username: str = "Player") -> int:
        command = await self.build_command(version_id, username)
        return await self._process.launch(command, cwd=get_version_dir(version_id))

    # ------------------------------------------------------------------
    def _jar_chain(self, version_id: str) -> List[Path]:
        """沿 inheritsFrom 收集每一层的 client jar（加载器实例需要父版本 jar）"""
        jars: List[Path] = []
        seen = set()
        current = version_id
        while current and current not in seen:
            seen.add(current)
            jar = get_version_dir(current) / f"{current}.jar"
            if jar.is_file():
                jars.append(jar)
            meta = get_version_dir(current) / f"{current}.json"
            if not meta.is_file():
                break
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                break
            current = data.get("inheritsFrom")
        return jars

    def _classpath(self, merged: Dict[str, Any], version_id: str) -> str:
        entries: List[str] = []
        for jar in self._jar_chain(version_id):
            entries.append(str(jar))
        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue
            artifact = (lib.get("downloads") or {}).get("artifact")
            if artifact and artifact.get("path"):
                jar = get_libraries_dir() / artifact["path"]
                if jar.is_file():
                    entries.append(str(jar))
        return os.pathsep.join(entries)

    def _extract_natives(self, merged: Dict[str, Any], target: Path) -> None:
        for lib in merged.get("libraries", []):
            if not self._rules_allow(lib.get("rules")):
                continue
            classifier = ((lib.get("natives") or {}).get("windows"))
            if not classifier:
                continue
            key = classifier.replace("${arch}", "64")
            artifact = ((lib.get("downloads") or {}).get("classifiers") or {}).get(key)
            if not artifact or not artifact.get("path"):
                continue
            jar = get_libraries_dir() / artifact["path"]
            if not jar.is_file():
                continue
            try:
                with zipfile.ZipFile(jar) as zf:
                    for member in zf.namelist():
                        if member.startswith("META-INF/") or member.endswith("/"):
                            continue
                        zf.extract(member, target)
            except (zipfile.BadZipFile, OSError) as exc:
                logger.warning("natives 解压失败 %s：%s", jar, exc)

    @staticmethod
    def _render(entries: List[Any], repl: Dict[str, str]) -> List[str]:
        result: List[str] = []

        def substitute(text: str) -> str:
            for key, value in repl.items():
                text = text.replace("${" + key + "}", value)
            return text

        for entry in entries:
            if isinstance(entry, str):
                result.append(substitute(entry))
                continue
            if not isinstance(entry, dict):
                continue
            rules = entry.get("rules")
            if rules and not LauncherService._rules_allow(rules):
                continue
            value = entry.get("value")
            for item in (value if isinstance(value, list) else [value]):
                if isinstance(item, str):
                    result.append(substitute(item))
        return result

    @staticmethod
    def _rules_allow(rules: Optional[List[Dict[str, Any]]]) -> bool:
        if not rules:
            return True
        allowed = False
        for rule in rules:
            os_rule = rule.get("os") or {}
            if os_rule and os_rule.get("name") not in (None, "windows"):
                continue
            allowed = rule.get("action", "allow") == "allow"
        return allowed

    @staticmethod
    def offline_uuid(username: str) -> str:
        return str(uuid_lib.UUID(hashlib.md5(f"OfflinePlayer:{username}".encode()).hexdigest()))


__all__ = ["LauncherService"]
