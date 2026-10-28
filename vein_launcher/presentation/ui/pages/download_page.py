"""墨刻 - 下载页（原版版本 + 社区资源）"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames

logger = logging.getLogger(__name__)

PROJECT_TYPES = [
    ("mod", "模组"),
    ("modpack", "整合包"),
    ("resourcepack", "资源包"),
    ("shader", "光影"),
    ("datapack", "数据包"),
]


class DownloadPage(QWidget):
    """下载中心"""

    versions_signal = Signal(object, object)
    install_signal = Signal(object, object)
    search_signal = Signal(object, object)
    progress_signal = Signal(int, str)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._loaded = False
        self._build()
        self._wire()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 18)
        layout.setSpacing(10)

        head = QHBoxLayout()
        idx = QLabel("02")
        idx.setObjectName("MastIndex")
        title = QLabel("下载")
        title.setObjectName("MastTitle")
        sub = QLabel("原版版本、模组、整合包、资源包、光影、数据包")
        sub.setObjectName("MastSub")
        head.addWidget(idx)
        head.addWidget(title)
        head.addWidget(sub)
        head.addStretch(1)
        layout.addLayout(head)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: palette(mid);")
        layout.addWidget(line)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_vanilla(), "原版版本")
        self.tabs.addTab(self._build_community(), "社区资源")
        layout.addWidget(self.tabs, 1)

    def _build_vanilla(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(6, 12, 6, 8)
        layout.setSpacing(8)

        row = QHBoxLayout()
        self.snapshot_btn = QPushButton("显示快照")
        self.snapshot_btn.setCheckable(True)
        self.snapshot_btn.clicked.connect(self._load_versions)
        refresh = QPushButton("刷新列表")
        refresh.clicked.connect(self._load_versions)
        self.install_btn = QPushButton("安装所选")
        self.install_btn.setObjectName("Primary")
        self.install_btn.clicked.connect(self._install_version)
        row.addWidget(self.snapshot_btn)
        row.addWidget(refresh)
        row.addStretch(1)
        row.addWidget(self.install_btn)
        layout.addLayout(row)

        self.version_list = QListWidget()
        layout.addWidget(self.version_list, 1)

        bottom = QHBoxLayout()
        self.vanilla_status = QLabel("尚未加载版本列表")
        self.vanilla_status.setObjectName("Hint")
        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.setValue(0)
        bottom.addWidget(self.vanilla_status, 1)
        bottom.addWidget(self.progress)
        layout.addLayout(bottom)
        return box

    def _build_community(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(6, 12, 6, 8)
        layout.setSpacing(8)

        row = QHBoxLayout()
        self.type_combo = QComboBox()
        for key, label in PROJECT_TYPES:
            self.type_combo.addItem(label, key)
        self.type_combo.currentIndexChanged.connect(lambda _=0: self._search())
        self.mc_combo = QComboBox()
        self.mc_combo.setEditable(True)
        self.mc_combo.addItem("1.20.4")
        self.mc_combo.addItem("1.21.4")
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["fabric", "forge", "quilt", "neoforge", "不限"])
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索 Sodium / Faithful / Complementary…")
        self.search_input.returnPressed.connect(self._search)
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("Primary")
        search_btn.clicked.connect(self._search)

        row.addWidget(QLabel("类型"))
        row.addWidget(self.type_combo)
        row.addWidget(QLabel("版本"))
        row.addWidget(self.mc_combo)
        row.addWidget(self.loader_combo)
        row.addWidget(self.search_input, 1)
        row.addWidget(search_btn)
        layout.addLayout(row)

        self.result_list = QListWidget()
        layout.addWidget(self.result_list, 1)

        bottom = QHBoxLayout()
        self.community_status = QLabel("输入关键词开始搜索")
        self.community_status.setObjectName("Hint")
        install = QPushButton("安装所选")
        install.clicked.connect(self._install_resource)
        bottom.addWidget(self.community_status, 1)
        bottom.addWidget(install)
        layout.addLayout(bottom)
        return box

    # ------------------------------------------------------------------
    def _wire(self) -> None:
        self.versions_signal.connect(self._render_versions)
        self.install_signal.connect(self._install_done)
        self.search_signal.connect(self._render_search)
        self.progress_signal.connect(self._apply_progress)
        event_bus.subscribe(EventNames.VERSION_DOWNLOAD_PROGRESS, self._on_progress)

    def _on_progress(self, percent: float = 0, phase: str = "", **_):
        self.progress_signal.emit(int(percent), str(phase))

    def _apply_progress(self, percent: int, phase: str) -> None:
        self.progress.setValue(percent)
        if phase:
            self.vanilla_status.setText(f"{phase} … {percent}%")

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        if not self._loaded:
            self._load_versions()

    def _load_versions(self) -> None:
        self.vanilla_status.setText("正在拉取版本清单…")
        self._bridge.submit(
            self._ctx.versions.list_remote_versions(
                include_snapshots=self.snapshot_btn.isChecked()
            ),
            self.versions_signal.emit,
        )

    def _render_versions(self, versions: Any, error: Optional[BaseException]) -> None:
        if error:
            self.vanilla_status.setText(f"加载失败：{error}")
            return
        self.version_list.clear()
        for item in versions or []:
            mark = "✔ " if item.get("installed") else ""
            text = f"{mark}{item['id']}    ·    {item['type']}    ·    {item.get('release_time', '')[:10]}"
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, item)
            self.version_list.addItem(row)
        self.vanilla_status.setText(f"共 {len(versions or [])} 个版本")
        self._loaded = True

    # ------------------------------------------------------------------
    def _install_version(self) -> None:
        item = self.version_list.currentItem()
        if not item:
            self._window.notify("请先选择一个版本")
            return
        version_id = item.data(Qt.ItemDataRole.UserRole)["id"]
        self.install_btn.setEnabled(False)
        self.vanilla_status.setText(f"正在安装 {version_id}…")
        self._bridge.submit(
            self._ctx.versions.install(version_id), self.install_signal.emit
        )

    def _install_done(self, report: Any, error: Optional[BaseException]) -> None:
        self.install_btn.setEnabled(True)
        if error:
            self.vanilla_status.setText(f"安装失败：{error}")
            return
        errors = getattr(report, "errors", [])
        if errors:
            self.vanilla_status.setText(f"部分文件失败（{len(errors)} 个）")
        else:
            self.progress.setValue(100)
            self.vanilla_status.setText(f"{report.version_id} 安装完成 ✅")
            self._window.notify(f"{report.version_id} 安装完成")
        self._load_versions()

    # ------------------------------------------------------------------
    def _search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return
        project_type = self.type_combo.currentData()
        loader = self.loader_combo.currentText()
        if loader == "不限":
            loader = None
        self.community_status.setText("搜索中…")
        self._bridge.submit(
            self._ctx.mods.search(
                query,
                project_type=project_type,
                mc_version=self.mc_combo.currentText() or None,
                loader=loader,
            ),
            self.search_signal.emit,
        )

    def _render_search(self, results: Any, error: Optional[BaseException]) -> None:
        if error:
            self.community_status.setText(f"搜索失败：{error}")
            return
        self.result_list.clear()
        for mod in results or []:
            text = f"{mod['title']}    ·    ⬇ {mod['downloads']:,}\n    {mod['description'][:90]}"
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, mod)
            self.result_list.addItem(row)
        self.community_status.setText(f"找到 {len(results or [])} 个结果")

    def _install_resource(self) -> None:
        row = self.result_list.currentItem()
        if not row:
            self._window.notify("请先选择一个资源")
            return
        mod = row.data(Qt.ItemDataRole.UserRole)
        instance = self.mc_combo.currentText()
        if not instance:
            self._window.notify("请填写目标实例")
            return
        loader = self.loader_combo.currentText()
        if loader == "不限":
            loader = "fabric"
        self.community_status.setText(f"正在安装 {mod['title']}…")
        self._bridge.submit(
            self._ctx.mods.install(
                mod["slug"],
                instance,
                project_type=self.type_combo.currentData(),
                mc_version=instance,
                loader=loader,
                source=mod.get("source", "modrinth"),
            ),
            self.install_signal.emit,
        )


__all__ = ["DownloadPage"]
