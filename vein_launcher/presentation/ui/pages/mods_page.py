"""表现层 - 模组市场页（Modrinth）"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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


class ModsPage(QWidget):
    """搜索并安装模组到指定实例"""

    search_signal = Signal(object, object)
    install_signal = Signal(object, object)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._build()
        self.search_signal.connect(self._render_results)
        self.install_signal.connect(self._install_done)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        layout.addWidget(self._title("模组市场", "数据来源 Modrinth，安装时自动解析前置依赖"))

        filters = QHBoxLayout()
        filters.addWidget(QLabel("目标实例"))
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(180)
        filters.addWidget(self.version_combo)

        filters.addWidget(QLabel("加载器"))
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["fabric", "quilt", "forge", "neoforge"])
        filters.addWidget(self.loader_combo)
        layout.addLayout(filters)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索模组，例如：sodium / create / jei")
        self.search_input.returnPressed.connect(self._search)
        search_row.addWidget(self.search_input, 1)

        search_btn = QPushButton("搜索")
        search_btn.setObjectName("Primary")
        search_btn.clicked.connect(self._search)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        self.result_list = QListWidget()
        layout.addWidget(self.result_list, 1)

        bottom = QHBoxLayout()
        self.status = QLabel("输入关键词开始搜索")
        self.status.setObjectName("PageSubtitle")
        bottom.addWidget(self.status, 1)

        self.install_btn = QPushButton("安装所选模组")
        self.install_btn.clicked.connect(self._install_selected)
        bottom.addWidget(self.install_btn)
        layout.addLayout(bottom)

    @staticmethod
    def _title(text: str, subtitle: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(2)
        title = QLabel(text)
        title.setObjectName("PageTitle")
        sub = QLabel(subtitle)
        sub.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(sub)
        return box

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        installed = self._ctx.versions.list_installed_versions()
        current = self.version_combo.currentText()
        self.version_combo.clear()
        for item in installed:
            self.version_combo.addItem(item["id"])
        if current:
            index = self.version_combo.findText(current)
            if index >= 0:
                self.version_combo.setCurrentIndex(index)

    def _search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return
        version = self.version_combo.currentText() or None
        loader = self.loader_combo.currentText()
        self.status.setText("搜索中…")
        self._bridge.submit(
            self._ctx.mods.search(query, mc_version=version, loader=loader),
            self.search_signal.emit,
        )

    def _render_results(self, results: Any, error: Optional[BaseException]) -> None:
        if error:
            self.status.setText(f"搜索失败：{error}")
            return
        self.result_list.clear()
        for mod in results or []:
            text = f"{mod['title']}   ·   ⬇ {mod['downloads']:,}\n    {mod['description'][:110]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, mod)
            self.result_list.addItem(item)
        self.status.setText(f"找到 {len(results or [])} 个模组")

    # ------------------------------------------------------------------
    def _install_selected(self) -> None:
        item = self.result_list.currentItem()
        if not item:
            self._window.notify("请先选择一个模组")
            return
        version = self.version_combo.currentText()
        if not version:
            self._window.notify("请先安装目标游戏版本")
            return
        mod = item.data(Qt.ItemDataRole.UserRole)
        loader = self.loader_combo.currentText()
        self.install_btn.setEnabled(False)
        self.status.setText(f"正在安装 {mod['title']} …")
        self._bridge.submit(
            self._ctx.mods.install(
                mod["slug"],
                version,
                project_type="mod",
                mc_version=version,
                loader=loader,
            ),
            self.install_signal.emit,
        )

    def _install_done(self, result: Any, error: Optional[BaseException]) -> None:
        self.install_btn.setEnabled(True)
        if error:
            self.status.setText(f"安装失败：{error}")
            return
        ok = sum(1 for f in result["files"] if f["ok"])
        self.status.setText(f"已安装 {ok}/{len(result['files'])} 个文件")
        self._window.notify(f"模组安装完成（{ok} 个文件）")


__all__ = ["ModsPage"]
