"""书脊导航按钮 —— 竖排汉字 + 编号（墨刻的核心识别元素）

Qt 没有 CSS 的 writing-mode，这里用 QPainter 逐字竖排绘制，
视觉上等同纸书的书脊章节，而不是常见的图标栏。
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QPushButton, QWidget

from vein_launcher.presentation.ui.theme.tokens import palette


class SpineButton(QPushButton):
    """竖排文字导航按钮"""

    def __init__(self, index: str, text: str, theme: str = "paper", parent: QWidget | None = None):
        super().__init__(parent)
        self._index = index
        self._text = text
        self._theme = theme
        self._hover = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(104, 88)
        self.setFlat(True)

    # ------------------------------------------------------------------
    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        p = palette(self._theme)
        checked = self.isChecked()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # 底与左侧强调线
        bg = QColor(p["paper"]) if (self._hover and not checked) else None
        if bg is not None:
            painter.fillRect(self.rect(), bg)
        if checked:
            painter.fillRect(QRect(0, 0, self.width(), self.height()), QColor(p["paper"]))
            painter.fillRect(QRect(0, 12, 2, self.height() - 24), QColor(p["accent"]))

        # 竖排汉字
        color = QColor(p["accent"]) if checked else QColor(p["ink3"] if not self._hover else p["ink"])
        font = QFont("SimSun", 12)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        painter.setPen(QPen(color))

        char_h = 20
        total = len(self._text) * char_h
        y = max(10, (self.height() - total) // 2 - 8)
        for ch in self._text:
            painter.drawText(
                QRect(0, y, self.width() - 18, char_h),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                ch,
            )
            y += char_h

        # 编号
        num_font = QFont("Consolas", 8)
        painter.setFont(num_font)
        painter.setPen(QPen(QColor(p["ink3"])))
        painter.drawText(
            QRect(0, self.height() - 20, self.width() - 18, 14),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            self._index,
        )
        painter.end()


__all__ = ["SpineButton"]
