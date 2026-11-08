"""应用层 - 启动服务（构建命令并启动游戏）"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import uuid as uuid_lib
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher import __version__ as LAUNCHER_VERSION
from vein_launcher.application.services.game_registry import game_registry
from vein_launcher.application.services.version_service import VersionService
from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.exceptions import GameLaunchError, JavaNotFoundError
from vein_launcher.common.utils.path_utils import (
    ensure_dir,
    get_assets_dir,
    get_libraries_dir,
    get_version_dir,
    resolve_version_dir,
)
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
        # 多实例：每次启动一个独立 GameProcess，按 pid 跟踪，互不覆盖
        self._processes: Dict[int, GameProcess] = {}
        # 原版 agent：每个实例一个端口
        self._agent_ports: Dict[int, int] = {}
        self._pending_agent_ports: list[int] = []
        self._reserved_agent_ports: set[int] = set()
        if process is not None:
            pid = process.pid
            if pid:
                self._processes[pid] = process

    @property
    def process(self) -> GameProcess:
        return self._process

    def _free_agent_port(self, start: int = 25566, end: int = 25600) -> int:
        """从 start 开始找一个没被占用、也没被预留的本地端口，并预留它"""
        import socket

        for port in range(start, end):
            if port in self._reserved_agent_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    probe.bind(("127.0.0.1", port))
                except OSError:
                    continue
            self._reserved_agent_ports.add(port)
            return port
        return start

    def agent_port(self, pid: Optional[int] = None) -> int:
        """返回某个实例（默认最近启动且仍在运行）的 agent 端口，拿不到就返回 0"""
        alive = {p: port for p, port in self._agent_ports.items() if p in self.running_processes}
        self._agent_ports = alive
        if pid:
            return alive.get(int(pid), 0)
        if not alive:
            return 0
        return alive[max(alive)]

    def forget_agent_port(self, pid: int) -> None:
        self._agent_ports.pop(int(pid), None)

    @property
    def running_processes(self) -> Dict[int, GameProcess]:
        alive = {pid: proc for pid, proc in self._processes.items() if proc.running}
        self._processes = alive
        return dict(alive)

    # ------------------------------------------------------------------
    async def build_command(
        self,
        version_id: str,
        username: str = "Player",
        java: Optional[JavaRuntime] = None,
        java_path: Optional[str] = None,
        access_token: Optional[str] = None,
        auth_uuid: Optional[str] = None,
        user_type: str = "legacy",
        extra_jvm: Optional[List[str]] = None,
    ) -> List[str]:
        merged = await self._versions.merged(version_id)
        cfg = settings_manager.get()

        if java is None and java_path is None:
            required = int((merged.get("javaVersion") or {}).get("majorVersion", 8))
            runtimes = await self._detector.detect()
            java = await self._detector.select(required, runtimes)
            if java is None:
                raise JavaNotFoundError(f"未找到 Java {required}+")

        version_dir = resolve_version_dir(version_id)
        natives_dir = ensure_dir(version_dir / "natives")
        self._extract_natives(merged, natives_dir)

        classpath = self._classpath(merged, version_id)
        if not self._jar_chain(version_id):
            # 没有客户端 jar 时 Java 只会报 ClassNotFoundException，提前给出可行动的提示
            jar = resolve_version_dir(version_id) / f"{version_id}.jar"
            partial = jar.with_suffix(jar.suffix + ".part")
            if partial.exists():
                raise GameLaunchError(
                    f"Client jar is incomplete: {partial.name} "
                    f"({partial.stat().st_size} bytes). Re-download the version to finish it."
                )
            raise GameLaunchError(
                f"Client jar missing: {jar}. Re-download {version_id} before launching."
            )
        replacements = {
            "auth_player_name": username,
            "version_name": version_id,
            "game_directory": str(version_dir),
            "assets_root": str(get_assets_dir()),
            "assets_index_name": str((merged.get("assetIndex") or {}).get("id", "legacy")),
            "auth_uuid": (auth_uuid or self.offline_uuid(username)),
            "auth_access_token": (access_token or "0"),
            "user_type": user_type,
            "version_type": merged.get("type", "release"),
            "natives_directory": str(natives_dir),
            "classpath": classpath,
            "library_directory": str(get_libraries_dir()),
            "launcher_name": "vein_launcher",
            "launcher_version": LAUNCHER_VERSION,
            "resolution_width": str(cfg.launch.resolution_width),
            "resolution_height": str(cfg.launch.resolution_height),
        }

        jvm_args = self._render((merged.get("arguments") or {}).get("jvm", []), replacements)
        game_args = self._render((merged.get("arguments") or {}).get("game", []), replacements)

        # ≤1.12.2 的版本 JSON 只有 minecraftArguments 字符串（没有 arguments 对象）
        legacy_arguments = merged.get("minecraftArguments")
        if not game_args and isinstance(legacy_arguments, str) and legacy_arguments.strip():
            game_args = self._render(legacy_arguments.split(), replacements)
            if not jvm_args:
                # 老版本没有 arguments.jvm，原生库目录只能由 java.library.path 传入
                jvm_args = [f"-Djava.library.path={natives_dir}"]

        java_bin = java_path or (str(java.path) if java else "")
        # 原版（无加载器）实例：挂 MLC agent，启动器可直连读取游戏状态
        agent_flags: List[str] = []
        lower_id = str(version_id).lower()
        if not any(key in lower_id for key in ("fabric", "forge", "quilt", "neoforge")):
            from vein_launcher.common.utils.path_utils import get_root_dir

            agent_jar = get_root_dir() / "agent" / f"vein-agent-{version_id}.jar"
            if agent_jar.is_file():
                port = self._free_agent_port()
                self._pending_agent_ports.append(port)
                agent_flags = [f"-javaagent:{agent_jar}", f"-Dvein.agent.port={port}"]
                logger.info("挂载原版 MLC agent：%s（端口 %s）", agent_jar.name, port)

        command = [
            java_bin,
            f"-Xms{cfg.launch.memory_min}M",
            f"-Xmx{cfg.launch.memory_max}M",
            *cfg.launch.jvm_args,
            *jvm_args,
            *(extra_jvm or []),
            *agent_flags,
        ]
        has_cp = any(arg in ("-cp", "-classpath") for arg in jvm_args)
        if not has_cp:
            command += ["-cp", classpath]
        command.append(merged.get("mainClass", "net.minecraft.client.main.Main"))
        command += game_args
        return command

    async def launch(
        self,
        version_id: str,
        username: str = "Player",
        java_path: Optional[str] = None,
        access_token: Optional[str] = None,
        auth_uuid: Optional[str] = None,
        user_type: str = "legacy",
        extra_jvm: Optional[List[str]] = None,
    ) -> int:
        command = await self.build_command(
            version_id,
            username,
            java_path=java_path,
            access_token=access_token,
            auth_uuid=auth_uuid,
            user_type=user_type,
            extra_jvm=extra_jvm,
        )
        cwd = resolve_version_dir(version_id)
        # 速查窗会短暂抢焦点：关掉「失焦暂停」，浏览指令时游戏不会被打断
        self._ensure_no_pause_on_focus_loss(cwd)
        # 多实例：第一个实例复用注入的 process（测试/兼容），之后每次新建
        reuse = (
            self._process is not None
            and not getattr(self._process, "running", False)
            and not self._processes
        )
        process = self._process if reuse else GameProcess()
        pid = await process.launch(command, cwd=cwd)
        self._process = process
        if isinstance(process, GameProcess):
            self._processes[pid] = process
            if self._pending_agent_ports:
                port = self._pending_agent_ports.pop(0)
                self._agent_ports[pid] = port
                self._reserved_agent_ports.discard(port)
            game_registry.register(pid, version_id, str(cwd), command)
            asyncio.create_task(self._watch(pid, process))
        return pid

    @staticmethod
    def _ensure_no_pause_on_focus_loss(cwd: Path) -> None:
        """把 options.txt 里的 pauseOnLostFocus 改成 false（游戏失焦不暂停）"""
        options = cwd / "options.txt"
        if not options.is_file():
            return
        try:
            lines = options.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            kept = [
                line for line in lines if not line.strip().startswith("pauseOnLostFocus:")
            ]
            if len(kept) < len(lines) and any(
                line.strip() == "pauseOnLostFocus:false" for line in lines
            ):
                return
            kept.append("pauseOnLostFocus:false")
            options.write_text("\n".join(kept) + "\n", encoding="utf-8")
            logger.info("已关闭失焦暂停：%s", options)
        except OSError:
            logger.debug("写入 pauseOnLostFocus 失败", exc_info=True)

    async def _watch(self, pid: int, process: GameProcess) -> None:
        """进程结束后自动从登记表与多实例表里移除"""
        try:
            await process.wait()
        except asyncio.CancelledError:
            raise
        except Exception:  # 监听失败不应影响启动
            logger.exception("等待游戏进程结束失败：pid=%s", pid)
        finally:
            game_registry.unregister(pid)
            self._processes.pop(pid, None)
            self.forget_agent_port(pid)

    # ------------------------------------------------------------------
    def _jar_chain(self, version_id: str) -> List[Path]:
        """沿 inheritsFrom 收集每一层的 client jar（加载器实例需要父版本 jar）"""
        jars: List[Path] = []
        seen = set()
        current = version_id
        while current and current not in seen:
            seen.add(current)
            jar = resolve_version_dir(current) / f"{current}.jar"
            if jar.is_file():
                jars.append(jar)
            meta = resolve_version_dir(current) / f"{current}.json"
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
                text = substitute(entry)
                if "${" in text:  # 未能解析的占位符（如 quickPlay 系列）直接丢弃
                    continue
                result.append(text)
                continue
            if not isinstance(entry, dict):
                continue
            rules = entry.get("rules")
            if rules and not LauncherService._rules_allow(rules):
                continue
            value = entry.get("value")
            for item in (value if isinstance(value, list) else [value]):
                if isinstance(item, str):
                    text = substitute(item)
                    if "${" in text:
                        continue
                    result.append(text)

        # 清理：demo / quickPlay 参数及其悬空值（我们不支持这些入口）
        cleaned: List[str] = []
        skip_next = False
        for token in result:
            if skip_next:
                skip_next = False
                if not token.startswith("--"):
                    continue
            if token == "--demo":
                continue
            if token.startswith("--quickPlay"):
                skip_next = True
                continue
            cleaned.append(token)
        return cleaned

    @staticmethod
    def _rules_allow(rules: Optional[List[Dict[str, Any]]]) -> bool:
        if not rules:
            return True
        # 我们支持的 feature：自定义分辨率；其余（demo/quickPlay）一律视为不满足
        supported = {
            "has_custom_resolution": True,
            "is_demo_user": False,
            "has_quick_plays_support": False,
            "is_quick_play_singleplayer": False,
            "is_quick_play_multiplayer": False,
            "is_quick_play_realms": False,
        }
        allowed = False
        for rule in rules:
            os_rule = rule.get("os") or {}
            if os_rule and os_rule.get("name") not in (None, "windows"):
                continue
            features = rule.get("features") or {}
            if any(bool(value) != bool(supported.get(name, False)) for name, value in features.items()):
                continue
            allowed = rule.get("action", "allow") == "allow"
        return allowed

    @staticmethod
    def offline_uuid(username: str) -> str:
        return str(uuid_lib.UUID(hashlib.md5(f"OfflinePlayer:{username}".encode()).hexdigest()))


__all__ = ["LauncherService"]
