"""MC2 区域扫描：从 region/*.mca 提取群系与结构

支持：
- 1.18+ 区块：sections[].biomes.palette
- 结构：structures.Starts.* 的 id
- 维度：region（主世界）、DIM-1/region（下界）、DIM1/region（末地）
压缩：1=gzip，2=zlib，3=不压缩。
"""

from __future__ import annotations

import gzip
import io
import logging
import zlib
from pathlib import Path
from typing import Any, Dict, List, Set

from vein_launcher.infrastructure.mc2 import nbt

logger = logging.getLogger(__name__)

DIMENSIONS = {
    "overworld": "region",
    "nether": "DIM-1/region",
    "end": "DIM1/region",
}
MAX_CHUNKS = 600  # 单维度最多解析的区块数，避免卡顿


def _decode_chunk(payload: bytes, compression: int) -> Any:
    if compression == 1:
        raw = gzip.decompress(payload)
    elif compression == 2:
        raw = zlib.decompress(payload)
    elif compression == 3:
        raw = payload
    else:
        raise ValueError(f"未知压缩类型：{compression}")
    return nbt.loads(raw)


def _biomes_of(chunk: Dict[str, Any]) -> Set[str]:
    names: Set[str] = set()
    sections = chunk.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            biomes = section.get("biomes")
            if not isinstance(biomes, dict):
                continue
            palette = biomes.get("palette")
            if isinstance(palette, list):
                for item in palette:
                    if isinstance(item, str):
                        names.add(item)
                    elif isinstance(item, dict) and isinstance(item.get("Name"), str):
                        names.add(item["Name"])
    level = chunk.get("Level")
    if isinstance(level, dict) and isinstance(level.get("Biomes"), (bytes, list)):
        names.add("legacy-biome-ids")  # 旧版本仅存数字 id，未做映射
    return names


def _structures_of(chunk: Dict[str, Any]) -> Set[str]:
    names: Set[str] = set()
    for container in (chunk.get("structures"), (chunk.get("Level") or {}).get("Structures") if isinstance(chunk.get("Level"), dict) else None):
        if not isinstance(container, dict):
            continue
        starts = container.get("Starts")
        if isinstance(starts, dict):
            names.update(str(key) for key in starts.keys())
    return names


def scan_dimension(region_dir: Path, max_chunks: int = MAX_CHUNKS) -> Dict[str, Any]:
    biomes: Set[str] = set()
    structures: Set[str] = set()
    chunks = 0
    files = sorted(region_dir.glob("*.mca"))
    for region_file in files:
        if chunks >= max_chunks:
            break
        try:
            with region_file.open("rb") as fh:
                header = fh.read(4096)
                if len(header) < 4096:
                    continue
                for slot in range(1024):
                    if chunks >= max_chunks:
                        break
                    entry = header[slot * 4: slot * 4 + 4]
                    offset = int.from_bytes(entry[:3], "big")
                    sectors = entry[3]
                    if offset == 0 or sectors == 0:
                        continue
                    fh.seek(offset * 4096)
                    length_raw = fh.read(4)
                    if len(length_raw) < 4:
                        continue
                    length = int.from_bytes(length_raw, "big")
                    if length <= 1 or length > 8 * 1024 * 1024:
                        continue
                    compression = fh.read(1)[0]
                    payload = fh.read(length - 1)
                    try:
                        chunk = _decode_chunk(payload, compression)
                    except Exception:
                        continue
                    if not isinstance(chunk, dict):
                        continue
                    biomes |= _biomes_of(chunk)
                    structures |= _structures_of(chunk)
                    chunks += 1
        except OSError as exc:
            logger.warning("region 读取失败 %s：%s", region_file, exc)
    return {
        "chunks": chunks,
        "biomes": sorted(biomes),
        "structures": sorted(structures),
        "files": len(files),
    }


def scan_world(world_dir: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"dimensions": {}}
    for name, rel in DIMENSIONS.items():
        region_dir = world_dir / rel
        if not region_dir.is_dir():
            continue
        info = scan_dimension(region_dir)
        info["biomes"] = info["biomes"][:40]
        info["structures"] = info["structures"][:40]
        result["dimensions"][name] = info
    return result


__all__ = ["scan_world", "scan_dimension"]
