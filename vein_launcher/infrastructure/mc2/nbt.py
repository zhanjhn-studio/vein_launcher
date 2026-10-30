"""最小 NBT 读取器（仅用于 level.dat 等小型文件）"""

from __future__ import annotations

import gzip
import io
import struct
from pathlib import Path
from typing import Any, BinaryIO, Dict, Tuple

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class _Reader:
    def __init__(self, stream: BinaryIO):
        self._s = stream

    def read(self, n: int) -> bytes:
        data = self._s.read(n)
        if len(data) != n:
            raise ValueError("NBT 数据不完整")
        return data

    def unpack(self, fmt: str, size: int) -> Any:
        return struct.unpack(fmt, self.read(size))[0]

    def string(self) -> str:
        length = self.unpack(">H", 2)
        return self.read(length).decode("utf-8", errors="replace")


def _read_payload(reader: _Reader, tag: int) -> Any:
    if tag == TAG_BYTE:
        return reader.unpack(">b", 1)
    if tag == TAG_SHORT:
        return reader.unpack(">h", 2)
    if tag == TAG_INT:
        return reader.unpack(">i", 4)
    if tag == TAG_LONG:
        return reader.unpack(">q", 8)
    if tag == TAG_FLOAT:
        return reader.unpack(">f", 4)
    if tag == TAG_DOUBLE:
        return reader.unpack(">d", 8)
    if tag == TAG_BYTE_ARRAY:
        return reader.read(reader.unpack(">i", 4))
    if tag == TAG_STRING:
        return reader.string()
    if tag == TAG_LIST:
        item_type = reader.unpack(">b", 1)
        length = reader.unpack(">i", 4)
        return [_read_payload(reader, item_type) for _ in range(max(0, length))]
    if tag == TAG_COMPOUND:
        result: Dict[str, Any] = {}
        while True:
            child = reader.unpack(">b", 1)
            if child == TAG_END:
                return result
            name = reader.string()
            result[name] = _read_payload(reader, child)
    if tag == TAG_INT_ARRAY:
        length = reader.unpack(">i", 4)
        return [reader.unpack(">i", 4) for _ in range(max(0, length))]
    if tag == TAG_LONG_ARRAY:
        length = reader.unpack(">i", 4)
        return [reader.unpack(">q", 8) for _ in range(max(0, length))]
    raise ValueError(f"未知 NBT 标签：{tag}")


def loads(raw: bytes) -> Any:
    """从已解压的 NBT 字节解析"""
    reader = _Reader(io.BytesIO(raw))
    root_type = reader.unpack(">b", 1)
    reader.string()  # 根标签名
    return _read_payload(reader, root_type)


def load(path: Path) -> Tuple[str, Any]:
    """返回 (根标签名, 值)"""
    with path.open("rb") as raw:
        with gzip.GzipFile(fileobj=raw) as gz:
            reader = _Reader(gz)
            root_type = reader.unpack(">b", 1)
            root_name = reader.string()
            return root_name, _read_payload(reader, root_type)


__all__ = ["load"]
