"""表现层 - 版本管理页"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)


class VersionsPage(QWidget):
    """远程版本浏览与安装"""

    versions_signal = Signal(object, object)
    progress_signal = Signal(int, str)
    install_signal = Signal(object, object)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._build()
        self._wire()
        self._loaded = False

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("版本管理")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch(1)

        self.snapshot_toggle = QPushButton("显示快照")
        self.snapshot_toggle.setCheckable(True)
        self.snapshot_toggle.clicked.connect(lambda: self._load_versions())
        header.addWidget(self.snapshot_toggle)

        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self._load_versions)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        layout.addWidget(self.list_widget, 1)

        bottom = QHBoxLayout()
        self.status = QLabel("")
        self.status.setObjectName("PageSubtitle")
        bottom.addWidget(self.status, 1)

        self.progress = QProgressBar()
        self.progress.setFixedWidth(240)
        self.progress.setValue(0)
        bottom.addWidget(self.progress)

        self.install_btn = QPushButton("安装所选版本")
        self.install_btn.setObjectName("Primary")
        self.install_btn.clicked.connect(self._install_selected)
        bottom.addWidget(self.install_btn)

        self.remove_btn = QPushButton("删除本地版本")
        self.remove_btn.setObjectName("Danger")
        self.remove_btn.clicked.connect(self._remove_selected)
        bottom.addWidget(self.remove_btn)

        layout.addLayout(bottom)

    def _wire(self) -> None:
        self.versions_signal.connect(self._render_versions)
        self.progress_signal.connect(self._apply_progress)
        self.install_signal.connect(self._install_done)
        event_bus.subscribe(EventNames.VERSION_DOWNLOAD_PROGRESS, self._on_progress)

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        if not self._loaded:
            self._load_versions()

    def _load_versions(self) -> None:
        include_snapshots = self.snapshot_toggle.isChecked()
        self.status.setText("正在拉取 Mojang 版本清单…")
        self._bridge.submit(
            self._ctx.versions.list_remote_versions(include_snapshots=include_snapshots),
            self.versions_signal.emit,
        )

    def _render_versions(self, versions: Any, error: Optional[BaseException]) -> None:
        if error:
            self.status.setText(f"加载失败：{error}")
            return
        self.list_widget.clear()
        for item in versions or []:
            mark = "✔ " if item.get("installed") else ""
            text = f"{mark}{item['id']}   ·   {item['type']}   ·   {item.get('release_time', '')[:10]}"
            widget = QListWidgetItem(text)
            widget.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(widget)
        self.status.setText(f"共 {len(versions or [])} 个版本")
        self._loaded = True

    # ------------------------------------------------------------------
    def _install_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            self._window.notify("请先选择一个版本")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        version_id = data["id"]
        self.install_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status.setText(f"正在安装 {version_id}（含依赖库与资源文件）…")
        self._bridge.submit(
            self._ctx.versions.install(version_id), self.install_signal.emit
        )

    def _on_progress(self, percent: float = 0, phase: str = "", **_):
        self.progress_signal.emit(int(percent), phase)

    def _apply_progress(self, percent: int, phase: str) -> None:
        self.progress.setValue(percent)
        if phase:
            self.status.setText(f"{phase} … {percent}%")

    def _install_done(self, report: Any, error: Optional[BaseException]) -> None:
        self.install_btn.setEnabled(True)
        if error:
            self.status.setText(f"安装失败：{error}")
            return
        if getattr(report, "errors", None):
            self.status.setText(f"部分文件失败（{len(report.errors)} 个），详见日志")
            return
        self.progress.setValue(100)
        self.status.setText(f"{report.version_id} 安装完成 ✅")
        self._window.notify(f"{report.version_id} 安装完成")
        self._load_versions()

    # ------------------------------------------------------------------
    def _remove_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        self._bridge.submit(
            self._ctx.versions.remove_version(data["id"]), self._on_removed
        )

    def _on_removed(self, ok: Any, error: Optional[BaseException]) -> None:
        if error:
            self.status.setText(f"删除失败：{error}")
            return
        self.status.setText("已删除本地版本" if ok else "该版本未安装")
        self._load_versions()


__all__ = ["VersionsPage"]
