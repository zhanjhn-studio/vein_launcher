"""玩家头像加载 —— 真实皮肤优先，缺失时回退默认头

来源：mc-heads.net（支持用户名或 UUID），失败/离线时用内置像素头，
绝不伪造玩家数据。
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from vein_launcher.common.utils.path_utils import ensure_dir, get_app_data_dir

logger = logging.getLogger(__name__)

CACHE_DIR = get_app_data_dir() / "cache" / "avatars"
AVATAR_API = "https://mc-heads.net/avatar/{key}/{size}"

# Steve / Alex 头部色板（像素画）
STEVE = {
    "skin": "#c79a76",
    "shade": "#a97c58",
    "hair": "#3b2a1d",
    "eye": "#ffffff",
    "pupil": "#3d4d7a",
    "mouth": "#7a4a3a",
}
ALEX = {
    "skin": "#f0c8a6",
    "shade": "#d8ab86",
    "hair": "#cf7a2e",
    "eye": "#ffffff",
    "pupil": "#3b6b4f",
    "mouth": "#9c5f4a",
}


def default_head(name: str = "steve", size: int = 96) -> QPixmap:
    """内置像素头像（Steve / Alex 风格），无需联网"""
    palette = ALEX if name.lower().startswith("alex") else STEVE
    pix = QPixmap(size, size)
    pix.fill(QColor(palette["skin"]))

    painter = QPainter(pix)
    cell = size / 8.0
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def rect(x: int, y: int, color: str, w: int = 1, h: int = 1) -> None:
        painter.fillRect(int(x * cell), int(y * cell), int(w * cell), int(h * cell), QColor(color))

    # 头发
    rect(0, 0, palette["hair"], 8, 2)
    rect(0, 2, palette["hair"], 1, 4)
    rect(7, 2, palette["hair"], 1, 4)
    # 眼睛
    rect(1, 3, palette["eye"], 2, 1)
    rect(5, 3, palette["eye"], 2, 1)
    rect(2, 3, palette["pupil"])
    rect(5, 3, palette["pupil"])
    # 鼻子
    rect(3, 4, palette["shade"], 2, 1)
    # 嘴
    rect(3, 6, palette["mouth"], 2, 1)
    painter.end()
    return pix


class AvatarLoader(QObject):
    """异步加载并缓存头像"""

    loaded = Signal(str, QPixmap)  # key, pixmap

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        ensure_dir(CACHE_DIR)

    # ------------------------------------------------------------------
    def cache_key(self, username: str, uuid: Optional[str] = None) -> str:
        raw = (uuid or username or "steve").strip().lower().replace("-", "")
        return raw or "steve"

    def load(self, username: str, uuid: Optional[str] = None, size: int = 96) -> None:
        key = self.cache_key(username, uuid)
        cached = CACHE_DIR / f"{key}_{size}.png"
        if cached.is_file():
            pix = QPixmap(str(cached))
            if not pix.isNull():
                self.loaded.emit(key, pix)
                return

        request = QNetworkRequest(QUrl(AVATAR_API.format(key=key, size=size)))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._on_finished(reply, key, size))

    def _on_finished(self, reply, key: str, size: int) -> None:
        try:
            if reply.error():
                logger.debug("头像获取失败 %s：%s", key, reply.errorString())
                self.loaded.emit(key, default_head(key, size))
                return

            data = bytes(reply.readAll())
            pix = QPixmap()
            if not pix.loadFromData(data) or pix.isNull():
                self.loaded.emit(key, default_head(key, size))
                return

            target: Path = CACHE_DIR / f"{key}_{size}.png"
            pix.save(str(target), "PNG")
            self.loaded.emit(key, pix)
        finally:
            reply.deleteLater()


__all__ = ["AvatarLoader", "default_head"]
