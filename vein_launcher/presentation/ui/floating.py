"""墨刻 - 悬浮球（印章圆盘 / 灵动岛）

最小化主窗口后显示，永远置顶：
- 圆盘：拖动移动，单击弹出辐射菜单（启动 / 恢复 / 下载 / 插件 / 设置 / 切换形态）
- 灵动岛：顶部细长胶囊，单击直接启动游戏，右键菜单可恢复窗口
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QMenu, QWidget

from vein_launcher.presentation.ui.theme.tokens import palette


class FloatingOrb(QWidget):
    """置顶悬浮控件"""

    launch_requested = Signal()
    restore_requested = Signal()
    switch_mode_requested = Signal()
    navigate_requested = Signal(str)

    DISC_SIZE = 62
    ISLAND_SIZE = (250, 38)

    def __init__(self, theme: str = "paper", mode: str = "disc", parent: QWidget | None = None):
        super().__init__(parent)
        self._theme = theme
        self._mode = mode
        self._drag_origin: QPoint | None = None
        self._moved = False

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_mode(mode)

    # ------------------------------------------------------------------
    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if mode == "disc":
            self.setFixedSize(self.DISC_SIZE, self.DISC_SIZE)
        else:
            self.setFixedSize(*self.ISLAND_SIZE)
        self.update()

    @property
    def mode(self) -> str:
        return self._mode

    def move_to_default(self, screen) -> None:
        """放到屏幕底部中间偏右"""
        if screen is None:
            return
        geo = screen.availableGeometry()
        if self._mode == "disc":
            self.move(geo.center().x() + 120, geo.bottom() - 140)
        else:
            self.move(geo.center().x() - self.width() // 2, geo.top() + 24)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._mode == "disc":
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.setPen(QPen(QColor(p["accent"]), 1))
            painter.setBrush(QColor(p["accent"]))
            painter.drawEllipse(rect)

            # 虚线外环
            pen = QPen(QColor(p["accent"]))
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(rect.adjusted(-7, -7, 7, 7))

            font = QFont("SimSun", 15)
            painter.setFont(font)
            painter.setPen(QPen(QColor(p["accent_ink"])))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "启")
        else:
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.setBrush(QColor(p["surface"]))
            painter.setPen(QPen(QColor(p["text3"]), 1))
            painter.drawRoundedRect(rect, 8, 8)

            painter.setBrush(QColor(p["ok"]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRect(14, self.height() // 2 - 2, 5, 5))

            font = QFont("Consolas", 10)
            painter.setFont(font)
            painter.setPen(QPen(QColor(p["text2"])))
            painter.drawText(
                QRect(28, 0, self.width() - 96, self.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                "1.20.4 · fabric",
            )

            painter.setBrush(QColor(p["accent"]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRect(self.width() - 62, 8, 54, self.height() - 16), 4, 4)
            painter.setPen(QPen(QColor(p["accent_ink"])))
            painter.setFont(QFont("Microsoft YaHei UI", 9))
            painter.drawText(
                QRect(self.width() - 62, 8, 54, self.height() - 16),
                Qt.AlignmentFlag.AlignCenter,
                "启动",
            )
        painter.end()

    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._moved = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_origin
            if (new_pos - self.pos()).manhattanLength() > 4:
                self._moved = True
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self._moved:
            self._activate()
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.restore_requested.emit()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self._build_menu().exec(event.globalPos())

    # ------------------------------------------------------------------
    def _activate(self) -> None:
        if self._mode == "island":
            self.launch_requested.emit()
        else:
            self._build_menu().exec(self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2)))

    def _build_menu(self) -> QMenu:
        menu = QMenu(self)
        act_launch = QAction("启动游戏", menu)
        act_launch.triggered.connect(self.launch_requested.emit)
        menu.addAction(act_launch)

        act_restore = QAction("恢复窗口", menu)
        act_restore.triggered.connect(self.restore_requested.emit)
        menu.addAction(act_restore)
        menu.addSeparator()

        for key, label in (("download", "下载"), ("plugin", "插件"), ("setting", "设置")):
            action = QAction(label, menu)
            action.triggered.connect(lambda _=False, k=key: self.navigate_requested.emit(k))
            menu.addAction(action)

        menu.addSeparator()
        other = "灵动岛" if self._mode == "disc" else "圆盘"
        act_mode = QAction(f"切换为{other}", menu)
        act_mode.triggered.connect(self.switch_mode_requested.emit)
        menu.addAction(act_mode)
        return menu


__all__ = ["FloatingOrb"]
