"""应用层 - 皮肤管理（本地导入 + 皮肤站读取）

本地皮肤存放在 VeinLauncher/skins/<account_id>.png，元数据写 config/skins.json。
PNG 尺寸校验不依赖 Pillow：直接解析 IHDR。
"""

from __future__ import annotations

import base64
import json
import logging
import struct
import time
from pathlib import Path
from typing import Any, Dict, Optional

from vein_launcher.common.utils.path_utils import ensure_dir, get_config_dir, get_root_dir

logger = logging.getLogger(__name__)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
VALID_SIZES = {(64, 64), (64, 32)}  # 现代皮肤 / 旧版皮肤
MODELS = {"classic", "slim"}


class SkinError(RuntimeError):
    pass


def png_size(data: bytes) -> Optional[tuple[int, int]]:
    """读取 PNG 宽高；不是合法 PNG 时返回 None"""
    if len(data) < 24 or not data.startswith(PNG_SIGNATURE):
        return None
    if data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def validate_skin(data: bytes) -> tuple[int, int]:
    size = png_size(data)
    if size is None:
        raise SkinError("这不是有效的 PNG 图片")
    if size not in VALID_SIZES:
        raise SkinError(
            f"皮肤尺寸必须是 64×64 或 64×32，当前为 {size[0]}×{size[1]}"
        )
    if len(data) > 2 * 1024 * 1024:
        raise SkinError("皮肤文件过大（超过 2 MB）")
    return size


class SkinService:
    def __init__(self, root: Optional[Path] = None, meta: Optional[Path] = None):
        self._root = Path(root) if root else (get_root_dir() / "skins")
        self._meta_path = Path(meta) if meta else (get_config_dir() / "skins.json")

    # ------------------------------------------------------------------
    @property
    def root(self) -> Path:
        return self._root

    def _read_meta(self) -> Dict[str, Any]:
        try:
            data = json.loads(self._meta_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_meta(self, data: Dict[str, Any]) -> None:
        ensure_dir(self._meta_path.parent)
        self._meta_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _file_for(self, account_id: str) -> Path:
        safe = "".join(c for c in str(account_id) if c.isalnum() or c in "-_")
        return self._root / f"{safe}.png"

    # ------------------------------------------------------------------
    def list(self) -> Dict[str, Any]:
        return self._read_meta()

    def state(self, account_id: str) -> Dict[str, Any]:
        meta = self._read_meta().get(str(account_id)) or {}
        path = self._file_for(account_id)
        if not path.is_file():
            return {"has": False}
        info: Dict[str, Any] = {
            "has": True,
            "model": meta.get("model", "classic"),
            "source": meta.get("source", "local"),
            "updated_at": meta.get("at"),
            "path": str(path),
        }
        try:
            data = path.read_bytes()
            info["data_url"] = "data:image/png;base64," + base64.b64encode(data).decode()
            size = png_size(data)
            if size:
                info["size"] = [size[0], size[1]]
        except OSError:
            info["has"] = False
        return info

    def apply_file(self, account_id: str, source: str, model: str = "classic") -> Dict[str, Any]:
        path = Path(str(source))
        if not path.is_file():
            raise SkinError("找不到皮肤文件")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SkinError(f"读取皮肤失败：{exc}") from exc
        return self.apply_bytes(account_id, data, model, source="local")

    def apply_bytes(
        self, account_id: str, data: bytes, model: str = "classic", source: str = "local"
    ) -> Dict[str, Any]:
        validate_skin(data)
        model = (model or "classic").lower()
        if model not in MODELS:
            model = "classic"
        ensure_dir(self._root)
        target = self._file_for(account_id)
        target.write_bytes(data)
        meta = self._read_meta()
        meta[str(account_id)] = {
            "model": model,
            "source": source,
            "at": int(time.time()),
        }
        self._write_meta(meta)
        logger.info("皮肤已保存：%s（%s）", target, model)
        state = self.state(account_id)
        state["data_url"] = "data:image/png;base64," + base64.b64encode(data).decode()
        return state

    def clear(self, account_id: str) -> Dict[str, Any]:
        target = self._file_for(account_id)
        if target.is_file():
            try:
                target.unlink()
            except OSError as exc:
                raise SkinError(f"删除皮肤失败：{exc}") from exc
        meta = self._read_meta()
        if meta.pop(str(account_id), None) is not None:
            self._write_meta(meta)
        return {"has": False}


__all__ = ["SkinError", "SkinService", "png_size", "validate_skin"]
