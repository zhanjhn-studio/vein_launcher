"""游戏运行登记表：既记录「本启动器启动的进程」，也能发现外部启动的 Minecraft。

用途：
    - 启动器重启后仍能看出有哪些游戏在跑（按进程命令行识别）
    - 允许同时开多个实例（每个进程单独登记）
    - 界面「运行中的游戏」列表 / 结束进程

识别规则：java 进程命令行里出现 `net.minecraft.client.main.Main` 或
`-Dminecraft.launcher.brand`；版本号取 `--version <id>`，目录取 `--gameDir <dir>`。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MINECRAFT_MARKERS = (
    "net.minecraft.client.main.Main",
    "-Dminecraft.launcher.brand",
    "net.fabricmc.loader.impl.launch",
    "cpw.mods.bootstraplauncher",
    "org.quiltmc.loader.impl.launch",
)


@dataclass
class RunningGame:
    pid: int
    version_id: str = "unknown"
    source: str = "external"  # launcher | external
    started_at: Optional[float] = None
    memory_mb: Optional[int] = None
    title: Optional[str] = None
    game_dir: Optional[str] = None
    command: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "version_id": self.version_id,
            "source": self.source,
            "started_at": self.started_at,
            "uptime": int(time.time() - self.started_at) if self.started_at else None,
            "memory_mb": self.memory_mb,
            "title": self.title,
            "game_dir": self.game_dir,
        }


def _arg_value(args: List[str], flag: str) -> Optional[str]:
    for index, item in enumerate(args):
        if item == flag and index + 1 < len(args):
            return args[index + 1]
        if item.startswith(flag + "="):
            return item.split("=", 1)[1]
    return None


class GameRegistry:
    """进程登记 + 外部进程探测（psutil 不可用时退化为只登记）"""

    def __init__(self) -> None:
        self._registered: Dict[int, RunningGame] = {}

    # ------------------------------------------------------------------ 登记
    def register(self, pid: int, version_id: str, game_dir: Optional[str] = None, command: Optional[List[str]] = None) -> None:
        self._registered[int(pid)] = RunningGame(
            pid=int(pid),
            version_id=version_id,
            source="launcher",
            started_at=time.time(),
            game_dir=game_dir,
            command=list(command or []),
        )
        logger.info("登记游戏进程：pid=%s version=%s", pid, version_id)

    def unregister(self, pid: int) -> None:
        if self._registered.pop(int(pid), None) is not None:
            logger.info("移除游戏进程登记：pid=%s", pid)

    # ------------------------------------------------------------------ 查询
    def list(self) -> List[Dict[str, Any]]:
        """登记的 + 外部发现的，按 pid 去重，去掉已退出的"""
        try:
            import psutil
        except ImportError:  # 没装 psutil 时只返回登记过的
            return [game.to_dict() for game in self._registered.values()]

        games: Dict[int, RunningGame] = {}
        for pid, game in list(self._registered.items()):
            try:
                process = psutil.Process(pid)
                if not process.is_running():
                    raise psutil.NoSuchProcess(pid)
                game.memory_mb = int(process.memory_info().rss / 1024 / 1024)
                try:
                    game.title = process.name()
                except psutil.Error:
                    game.title = None
                games[pid] = game
            except psutil.Error:
                self._registered.pop(pid, None)

        for process in psutil.process_iter(["pid", "name", "cmdline", "create_time", "memory_info"]):
            try:
                info = process.info
                name = (info.get("name") or "").lower()
                if name not in {"java.exe", "javaw.exe", "java", "javaw"}:
                    continue
                args = info.get("cmdline") or []
                joined = " ".join(args)
                if not any(marker in joined for marker in MINECRAFT_MARKERS):
                    continue
                pid = int(info["pid"])
                if pid in games:
                    continue
                version = _arg_value(args, "--version") or "unknown"
                games[pid] = RunningGame(
                    pid=pid,
                    version_id=version,
                    source="launcher" if pid in self._registered else "external",
                    started_at=info.get("create_time"),
                    memory_mb=int((info.get("memory_info") or process.memory_info()).rss / 1024 / 1024),
                    title="Minecraft",
                    game_dir=_arg_value(args, "--gameDir"),
                    command=args,
                )
            except (psutil.Error, ValueError):
                continue

        return sorted((game.to_dict() for game in games.values()), key=lambda item: item.get("started_at") or 0)

    def is_running(self, pid: int) -> bool:
        try:
            import psutil

            return psutil.pid_exists(int(pid))
        except ImportError:
            return int(pid) in self._registered

    def running_count(self) -> int:
        return len(self.list())

    # ------------------------------------------------------------------ 结束
    def kill(self, pid: int, timeout: float = 8.0) -> Dict[str, Any]:
        try:
            import psutil
        except ImportError as exc:
            raise RuntimeError("psutil 未安装，无法结束进程") from exc

        try:
            process = psutil.Process(int(pid))
        except psutil.Error as exc:
            self.unregister(int(pid))
            raise RuntimeError(f"进程不存在：{pid}") from exc

        try:
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        finally:
            self.unregister(int(pid))
        return {"pid": int(pid), "killed": True}


game_registry = GameRegistry()

__all__ = ["GameRegistry", "RunningGame", "game_registry", "MINECRAFT_MARKERS"]
