"""版本解析与比较工具"""

import re
from typing import Optional, Tuple


def parse_version_string(version_str: str) -> Optional[Tuple[int, ...]]:
    """
    解析版本号字符串为元组
    
    Args:
        version_str: 如 "1.20.4", "25w04a"
        
    Returns:
        版本元组，如 (1, 20, 4)
    """
    # 处理标准版本号：1.20.4
    if re.match(r"^\d+\.\d+(\.\d+)?$", version_str):
        parts = version_str.split(".")
        return tuple(int(p) for p in parts)
    
    # 处理快照版本：25w04a -> (25, 4, 'a')
    snapshot_match = re.match(r"(\d+)w(\d+)([a-z]*)", version_str)
    if snapshot_match:
        year = int(snapshot_match.group(1))
        week = int(snapshot_match.group(2))
        suffix = snapshot_match.group(3)
        return (year, week, 0) + tuple(ord(c) for c in suffix) if suffix else (year, week, 0)
    
    return None


def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号
    
    Args:
        v1: 版本 1
        v2: 版本 2
        
    Returns:
        -1: v1 < v2
         0: v1 == v2
         1: v1 > v2
    """
    parsed_v1 = parse_version_string(v1)
    parsed_v2 = parse_version_string(v2)
    
    if parsed_v1 is None or parsed_v2 is None:
        # 无法解析则按字符串比较
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        return 0
    
    # 补齐长度
    max_len = max(len(parsed_v1), len(parsed_v2))
    parsed_v1 = parsed_v1 + (0,) * (max_len - len(parsed_v1))
    parsed_v2 = parsed_v2 + (0,) * (max_len - len(parsed_v2))
    
    if parsed_v1 < parsed_v2:
        return -1
    elif parsed_v1 > parsed_v2:
        return 1
    return 0


def is_snapshot_version(version_id: str) -> bool:
    """判断是否为快照版本"""
    return bool(re.match(r"^\d+w\d+", version_id))


def get_major_minor(version_id: str) -> Optional[str]:
    """
    提取主要版本号
    
    Args:
        version_id: "fabric-1.20.4-v1" or "1.20.4"
        
    Returns:
        "1.20.4" or None
    """
    # 去掉前缀：fabric- / forge- / quilt- / loader-
    cleaned = re.sub(r"^(fabric|forge|quilt|loader)-", "", version_id, flags=re.IGNORECASE)
    
    # 提取版本号主体
    match = re.match(r"(\d+\.\d+(\.\d+)?)", cleaned)
    if match:
        return match.group(1)
    return None


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        如 "2.5 MB"
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def parse_size(size_str: str) -> int:
    """
    解析文件大小字符串为字节数
    
    Args:
        size_str: "2.5 MB", "4 GB", "1024 KB"
        
    Returns:
        字节数
    """
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    
    size_str = size_str.strip().upper()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            num_str = size_str[:-len(unit)].strip()
            return int(float(num_str) * multiplier)
    
    # 纯数字
    return int(size_str)
