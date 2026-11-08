"""指令速查 / 构建器小窗（全局热键 Ctrl+Alt+Q 唤起）

交互设计：
    左侧  输入框 + 当前指令预览 + 操作按钮
    右侧  候选列表（鼠标点击 / ↑↓ 选择 / Tab 追加）
    Enter：指令完整时直接发进游戏；还有候选时先追加
    Ctrl+Enter：强制发送当前指令
    Esc：关闭

发送失败（游戏没开 / agent 未连接）时由主窗口弹提示，并自动把指令复制到剪贴板。
"""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
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

MAX_ROWS = 80
ITEM_ROLE = Qt.ItemDataRole.UserRole

STYLE = """
#plRoot {
    background: #12161d;
    border: 1px solid #2a3444;
    border-radius: 14px;
}
#plRoot QLabel { color: #d7deeb; }
#plTitle { color: #eef2f9; font-size: 15px; font-weight: 700; letter-spacing: .01em; }
#plSub { color: #6d7b90; font-size: 11px; }
#plKbd {
    color: #8fa6c8; background: #1b2230; border: 1px solid #2a3444;
    border-radius: 5px; padding: 2px 7px; font-size: 10.5px;
}
#plSlash { color: #7fa3ff; font-size: 18px; font-weight: 800; }
#plInput {
    background: #171d27; border: 1px solid #2a3444; border-radius: 9px;
    padding: 10px 12px; color: #eef2f9; font-size: 14px;
    selection-background-color: #33507d;
}
#plInput:focus { border-color: #6f97f0; background: #182030; }
#plCurrent {
    background: #151b24; border: 1px solid #222b37; border-radius: 9px;
    padding: 8px 12px; color: #9fb0c8; font-size: 12.5px;
}
#plCurrent[ready="true"] { color: #bcd0f5; border-color: #2f4570; }
#plSend {
    background: #4f7bf0; border: 1px solid #4f7bf0; border-radius: 9px;
    color: #ffffff; padding: 10px 16px; font-size: 12.5px; font-weight: 700;
}
#plSend:hover { background: #5f89f5; }
#plSend:disabled { background: #232b38; border-color: #232b38; color: #5a6579; }
#plBtn {
    background: #1a212c; border: 1px solid #2a3444; border-radius: 9px;
    color: #9fb0c8; padding: 10px 12px; font-size: 12px;
}
#plBtn:hover { border-color: #6f97f0; color: #eef2f9; }
#plBtn:disabled { color: #4a5566; border-color: #222b37; }
#plPanel {
    background: #141a23; border: 1px solid #222b37; border-radius: 10px;
}
#plPanelTitle { color: #7c8ba2; font-size: 11px; font-weight: 700; letter-spacing: .08em; }
#plList {
    background: transparent; border: 0; color: #cdd7ea; font-size: 12.5px; outline: none;
}
#plList::item {
    padding: 6px 10px; border-radius: 8px; margin: 2px 5px;
    border-left: 2px solid transparent;
}
#plList::item:hover {
    background: #1b2333; border-left-color: #3d4a63;
}
#plList::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2b2350, stop:0.55 #232a45, stop:1 #1c2437);
    color: #f2ecff; border-left-color: #8a7ff0;
}
#plStatus { color: #6d7b90; font-size: 11.5px; }
#plFoot { color: #5d6a7e; font-size: 10.5px; }
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


def asset_path(name: str):
    """找 assets/ 下的资源（源码运行与打包后都能找到）"""
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[2] / "assets" / name,
        Path(__file__).resolve().parents[1] / "assets" / name,
    ]
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.append(Path(base) / "assets" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def ui_language_is_zh() -> bool:
    try:
        from vein_launcher.common.config.settings import settings_manager

        return str(settings_manager.get().ui.language).lower().startswith("zh")
    except Exception:
        return False


class CommandPalette(QWidget):
    """无边框置顶小窗：指令构建器 + 中文检索 + 直接发送"""

    picked = Signal(str)
    send_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setObjectName("plRoot")
        self.setWindowTitle("指令速查")
        self.setFixedSize(780, 560)
        self.setStyleSheet(STYLE)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._entries: List[dict] = []
        self._tree: Dict[str, List[dict]] = {}
        self._nodes: set = set()
        self._source: Optional[Callable[[], List[dict]]] = None
        self._rows: List[dict] = []
        self._history: List[str] = []
        self._mode = "root"
        self._complete = False
        self._prev_hwnd = 0
        self._user32 = _user32()
        self._book_icon = QIcon(str(asset_path("palette_book.png")))
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        # 标题行
        head = QHBoxLayout()
        title = QLabel("指令速查")
        title.setObjectName("plTitle")
        title.setMinimumHeight(24)
        sub = QLabel("输入指令或中文关键词，右侧选候选项")
        sub.setObjectName("plSub")
        sub.setMinimumHeight(24)
        head.addWidget(title)
        head.addSpacing(8)
        head.addWidget(sub)
        head.addStretch(1)
        for text in ("↑↓ 选择", "Enter 发送", "Esc 关闭"):
            chip = QLabel(text)
            chip.setObjectName("plKbd")
            chip.setMinimumHeight(22)
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            head.addWidget(chip)
        layout.addLayout(head)

        # 输入行
        row = QHBoxLayout()
        row.setSpacing(8)
        slash = QLabel("/")
        slash.setObjectName("plSlash")
        self.input = QLineEdit(self)
        self.input.setObjectName("plInput")
        self.input.setPlaceholderText("kill / give / time … 或中文关键词：钻石、封禁、白天")
        self.input.setMinimumHeight(42)
        self.input.textChanged.connect(self._on_text_changed)
        self.input.installEventFilter(self)

        self.btn_send = QPushButton("发送到游戏", self)
        self.btn_send.setObjectName("plSend")
        self.btn_send.clicked.connect(lambda: self.send_current(force=True))
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
        row.addWidget(self.btn_send)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_clear)
        layout.addLayout(row)

        # 当前指令
        self.current = QLabel("/…", self)
        self.current.setObjectName("plCurrent")
        self.current.setMinimumHeight(34)
        layout.addWidget(self.current)

        # 主体：左信息 / 右候选
        body = QHBoxLayout()
        body.setSpacing(12)

        left = QFrame(self)
        left.setObjectName("plPanel")
        left.setFixedWidth(250)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(8)
        self.left_title = QLabel("说明")
        self.left_title.setObjectName("plPanelTitle")
        self.left_layout = left_layout
        self.status = QLabel("", left)
        self.status.setObjectName("plStatus")
        self.status.setWordWrap(True)
        left_layout.addWidget(self.left_title)
        left_layout.addWidget(self.status)
        left_layout.addStretch(1)
        tip = QLabel(
            "点击候选 = 追加到指令\nTab = 追加高亮项\nEnter = 完整指令直接发送\nCtrl+Enter = 强制发送",
            left,
        )
        tip.setObjectName("plFoot")
        tip.setWordWrap(True)
        left_layout.addWidget(tip)
        body.addWidget(left)

        right = QFrame(self)
        right.setObjectName("plPanel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(6)
        self.list_title = QLabel("候选", right)
        self.list_title.setObjectName("plPanelTitle")
        self.list = QListWidget(right)
        self.list.setObjectName("plList")
        self.list.setWordWrap(True)
        self.list.setIconSize(QSize(26, 26))
        self.list.setUniformItemSizes(True)
        self.list.setSpacing(1)
        self.list.itemClicked.connect(self._on_item_clicked)
        self.list.itemDoubleClicked.connect(lambda _i: self.send_current(force=True))
        right_layout.addWidget(self.list_title)
        right_layout.addWidget(self.list, 1)
        body.addWidget(right, 1)

        layout.addLayout(body, 1)

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
        QTimer.singleShot(0, self._grab_focus)
        QTimer.singleShot(120, self._grab_focus)
        logger.info("指令速查已唤起（%d 条候选）", len(self._entries))

    def _grab_focus(self) -> None:
        self._force_foreground()
        self.activateWindow()
        self.input.setFocus()

    def _place_window(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = max(geo.left(), geo.center().x() - self.width() // 2)
        y = max(geo.top(), geo.top() + int(geo.height() * 0.12))
        if y + self.height() > geo.bottom():
            y = max(geo.top(), geo.bottom() - self.height())
        self.move(x, y)

    def _force_foreground(self) -> None:
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

        if key in self._nodes or key in self._tree:
            self._mode = "builder" if key else "root"
            rows = self._tree.get(key, [])
            kind = "append"
        elif key:
            self._mode = "search"
            rows = self._search(key)
            kind = "apply"
        else:
            self._mode = "root"
            rows = self._tree.get("", [])
            kind = "append"

        self._rows = rows[:MAX_ROWS]
        first = key.split(" ", 1)[0] if key else ""
        self._complete = bool(key) and (not self._rows) and (
            key in self._nodes or first in self._nodes
        )

        self.list.clear()
        for row in self._rows:
            label = self._row_label(row, kind)
            item = QListWidgetItem(label)
            item.setData(ITEM_ROLE, row)
            if not self._book_icon.isNull():
                item.setIcon(self._book_icon)
            item.setSizeHint(QSize(0, 42))
            self.list.addItem(item)
        if self._rows:
            self.list.setCurrentRow(0)

        draft = normalize(raw)
        self.current.setText("/" + draft if draft else "/…")
        self.current.setProperty("ready", "true" if self._complete else "false")
        self.current.style().unpolish(self.current)
        self.current.style().polish(self.current)

        self.list_title.setText(f"候选  ·  {len(self._rows)}")
        self.btn_send.setEnabled(bool(draft))
        self.btn_copy.setEnabled(bool(draft))
        self.btn_undo.setEnabled(bool(self._history))
        self.btn_clear.setEnabled(bool(draft))

        if self._complete:
            self.status.setText("这条指令已经完整，按 Enter 直接发送进游戏。")
        elif self._mode == "search":
            self.status.setText(
                f"正在全局检索：命中 {len(self._rows)} 条。\n点击候选填入，Enter 发送。"
            )
        elif self._rows:
            self.status.setText(
                f"后面还能接 {len(self._rows)} 项。\n点击或 Tab 追加，Enter/按钮 发送。"
            )
        else:
            self.status.setText("输入指令前缀开始构建，或输入中文关键词检索。")

    def _row_label(self, row: dict, kind: str) -> str:
        hint = row.get("hintZh") if ui_language_is_zh() else row.get("hint")
        hint = hint or row.get("hint", "")
        if kind == "apply":
            label = row.get("command") or row.get("token", "")
        else:
            label = row.get("token", "")
        return f"{label}    {hint}" if hint else label

    def _search(self, key: str) -> List[dict]:
        low = key.lower()
        return [
            e
            for e in self._entries
            if low in str(e.get("token", "")).lower()
            or low in str(e.get("hint", "")).lower()
            or low in str(e.get("parent", "")).lower()
        ]

    # ------------------------------------------------------------------ 交互
    def _append_current(self) -> bool:
        """把高亮候选追加到输入框；返回是否真的追加了"""
        entry = self._rows[self.list.currentRow()] if self._rows else None
        if entry is None:
            return False
        base = normalize(self.input.text())
        token = str(entry.get("token", ""))
        if not token:
            return False
        self._history.append(base)
        self.input.setText((base + " " + token).strip())
        self.input.setFocus()
        return True

    def _on_item_clicked(self, _item) -> None:
        """点击候选：检索结果填进输入框，构建模式直接追加"""
        if self._mode == "search":
            entry = self._rows[self.list.currentRow()] if self._rows else None
            if entry is None:
                return
            command = normalize(entry.get("command") or entry.get("token", ""))
            if not command:
                return
            self._history.append(normalize(self.input.text()))
            self._nodes.add(command)
            self.input.setText(command)
            self.input.setFocus()
            logger.info("速查窗点击填入：/%s", command)
            return
        self._append_current()

    def send_current(self, force: bool = False) -> None:
        """Enter / 发送按钮：完整就发游戏，否则先追加候选"""
        if not force and not self._complete and self._rows:
            if self._append_current():
                return
        draft = normalize(self.input.text())
        if not draft:
            return
        command = "/" + draft
        logger.info("速查窗发送：%s", command)
        self.hide()
        self._restore_focus()
        self.send_requested.emit(command)

    def _undo(self) -> None:
        if not self._history:
            return
        self.input.setText(self._history.pop())
        self.input.setFocus()

    def _clear(self) -> None:
        if normalize(self.input.text()):
            self._history.append(normalize(self.input.text()))
        self.input.clear()
        self.input.setFocus()

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
            if key in (Qt.Key.Key_Tab, Qt.Key.Key_Right):
                if self._append_current():
                    return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if mods & Qt.KeyboardModifier.ControlModifier:
                    self.send_current(force=True)
                else:
                    self.send_current()
                return True
            if key == Qt.Key.Key_C and (mods & Qt.KeyboardModifier.ControlModifier):
                self._copy_draft()
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
            self.send_current()
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
