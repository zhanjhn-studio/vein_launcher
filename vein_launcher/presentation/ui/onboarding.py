"""墨刻 - 首启引导对话框

第一步：语言；第二步：纸色。完成后由调用方写入 first_run.log。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.presentation.ui.theme.tokens import THEME_NAMES


class OnboardingDialog(QDialog):
    """首启引导"""

    def __init__(self, theme: str = "paper", language: str = "zh_CN", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 Vein Launcher")
        self.setModal(True)
        self.setFixedSize(520, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 24)
        layout.setSpacing(12)

        kicker = QLabel("FIRST RUN / 初次见面")
        kicker.setObjectName("MastIndex")
        layout.addWidget(kicker)

        title = QLabel("选择你的第一印象")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            "启动器会创建数据目录，并写入 first_run.log 记录本次初始化。\n"
            "语言与纸色之后都可以在设置里改。"
        )
        desc.setObjectName("Hint")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(8)

        lang_row = QHBoxLayout()
        lang_label = QLabel("界面语言")
        lang_label.setObjectName("MastSub")
        lang_label.setFixedWidth(90)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("简体中文", "zh_CN")
        self.lang_combo.addItem("English", "en_US")
        self.lang_combo.setCurrentIndex(0 if language == "zh_CN" else 1)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.lang_combo, 1)
        layout.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_label = QLabel("纸色主题")
        theme_label.setObjectName("MastSub")
        theme_label.setFixedWidth(90)
        self.theme_combo = QComboBox()
        for key, name in THEME_NAMES.items():
            self.theme_combo.addItem(f"{name}（{key}）", key)
        index = self.theme_combo.findData(theme)
        self.theme_combo.setCurrentIndex(max(0, index))
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo, 1)
        layout.addLayout(theme_row)

        layout.addStretch(1)

        footer = QHBoxLayout()
        hint = QLabel("v0.0.1-beta · 墨刻")
        hint.setObjectName("Hint")
        footer.addWidget(hint)
        footer.addStretch(1)

        start = QPushButton("开始使用")
        start.setObjectName("Primary")
        start.clicked.connect(self.accept)
        footer.addWidget(start)
        layout.addLayout(footer)

        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

    # ------------------------------------------------------------------
    @property
    def selected_language(self) -> str:
        return str(self.lang_combo.currentData())

    @property
    def selected_theme(self) -> str:
        return str(self.theme_combo.currentData())


__all__ = ["OnboardingDialog"]
