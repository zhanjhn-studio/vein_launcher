"""MLC 服务

接口（与插件宿主共享）：
    mlc.launch            启动游戏
    mlc.world.create      创建世界（当前仅创建存档目录）
    mlc.world.info        列出存档信息
    mlc.player.info       玩家数据（需要游戏侧 mod 配合，当前 unsupported）
    mlc.event.subscribe   订阅事件（日志 / 退出 / 下载进度）
    mlc.mod.load          加载模组（当前返回 unsupported）
    mlc.plugin.search     搜索已安装插件
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir

logger = logging.getLogger(__name__)

# MLC 事件 -> 启动器事件
EVENT_MAP = {
    "game.log": EventNames.GAME_LOG_UPDATE,
    "game.exit": EventNames.GAME_EXITED,
    "download.progress": EventNames.DOWNLOAD_TASK_PROGRESS,
}

UNSUPPORTED = {"supported": False, "reason": "需要游戏侧 mod 协作，尚未实现"}


class MlcService:
    """游戏控制层"""

    def __init__(self, launcher, plugins_dir: Optional[Path] = None):
        self._launcher = launcher
        self._plugins_dir = plugins_dir
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._installed = False

    # ------------------------------------------------------------------
    def install_bridge(self) -> None:
        """把启动器事件桥接到 MLC 订阅者"""
        if self._installed:
            return
        self._installed = True
        for topic, event_name in EVENT_MAP.items():
            event_bus.subscribe(event_name, self._make_forwarder(topic))

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

    # ------------------------------------------------------------------
    async def launch(self, version_id: str, username: str = "Player") -> Dict[str, Any]:
        pid = await self._launcher.launch(version_id, username)
        return {"pid": pid, "version_id": version_id}

    def world_create(self, version_id: str, name: str) -> Dict[str, Any]:
        """创建存档目录（真正的世界生成仍需游戏内完成）"""
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "New World"
        target = ensure_dir(get_version_dir(version_id) / "saves" / safe)
        return {"path": str(target), "name": safe, "generated": False}

    def world_info(self, version_id: str) -> Dict[str, Any]:
        saves = get_version_dir(version_id) / "saves"
        if not saves.is_dir():
            return {"worlds": []}
        worlds = []
        for child in sorted(saves.iterdir()):
            if not child.is_dir():
                continue
            worlds.append(
                {
                    "name": child.name,
                    "path": str(child),
                    "mtime": child.stat().st_mtime,
                }
            )
        return {"worlds": worlds}

    def player_info(self) -> Dict[str, Any]:
        return dict(UNSUPPORTED)

    def mod_load(self, *_: Any) -> Dict[str, Any]:
        return dict(UNSUPPORTED)

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


__all__ = ["MlcService", "EVENT_MAP"]
