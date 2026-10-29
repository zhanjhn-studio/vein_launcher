"""桌面悬浮入口：Logo 小球 / 灵动岛

不用时缩在屏幕顶部，鼠标移上去显现；点击后四周弹出选项。
"""

from __future__ import annotations

import math
from typing import List, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

ACCENT = "#2f6fed"
INK = "#ffffff"
ITEMS: List[Tuple[str, str]] = [
    ("home", "启动"),
    ("versions", "版本"),
    ("download", "下载"),
    ("accounts", "账号"),
    ("settings", "设置"),
    ("quit", "退出"),
]


class RadialMenu(QWidget):
    """围绕小球弹出的环形菜单"""

    triggered = Signal(str)

    RADIUS = 96
    ITEM_SIZE = 46

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        size = self.RADIUS * 2 + self.ITEM_SIZE + 24
        self.setFixedSize(size, size)

        self._buttons: List[QPushButton] = []
        center = size / 2
        for index, (key, label) in enumerate(ITEMS):
            angle = -math.pi / 2 + index * (2 * math.pi / len(ITEMS))
            button = QPushButton(label, self)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFixedSize(self.ITEM_SIZE, self.ITEM_SIZE)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: #ffffff;
                    color: #1f2328;
                    border: 1px solid #e3e7ee;
                    border-radius: {self.ITEM_SIZE // 2}px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {ACCENT};
                    color: #ffffff;
                    border-color: {ACCENT};
                }}
                """
            )
            x = center + math.cos(angle) * self.RADIUS - self.ITEM_SIZE / 2
            y = center + math.sin(angle) * self.RADIUS - self.ITEM_SIZE / 2
            button.move(int(x), int(y))
            button.clicked.connect(lambda _=False, k=key: self._pick(k))
            self._buttons.append(button)

    def _pick(self, key: str) -> None:
        self.hide()
        self.triggered.emit(key)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.setPen(QPen(QColor("#e3e7ee"), 1))
        margin = self.ITEM_SIZE / 2 + 6
        painter.drawEllipse(self.rect().adjusted(int(margin), int(margin), -int(margin), -int(margin)))
        painter.end()

    def popup_at(self, center: QPoint) -> None:
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        self.show()
        self.raise_()
        self.activateWindow()


class LogoBall(QWidget):
    """悬浮 Logo：小球 / 灵动岛"""

    navigate = Signal(str)

    BALL_SIZE = 64
    ISLAND_SIZE = (196, 40)
    HIDDEN_MARGIN = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._mode = "ball"
        self._visible = False
        self._menu = RadialMenu()
        self._menu.triggered.connect(self.navigate.emit)

        self.set_mode("ball")
        self._move_hidden()

        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        self._mode = "island" if mode == "island" else "ball"
        if self._mode == "ball":
            self.setFixedSize(self.BALL_SIZE, self.BALL_SIZE)
        else:
            self.setFixedSize(*self.ISLAND_SIZE)
        self._move_visible() if self._visible else self._move_hidden()
        self.update()

    def _screen(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    def _move_visible(self) -> None:
        geo = self._screen()
        x = geo.center().x() - self.width() // 2
        self.move(x, geo.top() + 8)

    def _move_hidden(self) -> None:
        geo = self._screen()
        x = geo.center().x() - self.width() // 2
        self.move(x, geo.top() - self.height() - self.HIDDEN_MARGIN)

    def _tick(self) -> None:
        pos = QCursor.pos()
        geo = self._screen()
        near_top = pos.y() <= geo.top() + 6
        inside = self.geometry().contains(pos)
        menu_open = self._menu.isVisible()

        if near_top or inside or menu_open:
            if not self._visible:
                self._visible = True
                self._move_visible()
                self.show()
                self.raise_()
        elif self._visible:
            self._visible = False
            self.hide()
            self._move_hidden()

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._mode == "ball":
            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.setBrush(QColor(ACCENT))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            self._draw_logo(painter, rect)
        else:
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#e3e7ee"), 1))
            painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

            badge = QRect(8, 6, 28, 28)
            painter.setBrush(QColor(ACCENT))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge)
            self._draw_logo(painter, badge)

            painter.setPen(QPen(QColor("#1f2328")))
            painter.setFont(QFont("Microsoft YaHei UI", 10))
            painter.drawText(
                QRect(44, 0, self.width() - 52, self.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                "Vein Launcher",
            )
        painter.end()

    @staticmethod
    def _draw_logo(painter: QPainter, rect: QRect) -> None:
        """V 字标记"""
        w, h = rect.width(), rect.height()
        left = QPoint(rect.left() + int(w * 0.28), rect.top() + int(h * 0.30))
        bottom = QPoint(rect.center().x(), rect.top() + int(h * 0.72))
        right = QPoint(rect.left() + int(w * 0.72), rect.top() + int(h * 0.30))

        pen = QPen(QColor(INK))
        pen.setWidthF(max(2.0, w * 0.08))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(QPolygonF([left, bottom, right]))

    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            self._menu.popup_at(center)
        super().mousePressEvent(event)


__all__ = ["LogoBall", "RadialMenu"]
