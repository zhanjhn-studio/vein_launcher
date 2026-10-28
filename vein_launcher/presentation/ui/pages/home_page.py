"""墨刻 - 主页（启动页）

左侧：大字标题 + 数据 + 世界墙；右侧：身份档案。
启动动作在底部发射台，本页只负责选择与展示。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)


def _rule() -> QFrame:
    line = QFrame()
    line.setObjectName("Rule")
    line.setFrameShape(QFrame.Shape.HLine)
    return line


def _stat(key: str, value: str) -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    k = QLabel(key)
    k.setObjectName("StatKey")
    v = QLabel(value)
    v.setObjectName("StatValue")
    layout.addWidget(k)
    layout.addWidget(v)
    return box


class HomePage(QWidget):
    """启动页"""

    launch_failed = Signal(str)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(30, 24, 30, 20)
        outer.setSpacing(0)

        outer.addWidget(self._build_lead(), 3)
        outer.addWidget(self._build_profile(), 2)

    def _build_lead(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 28, 0)
        layout.setSpacing(10)

        head = QHBoxLayout()
        idx = QLabel("01")
        idx.setObjectName("MastIndex")
        title = QLabel("启动")
        title.setObjectName("MastTitle")
        sub = QLabel("选择一个世界，继续上次的进度")
        sub.setObjectName("MastSub")
        head.addWidget(idx)
        head.addWidget(title)
        head.addWidget(sub)
        head.addStretch(1)
        manage = QPushButton("管理版本")
        manage.setObjectName("Ghost")
        manage.clicked.connect(lambda: self._window.switch_page("version"))
        head.addWidget(manage)
        layout.addLayout(head)
        layout.addWidget(_rule())

        lead = QLabel("雪原还在下雪，\n火把也还没熄。")
        lead.setObjectName("Lead")
        lead.setWordWrap(True)
        layout.addWidget(lead)

        lede = QLabel(
            "上次你在第 1284 天离开。Fabric 0.15.7 上的 42 个模组已就绪，"
            "Java 17 与 4 GB 内存分配完成。"
        )
        lede.setObjectName("Lede")
        lede.setWordWrap(True)
        layout.addWidget(lede)

        stats = QHBoxLayout()
        stats.setSpacing(34)
        for key, value in (
            ("累计时长", "128h"),
            ("存档", "06"),
            ("模组", "42"),
            ("上次启动", "2h"),
        ):
            stats.addWidget(_stat(key, value))
        stats.addStretch(1)
        layout.addSpacing(8)
        layout.addLayout(stats)

        layout.addSpacing(6)
        layout.addWidget(_rule())

        worlds = QGridLayout()
        worlds.setSpacing(1)
        worlds.setContentsMargins(0, 8, 0, 0)
        items = [
            ("WORLD 01", "雪原生存", "2 天前 · 1.8 GB"),
            ("WORLD 02", "沙漠工业", "5 天前 · 640 MB"),
            ("WORLD 03", "海岛建筑", "1 周前 · 320 MB"),
        ]
        for col, (no, name, meta) in enumerate(items):
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(5)
            k = QLabel(no)
            k.setObjectName("MastIndex")
            n = QLabel(name)
            n.setObjectName("PageTitle")
            n.setStyleSheet("font-size: 16px;")
            m = QLabel(meta)
            m.setObjectName("Hint")
            card_layout.addWidget(k)
            card_layout.addWidget(n)
            card_layout.addWidget(m)
            worlds.addWidget(card, 0, col)
        layout.addLayout(worlds)
        layout.addStretch(1)
        return box

    def _build_profile(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(30, 0, 0, 0)
        layout.setSpacing(8)

        cap = QLabel("当前身份")
        cap.setObjectName("MastIndex")
        layout.addWidget(cap)

        face = QLabel("🧑‍🌾")
        face.setObjectName("ProfileFace")
        face.setFixedSize(96, 96)
        face.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(face)

        self.name_label = QLabel("gazi_Z")
        self.name_label.setObjectName("ProfileName")
        layout.addWidget(self.name_label)

        self.meta_label = QLabel("microsoft · 已登录")
        self.meta_label.setObjectName("ProfileMeta")
        layout.addWidget(self.meta_label)

        layout.addSpacing(10)

        version_row = QHBoxLayout()
        key = QLabel("当前实例")
        key.setObjectName("MastSub")
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(150)
        version_row.addWidget(key)
        version_row.addWidget(self.version_combo, 1)
        layout.addLayout(version_row)

        for label, value in (
            ("账号类型", "正版"),
            ("Java", "17 · Adoptium"),
        ):
            row = QHBoxLayout()
            k = QLabel(label)
            k.setObjectName("MastSub")
            v = QLabel(value)
            v.setObjectName("ProfileMeta")
            row.addWidget(k)
            row.addStretch(1)
            row.addWidget(v)
            layout.addLayout(row)

        layout.addStretch(1)
        return box

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self._refresh_versions()
        self._refresh_account()

    def _refresh_versions(self) -> None:
        installed = self._ctx.versions.list_installed_versions()
        current = self.version_combo.currentData()
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for item in installed:
            self.version_combo.addItem(item["id"], item["id"])
        if current:
            index = self.version_combo.findData(current)
            if index >= 0:
                self.version_combo.setCurrentIndex(index)
        if not installed:
            self.version_combo.addItem("（尚未安装版本）", None)
        self.version_combo.blockSignals(False)

    def _refresh_account(self) -> None:
        try:
            account = self._ctx.accounts.current()
        except Exception:
            account = None
        if account:
            self.name_label.setText(account.username)
            self.meta_label.setText(f"{getattr(account, 'account_type', 'offline')} · 已登录")
            self._window.set_account(account.username)

    # ------------------------------------------------------------------
    @property
    def selected_version(self) -> Optional[str]:
        return self.version_combo.currentData()

    def launch(self) -> None:
        version_id = self.selected_version
        if not version_id:
            self.launch_failed.emit("请先在版本管理中安装一个实例")
            return

        account = self._ctx.accounts.current()

        def done(result: Any, error: Optional[BaseException]) -> None:
            if error:
                logger.error("启动失败：%s", error)
                self.launch_failed.emit(str(error))
                return
            event_bus.publish(EventNames.GAME_RUNNING, pid=result)

        self._bridge.submit(
            self._ctx.launcher.launch_with_account(version_id, account), done
        )


__all__ = ["HomePage"]
