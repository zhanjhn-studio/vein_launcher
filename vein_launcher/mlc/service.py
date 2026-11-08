"""MLC 服务（游戏控制层）

接口（RPC 与插件宿主共用）：
    mlc.state             运行状态（running / pid / version / exit_code）
    mlc.launch            启动游戏
    mlc.worlds            存档列表（含 level.dat 摘要与玩家数据是否存在）
    mlc.world.create      预留存档目录（真正的世界生成仍需游戏内完成）
    mlc.world.detail      单个存档详情（种子、难度、游戏模式、游玩时长）
    mlc.player            玩家数据（从 playerdata/*.dat 的 NBT 读取）
    mlc.mod.load          把 jar 装入实例 mods 目录
    mlc.plugin.search     搜索已安装插件
    mlc.event.subscribe   事件订阅（日志 / 退出 / 下载进度）

设计说明：
    「玩家数据 / 世界详情」不需要游戏侧 mod —— Minecraft 自己会把它们写成 NBT 文件，
    这里直接解析，所以离线也能给出真实数值。
"""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.utils.path_utils import (
    ensure_dir,
    get_instance_root,
    get_version_dir,
)
from vein_launcher.infrastructure.mc2 import nbt

logger = logging.getLogger(__name__)

# MLC 事件 -> 启动器事件
EVENT_MAP = {
    "game.log": EventNames.GAME_LOG_UPDATE,
    "game.exit": EventNames.GAME_EXITED,
    "download.progress": EventNames.DOWNLOAD_TASK_PROGRESS,
}

# 只允许装模组的扩展名，避免把任意文件塞进 mods
MOD_SUFFIXES = {".jar", ".zip", ".disabled"}


class MlcError(Exception):
    """MLC 调用失败（参数不合法 / 文件缺失）"""


class MlcService:
    """游戏控制层"""

    def __init__(self, launcher, plugins_dir: Optional[Path] = None):
        self._launcher = launcher
        self._plugins_dir = plugins_dir
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._installed = False
        self._started_at: Optional[float] = None
        self._exit_code: Optional[int] = None
        self._last_version: Optional[str] = None

    # ------------------------------------------------------------------ 开关
    @property
    def enabled(self) -> bool:
        """MLC 总开关：关闭时所有数据类接口拒绝服务"""
        try:
            from vein_launcher.common.config.settings import settings_manager

            return bool(settings_manager.get().mlc.enabled)
        except Exception:  # 配置未就绪时按关闭处理
            return False

    def set_enabled(self, value: bool) -> Dict[str, Any]:
        from vein_launcher.common.config.settings import settings_manager

        settings = settings_manager.get()
        settings.mlc.enabled = bool(value)
        settings_manager.save()
        logger.info("MLC 总开关：%s", "on" if value else "off")
        return {"enabled": bool(value)}

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise MlcError("MLC 总开关未开启：请先到 MLC 页打开总开关（MLC is turned off）")

    # ------------------------------------------------------------------ 事件桥
    def install_bridge(self) -> None:
        """把启动器事件桥接到 MLC 订阅者"""
        if self._installed:
            return
        self._installed = True
        for topic, event_name in EVENT_MAP.items():
            event_bus.subscribe(event_name, self._make_forwarder(topic))
        event_bus.subscribe(EventNames.GAME_RUNNING, self._on_game_running)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)

    def _on_game_running(self, pid: int = 0, **_: Any) -> None:
        self._started_at = time.time()
        self._exit_code = None

    def _on_game_exited(self, exit_code: int = 0, **_: Any) -> None:
        self._exit_code = int(exit_code or 0)

    def _make_forwarder(self, topic: str):
        def forward(**payload: Any) -> None:
            for callback in list(self._subscribers.get(topic, [])):
                try:
                    callback({"topic": topic, "data": payload})
                except Exception:  # 订阅者异常不影响其它订阅者
                    logger.exception("MLC 事件回调失败：%s", topic)

        return forward

    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.setdefault(topic, []).append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        handlers = self._subscribers.get(topic) or []
        if callback in handlers:
            handlers.remove(callback)

    # ------------------------------------------------------------------ 状态
    def state(self) -> Dict[str, Any]:
        process = getattr(self._launcher, "_process", None)
        running = bool(getattr(process, "running", False))
        inner = getattr(process, "_process", None)
        pid = getattr(inner, "pid", None) if running else None
        uptime = None
        if running and self._started_at:
            uptime = int(time.time() - self._started_at)
        return {
            "enabled": self.enabled,
            "running": running,
            "pid": pid,
            "exit_code": self._exit_code,
            "uptime": uptime,
            "version_id": self._last_version,
        }

    # ------------------------------------------------------------------ 启动
    async def launch(self, version_id: str, username: str = "Player") -> Dict[str, Any]:
        self._require_enabled()
        self._last_version = str(version_id)
        pid = await self._launcher.launch(version_id, username)
        return {"pid": pid, "version_id": version_id}

    # ------------------------------------------------------------------ 存档
    def _resolve_version(self, version_id: str) -> str:
        """没指定版本时，用最近改动过的实例，插件/界面就不用先知道版本号"""
        if version_id:
            return version_id
        if self._last_version:
            return self._last_version
        root = get_instance_root()
        if not root.is_dir():
            return version_id
        candidates = [d for d in root.iterdir() if d.is_dir()]
        if not candidates:
            return version_id
        newest = max(candidates, key=lambda d: d.stat().st_mtime)
        return newest.name

    def _saves_dir(self, version_id: str) -> Path:
        return get_version_dir(self._resolve_version(version_id)) / "saves"

    def world_create(self, version_id: str, name: str) -> Dict[str, Any]:
        """创建存档目录（真正的世界生成仍需游戏内完成）"""
        self._require_enabled()
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "New World"
        target = ensure_dir(self._saves_dir(version_id) / safe)
        return {"path": str(target), "name": safe, "generated": False}

    def world_info(self, version_id: str) -> Dict[str, Any]:
        self._require_enabled()
        saves = self._saves_dir(version_id)
        if not saves.is_dir():
            return {"worlds": []}

        worlds: List[Dict[str, Any]] = []
        for child in sorted(saves.iterdir()):
            if not child.is_dir():
                continue
            try:
                stat = child.stat()
            except OSError:
                continue
            summary: Dict[str, Any] = {
                "name": child.name,
                "path": str(child),
                "mtime": stat.st_mtime,
                "size": _dir_size(child),
            }
            level = child / "level.dat"
            if level.is_file():
                try:
                    summary["level"] = _read_level(level)
                except (OSError, ValueError) as exc:
                    summary["level_error"] = str(exc)
            players = list((child / "playerdata").glob("*.dat")) if (child / "playerdata").is_dir() else []
            summary["players"] = len(players)
            worlds.append(summary)

        # 最近玩过（有玩家数据）的存档排在前面
        worlds.sort(key=lambda w: (w.get("players", 0), w.get("mtime", 0)), reverse=True)
        return {"worlds": worlds}

    def world_detail(self, version_id: str, world: str) -> Dict[str, Any]:
        self._require_enabled()
        target = self._saves_dir(version_id) / _safe_name(world)
        if not target.is_dir():
            raise MlcError(f"world not found: {world}")
        level = target / "level.dat"
        data: Dict[str, Any] = {"name": target.name, "path": str(target)}
        if level.is_file():
            data["level"] = _read_level(level)
        data["player"] = self.player_info(version_id, world)
        return data

    # ------------------------------------------------------------------ 原版 agent
    async def _agent_call(self, payload: dict, port: int = 25566, timeout: float = 2.0) -> dict:
        import asyncio
        import json

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", int(port)), timeout=timeout
            )
        except (OSError, asyncio.TimeoutError) as exc:
            raise MlcError(f"MLC agent not reachable on port {port}") from exc
        try:
            writer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            await writer.drain()
            line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        if not line:
            raise MlcError("MLC agent closed the connection")
        return json.loads(line.decode("utf-8", errors="replace"))

    def _resolve_agent_port(self, port: int) -> int:
        if port:
            return int(port)
        resolver = getattr(self._launcher, "agent_port", None)
        if callable(resolver):
            resolved = resolver()
            if resolved:
                return int(resolved)
        return 25566

    # ------------------------------------------------------------------ agent 事件
    AGENT_EVENTS = ("game.enter", "game.leave", "player.dimension", "player.death")

    def start_agent_watch(self, interval: float = 1.0, port: int = 0) -> None:
        """轮询 agent 状态，状态变化时发布 mlc.agent.* 事件（幂等）"""
        import asyncio

        self._require_enabled()

        if getattr(self, "_agent_watch_task", None) and not self._agent_watch_task.done():
            return
        self._agent_watch_task = asyncio.create_task(self._agent_watch_loop(interval, port))

    def stop_agent_watch(self) -> None:
        task = getattr(self, "_agent_watch_task", None)
        if task and not task.done():
            task.cancel()
        self._agent_watch_task = None

    async def _agent_watch_loop(self, interval: float, port: int) -> None:
        import asyncio

        previous: dict = {}
        while True:
            try:
                state = await self.agent_state(port)
            except Exception:
                await asyncio.sleep(max(interval, 2.0))
                continue

            events = []
            was_in = bool(previous.get("inGame"))
            now_in = bool(state.get("inGame"))
            if previous and was_in != now_in:
                events.append("game.enter" if now_in else "game.leave")
            if was_in and now_in:
                before = previous.get("player") or {}
                after = state.get("player") or {}
                if before.get("dimension") != after.get("dimension"):
                    events.append("player.dimension")
                if (before.get("health") or 0) > 0 and (after.get("health") or 0) <= 0:
                    events.append("player.death")
            for name in events:
                try:
                    event_bus.publish(f"mlc.agent.{name}", state=state)
                    logger.info("MLC agent 事件：%s", name)
                except Exception:
                    logger.exception("发布 MLC agent 事件失败：%s", name)
            if events:
                previous = state
            elif not previous:
                previous = state
            await asyncio.sleep(interval)

    async def agent_state(self, port: int = 0) -> dict:
        self._require_enabled()
        return await self._agent_call({"cmd": "state"}, self._resolve_agent_port(port))

    async def agent_chat(self, text: str, port: int = 0) -> dict:
        self._require_enabled()
        return await self._agent_call({"cmd": "chat", "text": text}, self._resolve_agent_port(port))

    # ------------------------------------------------------------------ 玩家
    def player_info(self, version_id: str, world: str = "") -> Dict[str, Any]:
        """从 playerdata/<uuid>.dat 读真实玩家数据（无需游戏侧 mod）"""
        self._require_enabled()
        saves = self._saves_dir(version_id)
        if not saves.is_dir():
            return {"supported": False, "reason": "no saves directory"}

        candidates: List[Path] = []
        if world:
            candidates = list((saves / _safe_name(world) / "playerdata").glob("*.dat"))
        else:
            for child in saves.iterdir():
                if child.is_dir():
                    candidates.extend((child / "playerdata").glob("*.dat"))
        if not candidates:
            return {
                "supported": False,
                "reason": "no player data yet — enter a world once so Minecraft writes playerdata",
            }

        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        try:
            _root, data = nbt.load(latest)
        except (OSError, ValueError) as exc:
            raise MlcError(f"cannot read player data: {exc}") from exc

        payload = data.get("player", data) if isinstance(data, dict) else {}
        pos = payload.get("Pos") or [0, 0, 0]
        inventory = payload.get("Inventory") or []
        return {
            "supported": True,
            "world": latest.parent.parent.name,
            "file": latest.name,
            "uuid": latest.stem,
            "name": payload.get("Health") is not None and latest.stem or latest.stem,
            "health": payload.get("Health"),
            "food": payload.get("foodLevel"),
            "saturation": payload.get("foodSaturationLevel"),
            "xp_level": payload.get("XpLevel"),
            "xp_progress": payload.get("XpP"),
            "game_type": payload.get("playerGameType"),
            "dimension": payload.get("Dimension"),
            "pos": [round(float(v), 1) for v in pos],
            "inventory_slots": len(inventory),
            "mtime": latest.stat().st_mtime,
        }

    # ------------------------------------------------------------------ 模组
    def mod_load(self, version_id: str, source: str) -> Dict[str, Any]:
        """把本地 jar 复制进实例 mods 目录（真正的加载仍由游戏完成）"""
        self._require_enabled()
        src = Path(source)
        if not src.is_file():
            raise MlcError(f"mod file not found: {source}")
        if src.suffix.lower() not in MOD_SUFFIXES:
            raise MlcError(f"unsupported mod type: {src.suffix}")
        target_dir = ensure_dir(get_version_dir(version_id) / "mods")
        dest = target_dir / src.name
        shutil.copy2(src, dest)
        return {"installed": str(dest), "name": dest.name, "size": dest.stat().st_size}

    # ------------------------------------------------------------------ 插件
    def plugin_search(self, keyword: str = "") -> Dict[str, Any]:
        if self._plugins_dir is None or not self._plugins_dir.is_dir():
            return {"plugins": []}
        keyword = (keyword or "").lower()
        found = []
        for child in sorted(self._plugins_dir.iterdir()):
            if not child.is_dir():
                continue
            if keyword and keyword not in child.name.lower():
                continue
            found.append({"name": child.name, "path": str(child)})
        return {"plugins": found}


# ---------------------------------------------------------------------- 工具
def _safe_name(raw: str) -> str:
    safe = "".join(c for c in raw if c not in '\\/:*?"<>|').strip()
    if not safe:
        raise MlcError("empty name")
    return safe


def _dir_size(path: Path, limit: int = 5000) -> int:
    total = 0
    for index, item in enumerate(path.rglob("*")):
        if index > limit:
            break
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def _read_level(path: Path) -> Dict[str, Any]:
    _root, data = nbt.load(path)
    level = data.get("Data", data) if isinstance(data, dict) else {}
    version = level.get("Version") or {}
    # 1.16+ 把种子挪进了 WorldGenSettings.seed，老版本在顶层 RandomSeed
    worldgen = level.get("WorldGenSettings") or {}
    seed = worldgen.get("seed") if isinstance(worldgen, dict) else None
    if seed is None:
        seed = level.get("RandomSeed")
    day_time = level.get("DayTime")
    return {
        "name": level.get("LevelName"),
        "seed": seed,
        "difficulty": level.get("Difficulty"),
        "game_type": level.get("GameType"),
        "hardcore": level.get("hardcore"),
        "last_played": level.get("LastPlayed"),
        "day": (day_time // 24000 + 1) if isinstance(day_time, int) else None,
        "version": version.get("Name") if isinstance(version, dict) else None,
    }


__all__ = ["MlcService", "MlcError", "EVENT_MAP"]
