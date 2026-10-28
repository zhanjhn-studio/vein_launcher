"""表现层 - 主窗口（左侧导航 + 右侧页面栈）"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.presentation.bridge import AsyncBridge
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)

THEME_DIR = Path(__file__).parent / "theme"

NAV_ITEMS: List[tuple[str, str]] = [
    ("home", "🏠  主页"),
    ("versions", "📦  版本管理"),
    ("mods", "🧩  模组市场"),
    ("plugins", "🔌  插件"),
    ("settings", "⚙️  设置"),
]


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self, context: AppContext, bridge: AsyncBridge):
        super().__init__()
        self._context = context
        self._bridge = bridge
        self._nav_buttons: Dict[str, QPushButton] = {}
        self._pages: Dict[str, QWidget] = {}

        self.setWindowTitle("Vein Launcher")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self._apply_theme("dark")

        self._build_ui()
        self._connect_events()

        # 启动后异步加载数据
        QTimer.singleShot(50, self._bootstrap)

    # ------------------------------------------------------------------
    # 构建
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_content(), 1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("就绪")

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(198)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(6)

        brand = QLabel("VEIN")
        brand.setObjectName("Brand")
        brand.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        layout.addWidget(brand)

        subtitle = QLabel("Minecraft Launcher")
        subtitle.setObjectName("BrandSub")
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        for key, text in NAV_ITEMS:
            button = QPushButton(text)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            layout.addWidget(button)
            self._nav_buttons[key] = button

        layout.addStretch(1)

        self._plugin_badge = QLabel("插件宿主：未启动")
        self._plugin_badge.setObjectName("Hint")
        self._plugin_badge.setWordWrap(True)
        layout.addWidget(self._plugin_badge)

        self._nav_buttons["home"].setChecked(True)
        return sidebar

    def _build_content(self) -> QWidget:
        self._stack = QStackedWidget()
        self._stack.setObjectName("Content")

        from vein_launcher.presentation.ui.pages.home_page import HomePage
        from vein_launcher.presentation.ui.pages.mods_page import ModsPage
        from vein_launcher.presentation.ui.pages.plugins_page import PluginsPage
        from vein_launcher.presentation.ui.pages.settings_page import SettingsPage
        from vein_launcher.presentation.ui.pages.versions_page import VersionsPage

        for key, page_cls in (
            ("home", HomePage),
            ("versions", VersionsPage),
            ("mods", ModsPage),
            ("plugins", PluginsPage),
            ("settings", SettingsPage),
        ):
            page = page_cls(self._context, self._bridge, self)
            self._pages[key] = page
            self._stack.addWidget(page)

        return self._stack

    # ------------------------------------------------------------------
    # 行为
    # ------------------------------------------------------------------
    def switch_page(self, key: str) -> None:
        for nav_key, button in self._nav_buttons.items():
            button.setChecked(nav_key == key)
        page = self._pages.get(key)
        if page is not None:
            self._stack.setCurrentWidget(page)
            if hasattr(page, "on_show"):
                page.on_show()  # type: ignore[attr-defined]
            event_bus.publish(EventNames.PAGE_CHANGED, page=key)

    def notify(self, text: str) -> None:
        """底部状态栏提示"""
        self.statusBar().showMessage(text, 6000)

    def _bootstrap(self) -> None:
        self._bridge.submit(self._context.startup())
        self._bridge.submit(self._refresh_plugin_badge())

    async def _refresh_plugin_badge(self) -> str:
        try:
            plugins = self._context.plugins.list_plugins()
            active = sum(1 for p in plugins if p["active"])
            return f"插件宿主：运行中 · {active}/{len(plugins)} 已激活"
        except Exception:
            return "插件宿主：未启动"

    def _connect_events(self) -> None:
        event_bus.subscribe(EventNames.UI_NOTIFY, self._on_notify)
        event_bus.subscribe(
            EventNames.PLUGIN_HOST_STARTED, lambda **_: self._refresh_badge_async()
        )
        event_bus.subscribe(
            EventNames.PLUGIN_LIST_UPDATED, lambda **_: self._refresh_badge_async()
        )

    def _refresh_badge_async(self) -> None:
        self._bridge.submit(self._refresh_plugin_badge(), self._set_badge)

    def _set_badge(self, result, error) -> None:
        if result:
            self._plugin_badge.setText(result)

    def _on_notify(self, title: str = "", message: str = "", source: str = "", **_) -> None:
        prefix = "插件" if source == "plugin" else "提示"
        self.notify(f"[{prefix}] {title}：{message}")

    # ------------------------------------------------------------------
    def _apply_theme(self, theme: str) -> None:
        qss_path = THEME_DIR / f"{theme}.qss"
        if qss_path.is_file():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        else:
            logger.warning("主题文件缺失：%s", qss_path)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        """退出前优雅关闭插件宿主与网络会话"""
        logger.info("窗口关闭，正在释放资源")
        try:
            self._bridge.submit(self._context.shutdown())
        finally:
            self._bridge.shutdown()
        super().closeEvent(event)


__all__ = ["MainWindow"]
