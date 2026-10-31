"""MC2 世界数据：定位存档、读取种子与基础信息

能力边界（诚实标注）：
- 已实现：存档定位、level.dat 解析（种子/版本/游戏模式/时间）、世界列表
- 未实现：群系与结构扫描（需要解析 region/*.mca，属后续迭代）
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.common.utils.path_utils import get_version_dir
from vein_launcher.infrastructure.mc2 import nbt, region

logger = logging.getLogger(__name__)


class WorldScanner:
    def __init__(self, instances_root: Path):
        self._root = instances_root

    # ------------------------------------------------------------------
    def list_worlds(self, instance: Optional[str] = None) -> List[Dict[str, Any]]:
        worlds: List[Dict[str, Any]] = []
        if not self._root.is_dir():
            return worlds
        for inst in sorted(self._root.iterdir()):
            if not inst.is_dir():
                continue
            if instance and inst.name != instance:
                continue
            saves = inst / "saves"
            if not saves.is_dir():
                continue
            for world in sorted(saves.iterdir()):
                if world.is_dir():
                    info = self.read_world(inst.name, world)
                    if info:
                        worlds.append(info)
        return worlds

    def read_world(self, instance: str, world_dir: Path) -> Optional[Dict[str, Any]]:
        level = world_dir / "level.dat"
        if not level.is_file():
            return None
        try:
            _, data = nbt.load(level)
        except Exception as exc:  # 损坏或非 NBT
            logger.warning("level.dat 解析失败 %s：%s", level, exc)
            return None
        level_data = data.get("Data", data) if isinstance(data, dict) else {}
        version = level_data.get("Version") or {}
        worldgen = level_data.get("WorldGenSettings") or {}
        # 1.13+ 种子存在 WorldGenSettings.seed；旧版存 RandomSeed
        seed = level_data.get("RandomSeed")
        if seed in (None, 0):
            seed = worldgen.get("seed", 0)
        difficulty = level_data.get("Difficulty")
        if isinstance(difficulty, bytes):
            difficulty = int.from_bytes(difficulty, "big")
        return {
            "instance": instance,
            "name": level_data.get("LevelName", world_dir.name),
            "folder": world_dir.name,
            "path": str(world_dir),
            "seed": int(seed or 0),
            "version": version.get("Name", ""),
            "game_type": level_data.get("GameType", -1),
            "difficulty": difficulty,
            "hardcore": bool(level_data.get("hardcore", 0)),
            "last_played": level_data.get("LastPlayed", 0),
            "day_time": level_data.get("DayTime", 0),
            "spawn": [
                level_data.get("SpawnX", 0),
                level_data.get("SpawnY", 0),
                level_data.get("SpawnZ", 0),
            ],
            "biomes": None,
            "structures": None,
            "note": "level.dat parsed; biome/structure from region scan",
        }

    def scan(self, instance: str, folder: str) -> Dict[str, Any]:
        """扫描指定存档的群系与结构（region/*.mca）"""
        world_dir = self._root / instance / "saves" / folder
        if not world_dir.is_dir():
            raise FileNotFoundError(f"存档不存在：{world_dir}")
        detail = region.scan_world(world_dir)
        base = self.read_world(instance, world_dir) or {}
        return {**base, "scan": detail}

    # ------------------------------------------------------------------
    def instance_names(self) -> List[str]:
        if not self._root.is_dir():
            return []
        return sorted(p.name for p in self._root.iterdir() if p.is_dir())


__all__ = ["WorldScanner"]
