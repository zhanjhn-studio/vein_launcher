"""墨刻 - 主窗口

结构：顶栏 / 书脊导航 + 页面栈 / 底部发射台。
最小化后主窗口隐藏，只留置顶悬浮球（圆盘或灵动岛）。
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.config.settings import settings_manager
from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.version import __version__
from vein_launcher.presentation.bridge import AsyncBridge
from vein_launcher.presentation.context import AppContext
from vein_launcher.presentation.ui.floating import FloatingOrb
from vein_launcher.presentation.ui.theme import tokens
from vein_launcher.presentation.ui.widgets.spine import SpineButton

logger = logging.getLogger(__name__)

NAV = [
    ("launch", "01", "启动"),
    ("download", "02", "下载"),
    ("version", "03", "版本"),
    ("plugin", "04", "插件"),
    ("setting", "05", "设置"),
]


class MainWindow(QMainWindow):
    """Vein Launcher 主窗口（墨刻）"""

    def __init__(self, context: AppContext, bridge: AsyncBridge):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._theme = settings_manager.get().ui.theme or tokens.DEFAULT_THEME
        self._nav_buttons: Dict[str, SpineButton] = {}
        self._pages: Dict[str, QWidget] = {}
        self._orb: Optional[FloatingOrb] = None
        self._drag_pos: Optional[QPoint] = None

        self.setWindowTitle(f"Vein Launcher {__version__}")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.resize(1180, 800)
        self.setMinimumSize(1000, 680)
        self.apply_theme(self._theme)

        self._build()
        self._connect_events()
        QTimer.singleShot(80, self._bootstrap)

    # ------------------------------------------------------------------
    # 构建
    # ------------------------------------------------------------------
    def _build(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_topbar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._build_spine())

        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack, 1)
        layout.addWidget(body, 1)

        layout.addWidget(self._build_dock())

        self.setCentralWidget(root)
        self._build_pages()
        self.switch_page("launch")

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(22, 0, 12, 0)
        layout.setSpacing(16)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(0)
        brand = QLabel("VEIN")
        brand.setObjectName("Brand")
        brand.setFont(QFont("SimSun", 17))
        sub = QLabel("墨刻")
        sub.setObjectName("BrandSub")
        brand_box.addWidget(brand)
        brand_box.addWidget(sub)
        layout.addLayout(brand_box)

        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("搜索版本 / 模组 / 插件")
        self.search.setFixedWidth(300)
        self.search.returnPressed.connect(self._on_search)
        layout.addWidget(self.search)
        layout.addStretch(1)

        self.account_label = QLabel("未登录")
        self.account_label.setObjectName("MastSub")
        layout.addWidget(self.account_label)

        for text, name, handler, tip in (
            ("⤡", "WinBtn", self.minimize_to_orb, "收起为悬浮球"),
            ("—", "WinBtn", self.minimize_to_orb, "最小化"),
            ("□", "WinBtn", self._toggle_max, "最大化"),
            ("✕", "WinClose", self.close, "关闭"),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setFixedSize(30, 26)
            button.setToolTip(tip)
            button.clicked.connect(handler)
            layout.addWidget(button)

        return bar

    def _build_spine(self) -> QWidget:
        spine = QFrame()
        spine.setObjectName("Spine")
        spine.setFixedWidth(104)
        layout = QVBoxLayout(spine)
        layout.setContentsMargins(0, 14, 0, 10)
        layout.setSpacing(0)

        for key, index, text in NAV:
            button = SpineButton(index, text, self._theme)
            button.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            layout.addWidget(button)
            self._nav_buttons[key] = button
            if key == "version":
                spacer = QWidget()
                spacer.setFixedHeight(12)
                layout.addWidget(spacer)

        layout.addStretch(1)
        stamp = QLabel("VEIN · " + __version__)
        stamp.setObjectName("Hint")
        stamp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stamp)
        return spine

    def _build_dock(self) -> QWidget:
        dock = QFrame()
        dock.setObjectName("Dock")
        dock.setFixedHeight(64)
        layout = QHBoxLayout(dock)
        layout.setContentsMargins(26, 0, 22, 0)
        layout.setSpacing(16)

        ver_box = QVBoxLayout()
        ver_box.setSpacing(1)
        self.dock_version = QLabel("未选择版本")
        self.dock_version.setObjectName("DockVersion")
        self.dock_meta = QLabel("OFFLINE")
        self.dock_meta.setObjectName("DockMeta")
        ver_box.addWidget(self.dock_version)
        ver_box.addWidget(self.dock_meta)
        layout.addLayout(ver_box)
        layout.addSpacing(10)

        self.dock_state = QLabel("就绪")
        self.dock_state.setObjectName("DockState")
        layout.addWidget(self.dock_state)
        layout.addStretch(1)

        self.launch_button = QPushButton("启 动")
        self.launch_button.setObjectName("Launch")
        self.launch_button.clicked.connect(self._on_launch)
        layout.addWidget(self.launch_button)
        return dock

    def _build_pages(self) -> None:
        from vein_launcher.presentation.ui.pages.download_page import DownloadPage
        from vein_launcher.presentation.ui.pages.home_page import HomePage
        from vein_launcher.presentation.ui.pages.plugins_page import PluginsPage
        from vein_launcher.presentation.ui.pages.settings_page import SettingsPage
        from vein_launcher.presentation.ui.pages.versions_page import VersionsPage

        for key, cls in (
            ("launch", HomePage),
            ("download", DownloadPage),
            ("version", VersionsPage),
            ("plugin", PluginsPage),
            ("setting", SettingsPage),
        ):
            page = cls(self._ctx, self._bridge, self)
            if hasattr(page, "launch_failed"):
                page.launch_failed.connect(self.notify)  # type: ignore[attr-defined]
            self._pages[key] = page
            self._stack.addWidget(page)

    # ------------------------------------------------------------------
    # 行为
    # ------------------------------------------------------------------
    def switch_page(self, key: str) -> None:
        for nav_key, button in self._nav_buttons.items():
            button.setChecked(nav_key == key)
        page = self._pages.get(key)
        if page is None:
            return
        self._stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()  # type: ignore[attr-defined]
        self._sync_dock()
        event_bus.publish(EventNames.PAGE_CHANGED, page=key)

    def _sync_dock(self) -> None:
        home = self._pages.get("launch")
        version = getattr(home, "selected_version", None) if home else None
        self.dock_version.setText(version or "未选择版本")

    def notify(self, text: str) -> None:
        self.dock_state.setText(text)
        QTimer.singleShot(5000, lambda: self.dock_state.setText("就绪"))

    def set_account(self, username: str) -> None:
        self.account_label.setText(username)
        self.dock_meta.setText(f"MICROSOFT · {username.upper()}")

    def _on_search(self) -> None:
        query = self.search.text().strip()
        if not query:
            return
        self.switch_page("download")
        page = self._pages["download"]
        if hasattr(page, "search_input"):
            page.search_input.setText(query)  # type: ignore[attr-defined]
            page._search()  # type: ignore[attr-defined]

    def _on_launch(self) -> None:
        home = self._pages.get("launch")
        if home is None:
            return
        self.launch_button.setEnabled(False)
        self.dock_state.setText("启动中…")
        try:
            home.launch()  # type: ignore[attr-defined]
        finally:
            QTimer.singleShot(1500, lambda: self.launch_button.setEnabled(True))

    # ------------------------------------------------------------------
    # 主题
    # ------------------------------------------------------------------
    def apply_theme(self, theme: str) -> None:
        self._theme = theme if theme in tokens.PALETTES else tokens.DEFAULT_THEME
        self.setStyleSheet(tokens.qss(self._theme))
        for button in getattr(self, "_nav_buttons", {}).values():
            button.set_theme(self._theme)
        if self._orb is not None:
            self._orb.set_theme(self._theme)

    # ------------------------------------------------------------------
    # 悬浮球
    # ------------------------------------------------------------------
    def minimize_to_orb(self) -> None:
        self._ensure_orb()
        assert self._orb is not None
        mode = settings_manager.get().ui.float_mode or "disc"
        self._orb.set_mode(mode)
        self._orb.move_to_default(QApplication.primaryScreen())
        self._orb.show()
        self._orb.raise_()
        self.hide()

    def _ensure_orb(self) -> None:
        if self._orb is not None:
            return
        self._orb = FloatingOrb(self._theme, "disc")
        self._orb.launch_requested.connect(self._launch_from_orb)
        self._orb.restore_requested.connect(self.restore_from_orb)
        self._orb.switch_mode_requested.connect(self._toggle_orb_mode)
        self._orb.navigate_requested.connect(self._navigate_from_orb)

    def _toggle_orb_mode(self) -> None:
        if self._orb is None:
            return
        new_mode = "island" if self._orb.mode == "disc" else "disc"
        self._orb.set_mode(new_mode)
        self._orb.move_to_default(QApplication.primaryScreen())
        settings = settings_manager.get()
        settings.ui.float_mode = new_mode
        settings_manager.save()
        self.notify(f"悬浮形态：{'灵动岛' if new_mode == 'island' else '圆盘'}")

    def _navigate_from_orb(self, key: str) -> None:
        self.restore_from_orb()
        self.switch_page(key)

    def _launch_from_orb(self) -> None:
        self._on_launch()

    def restore_from_orb(self) -> None:
        if self._orb is not None:
            self._orb.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # 窗口拖动 / 最大化
    # ------------------------------------------------------------------
    def _toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 56:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.position().y() < 56:
            self._toggle_max()
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------
    def _connect_events(self) -> None:
        event_bus.subscribe(EventNames.THEME_CHANGED, self._on_theme_changed)
        event_bus.subscribe(EventNames.GAME_RUNNING, self._on_game_running)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)
        event_bus.subscribe(EventNames.UI_NOTIFY, self._on_notify)

    def _on_theme_changed(self, theme: str = "", **_):
        self.apply_theme(theme)

    def _on_game_running(self, pid: int = 0, **_):
        self.dock_state.setText(f"运行中 · PID {pid}")

    def _on_game_exited(self, exit_code: int = 0, **_):
        self.dock_state.setText(f"已退出 · code {exit_code}")

    def _on_notify(self, title: str = "", message: str = "", **_):
        self.notify(f"{title}：{message}")

    # ------------------------------------------------------------------
    def _bootstrap(self) -> None:
        self._bridge.submit(self._ctx.startup())
        self.switch_page("launch")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 约定
        logger.info("窗口关闭，释放资源")
        if self._orb is not None:
            self._orb.hide()
        try:
            self._bridge.submit(self._ctx.shutdown())
        finally:
            self._bridge.shutdown()
        super().closeEvent(event)


__all__ = ["MainWindow"]
