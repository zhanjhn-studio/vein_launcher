"""表现层 - 主页（选版本 / 选账号 / 启动）"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)


class HomePage(QWidget):
    """启动入口页"""

    game_log_signal = Signal(str)
    launch_done_signal = Signal(object, object)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._log_buffer: List[str] = []

        self._build()
        self._wire_signals()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("准备起飞")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("选择实例与账号，一键进入 Minecraft")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("游戏版本"))
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(220)
        row1.addWidget(self.version_combo, 1)
        row1.addWidget(QLabel("账号"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(160)
        row1.addWidget(self.account_combo, 1)
        card_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("最大内存 (MB)"))
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(512, 32768)
        self.memory_spin.setSingleStep(512)
        self.memory_spin.setValue(4096)
        row2.addWidget(self.memory_spin)
        row2.addStretch(1)
        self.launch_button = QPushButton("启动游戏")
        self.launch_button.setObjectName("Primary")
        self.launch_button.setMinimumWidth(160)
        self.launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_button.clicked.connect(self._on_launch)
        row2.addWidget(self.launch_button)
        card_layout.addLayout(row2)

        layout.addWidget(card)

        self.status_label = QLabel("")
        self.status_label.setObjectName("PageSubtitle")
        layout.addWidget(self.status_label)

        log_label = QLabel("游戏日志")
        log_label.setObjectName("PageSubtitle")
        layout.addWidget(log_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        self.log_view.setPlaceholderText("启动游戏后，这里会实时显示 stdout 输出…")
        layout.addWidget(self.log_view, 1)

    def _wire_signals(self) -> None:
        self.game_log_signal.connect(self.log_view.appendPlainText)
        self.launch_done_signal.connect(self._on_launch_done)
        event_bus.subscribe(EventNames.GAME_LOG_UPDATE, self._on_game_log)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)
        event_bus.subscribe(EventNames.UI_NOTIFY, self._on_notify)

        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_logs)
        self._flush_timer.start(250)

    # ------------------------------------------------------------------
    # 事件（可能来自后台线程，只做缓冲/发信号）
    # ------------------------------------------------------------------
    def _on_game_log(self, line: str = "", **_) -> None:
        self._log_buffer.append(line)
        if len(self._log_buffer) > 500:
            del self._log_buffer[:-500]

    def _flush_logs(self) -> None:
        if not self._log_buffer:
            return
        chunk = "\n".join(self._log_buffer)
        self._log_buffer.clear()
        self.game_log_signal.emit(chunk)

    def _on_game_exited(self, exit_code: int = 0, **_) -> None:
        self.status_label.setText(f"游戏已退出，退出码 {exit_code}")
        self.launch_button.setEnabled(True)

    def _on_notify(self, title: str = "", message: str = "", **_) -> None:
        self._window.notify(f"{title}：{message}")

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self._refresh_versions()
        self._refresh_accounts()

    def _refresh_versions(self) -> None:
        installed = self._ctx.versions.list_installed_versions()
        self.version_combo.clear()
        if not installed:
            self.version_combo.addItem("（暂无已安装版本，请先去版本管理下载）", None)
            return
        for item in installed:
            self.version_combo.addItem(f"{item['id']}  ·  {item['type']}", item["id"])

    def _refresh_accounts(self) -> None:
        accounts = self._ctx.accounts.list_accounts()
        self.account_combo.clear()
        if not accounts:
            self.account_combo.addItem("（未添加账号，将使用离线 Player）", None)
            return
        for acc in accounts:
            mark = " ●" if acc["selected"] else ""
            self.account_combo.addItem(f"{acc['username']} ({acc['type']}){mark}", acc["id"])

    # ------------------------------------------------------------------
    def _on_launch(self) -> None:
        version_id = self.version_combo.currentData()
        if not version_id:
            self._window.notify("请先安装一个游戏版本")
            return

        account_id = self.account_combo.currentData()
        account = None
        if account_id:
            self._ctx.accounts.select(account_id)
            account = self._ctx.accounts.current()

        self.launch_button.setEnabled(False)
        self.status_label.setText("正在构建启动命令…")
        self._bridge.submit(
            self._ctx.launcher.launch_with_account(version_id, account),
            self.launch_done_signal.emit,
        )

    def _on_launch_done(self, result: Any, error: Optional[BaseException]) -> None:
        if error:
            self.launch_button.setEnabled(True)
            self.status_label.setText(f"启动失败：{error}")
            self._window.notify(f"启动失败：{error}")
            return
        self.status_label.setText(f"游戏已启动，PID={result}")


__all__ = ["HomePage"]
