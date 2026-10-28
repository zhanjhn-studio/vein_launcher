"""表现层 - 插件管理页（特色模块）

展示：插件清单、权限声明、宿主能力目录、实时日志。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)


class PluginsPage(QWidget):
    """插件面板"""

    refresh_signal = Signal(object, object)
    action_signal = Signal(object, object)
    install_signal = Signal(object, object)
    log_signal = Signal(str)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._log_buffer: List[str] = []
        self._build()
        self._wire()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        box = QVBoxLayout()
        box.setSpacing(2)
        title = QLabel("插件系统")
        title.setObjectName("PageTitle")
        sub = QLabel("Node.js 插件宿主 · 双向 JSON-RPC · 权限沙箱")
        sub.setObjectName("PageSubtitle")
        box.addWidget(title)
        box.addWidget(sub)
        header.addLayout(box)
        header.addStretch(1)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._refresh)
        header.addWidget(self.refresh_btn)

        self.install_btn = QPushButton("从文件夹安装…")
        self.install_btn.clicked.connect(self._install_from_dir)
        header.addWidget(self.install_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()

        # --- 已安装 ---
        installed_tab = QWidget()
        vbox = QVBoxLayout(installed_tab)
        vbox.setContentsMargins(10, 12, 10, 12)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["插件", "版本", "状态", "权限数", "来源"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection)
        vbox.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.enable_btn = QPushButton("启用")
        self.enable_btn.setObjectName("Primary")
        self.enable_btn.clicked.connect(lambda: self._toggle(True))
        self.disable_btn = QPushButton("停用")
        self.disable_btn.clicked.connect(lambda: self._toggle(False))
        self.uninstall_btn = QPushButton("卸载")
        self.uninstall_btn.setObjectName("Danger")
        self.uninstall_btn.clicked.connect(self._uninstall)
        actions.addWidget(self.enable_btn)
        actions.addWidget(self.disable_btn)
        actions.addStretch(1)
        actions.addWidget(self.uninstall_btn)
        vbox.addLayout(actions)

        self.detail = QLabel("选择插件查看权限声明")
        self.detail.setWordWrap(True)
        self.detail.setObjectName("PageSubtitle")
        vbox.addWidget(self.detail)
        self.tabs.addTab(installed_tab, "已安装")

        # --- 宿主能力 ---
        cap_tab = QWidget()
        cap_layout = QVBoxLayout(cap_tab)
        cap_layout.setContentsMargins(10, 12, 10, 12)
        self.cap_table = QTableWidget(0, 3)
        self.cap_table.setHorizontalHeaderLabels(["能力", "所需权限", "说明"])
        self.cap_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.cap_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        cap_layout.addWidget(self.cap_table)
        self.tabs.addTab(cap_tab, "宿主能力")

        # --- 日志 ---
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(10, 12, 10, 12)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        log_layout.addWidget(self.log_view)
        self.tabs.addTab(log_tab, "运行日志")

        layout.addWidget(self.tabs, 1)

        self.status = QLabel("插件宿主状态未知")
        self.status.setObjectName("PageSubtitle")
        layout.addWidget(self.status)

    def _wire(self) -> None:
        self.refresh_signal.connect(self._render_plugins)
        self.action_signal.connect(self._action_done)
        self.install_signal.connect(self._install_done)
        self.log_signal.connect(self.log_view.appendPlainText)

        event_bus.subscribe(EventNames.PLUGIN_LOG, self._on_log)
        event_bus.subscribe(EventNames.PLUGIN_ERROR, self._on_plugin_error)
        event_bus.subscribe(
            EventNames.PLUGIN_PERMISSION_DENIED, self._on_permission_denied
        )
        event_bus.subscribe(EventNames.PLUGIN_LIST_UPDATED, lambda **_: self._refresh())

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._flush_logs)
        self._timer.start(300)

    # ------------------------------------------------------------------
    # 事件 → UI（跨线程，只入缓冲）
    # ------------------------------------------------------------------
    def _on_log(self, plugin_id: str = "", message: str = "", **_) -> None:
        self._log_buffer.append(f"[{plugin_id}] {message}")

    def _on_plugin_error(self, plugin_id: str = "", error: str = "", **_) -> None:
        self._log_buffer.append(f"[{plugin_id}] ❌ {error}")

    def _on_permission_denied(self, plugin_id: str = "", api: str = "", error: str = "", **_) -> None:
        self._log_buffer.append(f"[{plugin_id}] 🚫 越权拦截 {api}：{error}")

    def _flush_logs(self) -> None:
        if not self._log_buffer:
            return
        chunk = "\n".join(self._log_buffer)
        self._log_buffer.clear()
        self.log_signal.emit(chunk)

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self._bridge.submit(self._load_data(), self.refresh_signal.emit)

    async def _load_data(self) -> dict:
        return {
            "plugins": self._ctx.plugins.list_plugins(),
            "capabilities": self._ctx.plugins.capability_catalog(),
            "host_running": self._ctx.plugins.host.running,
        }

    def _render_plugins(self, data: Any, error: Optional[BaseException]) -> None:
        if error:
            self.status.setText(f"加载失败：{error}")
            return
        plugins = data["plugins"]
        self.table.setRowCount(len(plugins))
        for row, plugin in enumerate(plugins):
            state = "运行中" if plugin["active"] else ("已启用" if plugin["enabled"] else "已停用")
            cells = [
                plugin["name"],
                plugin["version"],
                state,
                str(len(plugin["permissions"])),
                plugin["source"],
            ]
            for col, text in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(text))

        self.cap_table.setRowCount(len(data["capabilities"]))
        for row, cap in enumerate(data["capabilities"]):
            self.cap_table.setItem(row, 0, QTableWidgetItem(cap["name"]))
            self.cap_table.setItem(row, 1, QTableWidgetItem(cap["permission"]))
            self.cap_table.setItem(row, 2, QTableWidgetItem(cap["description"]))

        host = "运行中" if data["host_running"] else "未运行"
        self.status.setText(f"宿主 {host} · 已安装 {len(plugins)} 个插件")

    def _on_selection(self) -> None:
        plugin = self._current_plugin()
        if not plugin:
            return
        perms = "、".join(plugin["permissions"]) or "（未声明任何权限）"
        self.detail.setText(f"权限声明：{perms}\n安装路径：{plugin['path']}")

    def _current_plugin(self) -> Optional[dict]:
        row = self.table.currentRow()
        if row < 0:
            return None
        plugins = self._ctx.plugins.list_plugins()
        if row >= len(plugins):
            return None
        return plugins[row]

    # ------------------------------------------------------------------
    def _toggle(self, enable: bool) -> None:
        plugin = self._current_plugin()
        if not plugin:
            self._window.notify("请先选择一个插件")
            return
        coro = (
            self._ctx.plugins.enable(plugin["id"])
            if enable
            else self._ctx.plugins.disable(plugin["id"])
        )
        self._bridge.submit(coro, self.action_signal.emit)

    def _uninstall(self) -> None:
        plugin = self._current_plugin()
        if not plugin:
            return
        self._bridge.submit(
            self._ctx.plugins.uninstall(plugin["id"]), self.action_signal.emit
        )

    def _action_done(self, result: Any, error: Optional[BaseException]) -> None:
        if error:
            self._window.notify(f"操作失败：{error}")
        self._refresh()

    def _install_from_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择插件目录")
        if not directory:
            return
        from pathlib import Path

        self._bridge.submit(
            self._ctx.plugins.install_from_dir(Path(directory)), self.install_signal.emit
        )

    def _install_done(self, result: Any, error: Optional[BaseException]) -> None:
        if error:
            self._window.notify(f"安装失败：{error}")
            return
        self._window.notify(f"已安装插件 {result.manifest.name}")
        self._refresh()


__all__ = ["PluginsPage"]
