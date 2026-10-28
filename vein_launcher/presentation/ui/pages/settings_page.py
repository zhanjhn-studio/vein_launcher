"""表现层 - 设置页"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.config.settings import settings_manager

logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """基础设置：Java、内存、分辨率、主题、语言"""

    detect_signal = Signal(object, object)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._build()
        self.detect_signal.connect(self._detect_done)
        self._load_values()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("设置")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(12)

        java_row = QHBoxLayout()
        self.java_path = QLineEdit()
        self.java_path.setPlaceholderText("留空则自动探测（JAVA_HOME / 注册表 / 安装目录）")
        java_row.addWidget(self.java_path, 1)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse_java)
        java_row.addWidget(browse)
        detect = QPushButton("自动检测")
        detect.clicked.connect(self._detect_java)
        java_row.addWidget(detect)
        form.addRow("Java 路径", java_row)

        self.java_result = QLabel("")
        self.java_result.setObjectName("PageSubtitle")
        form.addRow("", self.java_result)

        self.memory_min = QSpinBox()
        self.memory_min.setRange(512, 16384)
        self.memory_min.setSingleStep(512)
        self.memory_max = QSpinBox()
        self.memory_max.setRange(1024, 65536)
        self.memory_max.setSingleStep(512)
        memory_row = QHBoxLayout()
        memory_row.addWidget(self.memory_min)
        memory_row.addWidget(QLabel("~"))
        memory_row.addWidget(self.memory_max)
        memory_row.addWidget(QLabel("MB"))
        memory_row.addStretch(1)
        form.addRow("内存范围", memory_row)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 7680)
        self.width_spin.setSingleStep(10)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 4320)
        self.height_spin.setSingleStep(10)
        res_row = QHBoxLayout()
        res_row.addWidget(self.width_spin)
        res_row.addWidget(QLabel("×"))
        res_row.addWidget(self.height_spin)
        res_row.addStretch(1)
        form.addRow("窗口分辨率", res_row)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("白墨（paper）", "paper")
        self.theme_combo.addItem("夜墨（night）", "night")
        self.theme_combo.addItem("青瓷（celadon）", "celadon")
        form.addRow("纸色主题", self.theme_combo)

        self.float_combo = QComboBox()
        self.float_combo.addItem("圆盘", "disc")
        self.float_combo.addItem("灵动岛", "island")
        form.addRow("悬浮形态", self.float_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        form.addRow("语言", self.language_combo)

        layout.addWidget(card)
        layout.addStretch(1)

        bottom = QHBoxLayout()
        self.status = QLabel("")
        self.status.setObjectName("PageSubtitle")
        bottom.addWidget(self.status, 1)
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._save)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)

    # ------------------------------------------------------------------
    def _load_values(self) -> None:
        cfg = settings_manager.get()
        self.java_path.setText(cfg.java.path or "")
        self.memory_min.setValue(cfg.launch.memory_min)
        self.memory_max.setValue(cfg.launch.memory_max)
        self.width_spin.setValue(cfg.launch.resolution_width)
        self.height_spin.setValue(cfg.launch.resolution_height)
        index = self.theme_combo.findData(cfg.ui.theme)
        self.theme_combo.setCurrentIndex(max(0, index))
        index = self.float_combo.findData(cfg.ui.float_mode)
        self.float_combo.setCurrentIndex(max(0, index))
        self.language_combo.setCurrentText(cfg.ui.language)

    def _browse_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 java.exe", "", "Java 可执行文件 (java.exe)"
        )
        if path:
            self.java_path.setText(path)

    def _detect_java(self) -> None:
        from vein_launcher.infrastructure.process.java_detector import JavaDetector

        self.java_result.setText("正在探测…")
        self._bridge.submit(JavaDetector().detect_all(), self.detect_signal.emit)

    def _detect_done(self, installations: Any, error: Optional[BaseException]) -> None:
        if error:
            self.java_result.setText(f"探测失败：{error}")
            return
        if not installations:
            self.java_result.setText("未找到任何 Java，请手动指定路径")
            return
        lines = [
            f"{item.major} ({item.vendor}) · {item.path}" for item in installations[:5]
        ]
        self.java_result.setText("检测到：" + " ｜ ".join(lines))
        self.java_path.setText(str(installations[0].path))

    def _save(self) -> None:
        cfg = settings_manager.get()
        cfg.java.path = self.java_path.text().strip() or None
        cfg.launch.memory_min = self.memory_min.value()
        cfg.launch.memory_max = max(self.memory_max.value(), self.memory_min.value())
        cfg.launch.resolution_width = self.width_spin.value()
        cfg.launch.resolution_height = self.height_spin.value()
        cfg.ui.theme = str(self.theme_combo.currentData())
        cfg.ui.float_mode = str(self.float_combo.currentData())
        cfg.ui.language = self.language_combo.currentText()
        ok = settings_manager.save()
        self.status.setText("已保存 ✅" if ok else "保存失败，请查看日志")
        if ok:
            from vein_launcher.common.events.event_bus import event_bus
            from vein_launcher.common.events.events import EventNames

            event_bus.publish(EventNames.THEME_CHANGED, theme=cfg.ui.theme)
            event_bus.publish(EventNames.SETTINGS_UPDATED, key="ui")
            self._window.notify("设置已保存")


__all__ = ["SettingsPage"]
