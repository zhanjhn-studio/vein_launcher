"""主窗口 —— Apple 风格 + 原生窗口边框

原生标题栏（关闭/最小化/最大化交给系统），应用内只做顶部导航与内容。
「悬浮」是一个普通按钮：把主窗口收成置顶圆盘/灵动岛。
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
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
from vein_launcher.presentation.ui.assets import asset
from vein_launcher.presentation.ui.floating import FloatingOrb
from vein_launcher.presentation.ui.theme import tokens

logger = logging.getLogger(__name__)

NAV = [
    ("launch", "启动"),
    ("download", "下载"),
    ("version", "版本"),
    ("plugin", "插件"),
    ("setting", "设置"),
]


def _logo_pixmap(size: int = 26) -> Optional[QPixmap]:
    path = asset("logo.svg")
    if path is None:
        return None
    try:
        from PySide6.QtSvg import QSvgRenderer

        renderer = QSvgRenderer(str(path))
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter

        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return pix
    except Exception:  # QtSvg 缺失时不影响启动
        logger.debug("logo 渲染失败", exc_info=True)
        return None


class MainWindow(QMainWindow):
    """Vein Launcher 主窗口"""

    def __init__(self, context: AppContext, bridge: AsyncBridge):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._theme = settings_manager.get().ui.theme or tokens.DEFAULT_THEME
        self._nav_buttons: Dict[str, QPushButton] = {}
        self._pages: Dict[str, QWidget] = {}
        self._orb: Optional[FloatingOrb] = None

        self.setWindowTitle(f"Vein Launcher {__version__}")
        self.resize(1180, 780)
        self.setMinimumSize(980, 640)
        self.apply_theme(self._theme)

        self._build()
        self._connect_events()
        QTimer.singleShot(80, self._bootstrap)

    # ------------------------------------------------------------------
    def _build(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_topbar())

        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("就绪")
        self._build_pages()
        self.switch_page("launch")

        icon = _logo_pixmap(64)
        if icon is not None:
            self.setWindowIcon(QIcon(icon))

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        logo = QLabel()
        pix = _logo_pixmap(26)
        if pix is not None:
            logo.setPixmap(pix)
        else:
            logo.setText("V")
            logo.setObjectName("LogoText")
        layout.addWidget(logo)

        name = QLabel("Vein")
        name.setObjectName("LogoText")
        layout.addWidget(name)
        layout.addSpacing(18)

        for key, label in NAV:
            button = QPushButton(label)
            button.setObjectName("NavTab")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            self._nav_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

        self.account_chip = QPushButton("未登录")
        self.account_chip.setObjectName("Link")
        self.account_chip.clicked.connect(lambda: self.switch_page("setting"))
        layout.addWidget(self.account_chip)

        float_btn = QPushButton("悬浮")
        float_btn.setObjectName("Link")
        float_btn.clicked.connect(self.minimize_to_orb)
        layout.addWidget(float_btn)

        return bar

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
    def switch_page(self, key: str) -> None:
        for nav_key, button in self._nav_buttons.items():
            button.setChecked(nav_key == key)
        page = self._pages.get(key)
        if page is None:
            return
        self._stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()  # type: ignore[attr-defined]
        event_bus.publish(EventNames.PAGE_CHANGED, page=key)

    def notify(self, text: str) -> None:
        self.statusBar().showMessage(str(text), 6000)
        QTimer.singleShot(6000, lambda: self.statusBar().showMessage("就绪"))

    def set_account(self, username: str) -> None:
        self.account_chip.setText(username or "未登录")

    # ------------------------------------------------------------------
    def apply_theme(self, theme: str) -> None:
        self._theme = theme if theme in tokens.PALETTES else tokens.DEFAULT_THEME
        self.setStyleSheet(tokens.qss(self._theme))
        if self._orb is not None:
            self._orb.set_theme(self._theme)

    # ------------------------------------------------------------------
    def _ensure_orb(self) -> None:
        if self._orb is not None:
            return
        mode = settings_manager.get().ui.float_mode or "disc"
        self._orb = FloatingOrb(self._theme, mode)
        self._orb.launch_requested.connect(self._launch_from_orb)
        self._orb.restore_requested.connect(self.restore_from_orb)
        self._orb.switch_mode_requested.connect(self._toggle_orb_mode)
        self._orb.navigate_requested.connect(self._navigate_from_orb)

    def minimize_to_orb(self) -> None:
        self._ensure_orb()
        assert self._orb is not None
        self._orb.move_to_default(QApplication.primaryScreen())
        self._orb.show()
        self._orb.raise_()
        self.hide()

    def restore_from_orb(self) -> None:
        if self._orb is not None:
            self._orb.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _toggle_orb_mode(self) -> None:
        if self._orb is None:
            return
        new_mode = "island" if self._orb.mode == "disc" else "disc"
        self._orb.set_mode(new_mode)
        self._orb.move_to_default(QApplication.primaryScreen())
        settings = settings_manager.get()
        settings.ui.float_mode = new_mode
        settings_manager.save()
        self.notify("悬浮形态：" + ("灵动岛" if new_mode == "island" else "圆盘"))

    def _navigate_from_orb(self, key: str) -> None:
        self.restore_from_orb()
        self.switch_page(key)

    def _launch_from_orb(self) -> None:
        page = self._pages.get("launch")
        if page is not None:
            page.launch()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    def _connect_events(self) -> None:
        event_bus.subscribe(EventNames.THEME_CHANGED, self._on_theme_changed)
        event_bus.subscribe(EventNames.GAME_RUNNING, self._on_game_running)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)
        event_bus.subscribe(EventNames.UI_NOTIFY, self._on_notify)

    def _on_theme_changed(self, theme: str = "", **_):
        self.apply_theme(theme)

    def _on_game_running(self, pid: int = 0, **_):
        self.statusBar().showMessage(f"游戏运行中 · PID {pid}")

    def _on_game_exited(self, exit_code: int = 0, **_):
        self.statusBar().showMessage(f"游戏已退出 · code {exit_code}")

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
