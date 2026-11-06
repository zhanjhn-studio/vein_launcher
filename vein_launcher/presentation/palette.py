"""指令速查 / 构建器小窗（全局热键 Ctrl+Alt+Q 唤起）

完整功能对齐工具页的「指令构建器」：
- 输入一段指令 → 列出后面能接什么 → 点/回车追加 → 逐级构建
- 输入中文或英文关键词 → 直接在全部候选里检索（物品、二级参数都能搜到）
- 复制按钮 / Ctrl+Enter 把当前指令写进剪贴板，Esc 关闭，回退可逐级撤销

数据由前端通过 tools.syncPalette 推过来（带 parent 的扁平候选表），
这里用 parent 重建「前缀 → 候选」的树，所以不依赖页面是否打开过。
"""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 60
ITEM_ROLE = Qt.ItemDataRole.UserRole

STYLE = """
#plRoot { background: #151a22; border: 1px solid #2a3240; border-radius: 10px; }
#plTitle { color: #e8ecf4; font-size: 13px; font-weight: 600; }
#plHint, #plStatus { color: #6b7688; font-size: 11px; }
#plSlash { color: #6f97f0; font-size: 16px; font-weight: 700; }
#plInput {
    background: #1d232d; border: 1px solid #2a3240; border-radius: 7px;
    padding: 8px 10px; color: #e8ecf4; font-size: 13px;
}
#plInput:focus { border-color: #6f97f0; }
#plCurrent {
    background: #171c24; border: 1px solid #232a35; border-radius: 7px;
    padding: 6px 10px; color: #9da8ba; font-size: 12px;
}
#plList {
    background: #171c24; border: 1px solid #232a35; border-radius: 7px;
    color: #c9d2e0; font-size: 12px; outline: none;
}
#plList::item { padding: 6px 9px; border-radius: 5px; }
#plList::item:selected { background: #26324a; color: #ffffff; }
#plBtn {
    background: #1d232d; border: 1px solid #2a3240; border-radius: 6px;
    color: #9da8ba; padding: 7px 12px; font-size: 12px;
}
#plBtn:hover { border-color: #6f97f0; color: #e8ecf4; }
#plBtn:disabled { color: #4a5566; border-color: #232a35; }
"""


def _user32():
    if sys.platform != "win32":
        return None
    try:
        u = ctypes.WinDLL("user32", use_last_error=True)
        u.GetForegroundWindow.restype = ctypes.c_void_p
        u.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        u.GetWindowThreadProcessId.restype = ctypes.c_ulong
        u.AttachThreadInput.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_bool]
        u.SetForegroundWindow.argtypes = [ctypes.c_void_p]
        u.SetFocus.argtypes = [ctypes.c_void_p]
        return u
    except OSError:  # pragma: no cover
        return None


def normalize(text: str) -> str:
    """去掉开头的 /、压缩空白，和前端 normalizeCommand 保持一致"""
    return " ".join(str(text or "").lstrip("/").split())


class CommandPalette(QWidget):
    """无边框置顶小窗：指令构建器 + 中文检索"""

    picked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setObjectName("plRoot")
        self.setWindowTitle("指令速查")
        self.setFixedSize(660, 480)
        self.setStyleSheet(STYLE)

        self._entries: List[dict] = []
        self._tree: Dict[str, List[dict]] = {}
        self._nodes: set = set()
        self._source: Optional[Callable[[], List[dict]]] = None
        self._rows: List[dict] = []
        self._history: List[str] = []
        self._mode = "root"
        self._prev_hwnd = 0
        self._user32 = _user32()
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        head = QHBoxLayout()
        title = QLabel("指令速查")
        title.setObjectName("plTitle")
        hint = QLabel("Enter 追加/复制 · Ctrl+Enter 复制 · Esc 关闭")
        hint.setObjectName("plHint")
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(hint)
        layout.addLayout(head)

        row = QHBoxLayout()
        row.setSpacing(6)
        slash = QLabel("/")
        slash.setObjectName("plSlash")
        self.input = QLineEdit(self)
        self.input.setObjectName("plInput")
        self.input.setPlaceholderText("输入指令（kill / give / time…）或中文关键词（钻石 / 封禁）")
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self._accept)
        self.input.installEventFilter(self)

        self.btn_copy = QPushButton("复制", self)
        self.btn_copy.setObjectName("plBtn")
        self.btn_copy.clicked.connect(self._copy_draft)
        self.btn_undo = QPushButton("回退", self)
        self.btn_undo.setObjectName("plBtn")
        self.btn_undo.clicked.connect(self._undo)
        self.btn_clear = QPushButton("清空", self)
        self.btn_clear.setObjectName("plBtn")
        self.btn_clear.clicked.connect(self._clear)

        row.addWidget(slash)
        row.addWidget(self.input, 1)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_clear)
        layout.addLayout(row)

        self.current = QLabel("/…", self)
        self.current.setObjectName("plCurrent")
        layout.addWidget(self.current)

        self.list = QListWidget(self)
        self.list.setObjectName("plList")
        self.list.setWordWrap(True)
        self.list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list, 1)

        self.status = QLabel("", self)
        self.status.setObjectName("plStatus")
        layout.addWidget(self.status)

    # ------------------------------------------------------------------ 数据
    def set_source(self, source: Callable[[], List[dict]]) -> None:
        self._source = source

    def _load(self) -> None:
        try:
            data = self._source() if self._source else None
        except Exception:
            logger.exception("读取速查表失败")
            data = None

        entries: List[dict] = []
        nodes: List[str] = []
        if isinstance(data, tuple) and len(data) == 2:
            entries = list(data[0] or [])
            nodes = list(data[1] or [])
        elif isinstance(data, list):
            entries = list(data)

        self._entries = entries
        self._nodes = {normalize(n) for n in nodes if normalize(n)}
        tree: Dict[str, List[dict]] = {}
        for entry in entries:
            parent = normalize(entry.get("parent", ""))
            tree.setdefault(parent, []).append(entry)
        self._tree = tree

    # ------------------------------------------------------------------ 显示
    def open_palette(self) -> None:
        self._prev_hwnd = self._foreground_window()
        self._load()
        self._history = []
        self.input.blockSignals(True)
        self.input.clear()
        self.input.blockSignals(False)
        self._refresh()
        self._place_window()
        self.show()
        self.raise_()
        # 窗口刚 show 出来还没真正 map，立刻抢焦点会被 Windows 拒绝，延后两拍再抢
        QTimer.singleShot(0, self._grab_focus)
        QTimer.singleShot(120, self._grab_focus)
        logger.info("指令速查已唤起（%d 条候选）", len(self._entries))

    def _grab_focus(self) -> None:
        """把速查窗顶到前台并让输入框拿到键盘焦点"""
        self._force_foreground()
        self.activateWindow()
        self.input.setFocus()

    def _place_window(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        dpr = float(screen.devicePixelRatio() or 1.0)
        phys_w = int(self.width() * dpr)
        phys_h = int(self.height() * dpr)
        x = max(geo.left(), geo.center().x() - phys_w // 2)
        y = max(geo.top(), geo.top() + int(geo.height() * 0.10))
        if y + phys_h > geo.bottom():
            y = max(geo.top(), geo.bottom() - phys_h)
        self.move(x, y)

    def _force_foreground(self) -> None:
        """把速查窗顶到前台并抢到键盘焦点（AttachThreadInput 绕过前台锁）"""
        u = self._user32
        if u is None:
            return
        try:
            hwnd = ctypes.c_void_p(int(self.winId()))
            fg = u.GetForegroundWindow()
            cur_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            if fg:
                fg_thread = u.GetWindowThreadProcessId(fg, None)
                if fg_thread and fg_thread != cur_thread:
                    u.AttachThreadInput(fg_thread, cur_thread, True)
                    u.SetForegroundWindow(hwnd)
                    u.AttachThreadInput(fg_thread, cur_thread, False)
                else:
                    u.SetForegroundWindow(hwnd)
            else:
                u.SetForegroundWindow(hwnd)
            u.SetFocus(hwnd)
        except Exception:
            logger.debug("前置速查窗失败", exc_info=True)

    # ------------------------------------------------------------------ 检索 / 构建
    def _on_text_changed(self, _text: str) -> None:
        self._refresh()

    def _refresh(self) -> None:
        raw = self.input.text()
        key = normalize(raw)

        # 1) 能对上合法前缀：构建模式（没有候选 = 指令已完整）
        if key in self._nodes or key in self._tree:
            self._mode = "builder" if key else "root"
            rows = self._tree.get(key, [])
            kind = "append"
        # 2) 对不上但有输入：全局检索模式
        elif key:
            self._mode = "search"
            rows = self._search(key)
            kind = "apply"
        else:
            self._mode = "root"
            rows = self._tree.get("", [])
            kind = "append"

        self._rows = rows[:MAX_ROWS]
        # 「指令已经完整」：前缀没候选，或者检索不到但首词是已知指令
        first = key.split(" ", 1)[0] if key else ""
        self._complete = bool(key) and (not self._rows) and (
            key in self._nodes or first in self._nodes
        )
        self.list.clear()
        for row in self._rows:
            label = self._row_label(row, kind)
            item = QListWidgetItem(label)
            self.list.addItem(item)
        if self._rows:
            self.list.setCurrentRow(0)

        draft = normalize(raw)
        self.current.setText("/" + draft if draft else "/…")
        self.btn_copy.setEnabled(bool(draft))
        self.btn_undo.setEnabled(bool(self._history))
        self.btn_clear.setEnabled(bool(draft))

        total = len(self._entries)
        if self._complete:
            self.status.setText("这条指令已经完整：Enter 或 Ctrl+Enter 复制")
        elif self._mode == "search":
            self.status.setText(
                f"检索：{len(self._rows)} / {total} 条 · 点击填入输入框 · Enter 直接复制"
            )
        else:
            self.status.setText(
                f"后面可以接 {len(self._rows)} 项 · Enter 追加 · Ctrl+Enter 复制当前指令"
            )

    def _row_label(self, row: dict, kind: str) -> str:
        hint = row.get("hint", "")
        if kind == "apply":
            label = row.get("command") or row.get("token", "")
        else:
            label = row.get("token", "")
        return f"{label}    {hint}" if hint else label

    def _search(self, key: str) -> List[dict]:
        low = key.lower()
        hits = [
            e
            for e in self._entries
            if low in str(e.get("token", "")).lower()
            or low in str(e.get("hint", "")).lower()
            or low in str(e.get("parent", "")).lower()
        ]
        return hits

    # ------------------------------------------------------------------ 交互
    def _on_item_clicked(self, _item) -> None:
        """检索模式点结果 = 填进输入框（不关窗）；构建模式点结果 = 追加"""
        if self._mode != "search":
            self._accept()
            return
        entry = self._rows[self.list.currentRow()] if self._rows else None
        if entry is None:
            return
        command = normalize(entry.get("command") or entry.get("token", ""))
        if not command:
            return
        self._history.append(normalize(self.input.text()))
        # 检索结果本身就是一条完整指令，标记为已知前缀，刷新后直接显示"已完整"
        self._nodes.add(command)
        self.input.setText(command)
        self.input.setFocus()
        logger.info("速查窗点击填入：/%s", command)

    def _accept(self) -> None:
        """构建模式追加选中项；检索模式直接复制整条指令"""
        logger.info(
            "速查窗 accept：mode=%s rows=%d cur=%d",
            self._mode,
            len(self._rows),
            self.list.currentRow(),
        )
        entry = self._rows[self.list.currentRow()] if self._rows else None

        if self._mode == "search":
            if entry is None:
                # 检索不到但首词是已知指令：当作"指令已完整"直接复制
                if self._complete:
                    self._copy_draft()
                return
            self._copy(entry.get("command") or entry.get("token", ""))
            return

        if entry is None:
            # 没有候选 = 指令已经完整
            self._copy_draft()
            return

        base = normalize(self.input.text())
        token = str(entry.get("token", ""))
        if not token:
            return
        self._history.append(base)
        self.input.setText((base + " " + token).strip())

    def _undo(self) -> None:
        if not self._history:
            return
        self.input.setText(self._history.pop())

    def _clear(self) -> None:
        if normalize(self.input.text()):
            self._history.append(normalize(self.input.text()))
        self.input.clear()

    def _copy_draft(self) -> None:
        draft = normalize(self.input.text())
        if draft:
            self._copy(draft)

    def _copy(self, command: str) -> None:
        command = normalize(command)
        if not command:
            return
        QGuiApplication.clipboard().setText("/" + command)
        logger.info("速查窗复制：/%s", command)
        self.hide()
        self._restore_focus()
        self.picked.emit("/" + command)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt 约定
        if obj is self.input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                row = self.list.currentRow()
                step = 1 if key == Qt.Key.Key_Down else -1
                row = max(0, min(self.list.count() - 1, row + step))
                self.list.setCurrentRow(row)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # 回车统一在这里处理，不依赖 returnPressed（焦点可能在列表上）
                if mods & Qt.KeyboardModifier.ControlModifier:
                    self._copy_draft()
                else:
                    self._accept()
                return True
            if key == Qt.Key.Key_Backspace and not self.input.text() and self._history:
                self._undo()
                return True
        return super().eventFilter(obj, event)

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self._restore_focus()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.hide()
        super().focusOutEvent(event)

    # ------------------------------------------------------------------ 焦点
    def _foreground_window(self) -> int:
        if self._user32 is None:
            return 0
        try:
            return int(self._user32.GetForegroundWindow() or 0)
        except Exception:
            return 0

    def _restore_focus(self) -> None:
        if self._user32 is None or not self._prev_hwnd:
            return
        try:
            self._user32.SetForegroundWindow(ctypes.c_void_p(self._prev_hwnd))
        except Exception:
            logger.debug("恢复焦点失败", exc_info=True)
        finally:
            self._prev_hwnd = 0


__all__ = ["CommandPalette"]
