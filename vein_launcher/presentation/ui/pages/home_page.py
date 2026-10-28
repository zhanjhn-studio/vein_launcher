"""启动页 —— 只用真实数据

展示：本地已安装实例、当前账号（真实头像）、该实例下的真实存档。
没有任何数据时显示空状态，不编造。
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from vein_launcher.common.utils.path_utils import get_version_dir
from vein_launcher.presentation.ui.avatar import AvatarLoader, default_head

logger = logging.getLogger(__name__)


def scan_worlds(version_id: str) -> List[dict]:
    """扫描实例 saves/ 目录，返回真实存档列表"""
    saves = get_version_dir(version_id) / "saves"
    if not saves.is_dir():
        return []
    worlds = []
    for child in saves.iterdir():
        if not child.is_dir():
            continue
        try:
            mtime = datetime.fromtimestamp(child.stat().st_mtime)
        except OSError:
            continue
        worlds.append({"name": child.name, "mtime": mtime, "path": child})
    worlds.sort(key=lambda w: w["mtime"], reverse=True)
    return worlds


class HomePage(QWidget):
    """启动页"""

    launch_failed = Signal(str)

    def __init__(self, context, bridge, window):
        super().__init__()
        self._ctx = context
        self._bridge = bridge
        self._window = window
        self._avatar = AvatarLoader(self)
        self._avatar.loaded.connect(self._on_avatar)
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(48, 34, 48, 34)
        layout.setSpacing(18)
        scroll.setWidget(content)

        # ---- 主区块 ----
        hero = QFrame()
        hero.setObjectName("Card")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(32, 28, 32, 28)
        hero_layout.setSpacing(10)

        title = QLabel("启动")
        title.setObjectName("HeroTitle")
        hero_layout.addWidget(title)

        self.sub_label = QLabel("读取本地实例中…")
        self.sub_label.setObjectName("HeroSub")
        self.sub_label.setWordWrap(True)
        hero_layout.addWidget(self.sub_label)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(220)
        self.version_combo.currentIndexChanged.connect(self._on_version_changed)
        row.addWidget(self.version_combo, 0)

        self.launch_button = QPushButton("启动游戏")
        self.launch_button.setObjectName("Primary")
        self.launch_button.clicked.connect(self.launch)
        row.addWidget(self.launch_button)
        row.addStretch(1)
        hero_layout.addSpacing(6)
        hero_layout.addLayout(row)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("CardMeta")
        hero_layout.addWidget(self.hint_label)
        layout.addWidget(hero)

        # ---- 账号 + 统计 ----
        mid = QHBoxLayout()
        mid.setSpacing(18)

        account = QFrame()
        account.setObjectName("Card")
        acc_layout = QHBoxLayout(account)
        acc_layout.setContentsMargins(22, 20, 22, 20)
        acc_layout.setSpacing(16)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(64, 64)
        self.avatar_label.setPixmap(default_head("steve", 64))
        self.avatar_label.setScaledContents(True)
        acc_layout.addWidget(self.avatar_label)

        acc_text = QVBoxLayout()
        acc_text.setSpacing(3)
        self.account_name = QLabel("未登录")
        self.account_name.setObjectName("CardTitle")
        self.account_type = QLabel("添加账号后才能启动正版")
        self.account_type.setObjectName("CardMeta")
        acc_text.addWidget(self.account_name)
        acc_text.addWidget(self.account_type)
        acc_layout.addLayout(acc_text, 1)

        self.account_button = QPushButton("添加离线账号")
        self.account_button.clicked.connect(self._add_offline)
        acc_layout.addWidget(self.account_button)
        mid.addWidget(account, 3)

        stats = QFrame()
        stats.setObjectName("Card")
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(22, 20, 22, 20)
        stats_layout.setSpacing(28)
        self.stat_instances = self._stat(stats_layout, "实例", "0")
        self.stat_worlds = self._stat(stats_layout, "存档", "0")
        self.stat_accounts = self._stat(stats_layout, "账号", "0")
        mid.addWidget(stats, 2)
        layout.addLayout(mid)

        # ---- 世界 ----
        head = QHBoxLayout()
        world_title = QLabel("存档")
        world_title.setObjectName("SectionTitle")
        self.world_count = QLabel("")
        self.world_count.setObjectName("SectionSub")
        head.addWidget(world_title)
        head.addWidget(self.world_count)
        head.addStretch(1)
        open_folder = QPushButton("打开存档目录")
        open_folder.setObjectName("Link")
        open_folder.clicked.connect(self._open_saves)
        head.addWidget(open_folder)
        layout.addSpacing(4)
        layout.addLayout(head)

        self.worlds_box = QVBoxLayout()
        self.worlds_box.setSpacing(8)
        layout.addLayout(self.worlds_box)
        layout.addStretch(1)

    @staticmethod
    def _stat(layout: QHBoxLayout, key: str, value: str) -> QLabel:
        box = QVBoxLayout()
        box.setSpacing(2)
        k = QLabel(key)
        k.setObjectName("CardMeta")
        v = QLabel(value)
        v.setObjectName("SectionTitle")
        box.addWidget(k)
        box.addWidget(v)
        layout.addLayout(box)
        return v

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self._refresh_versions()
        self._refresh_account()
        self._refresh_worlds()

    def _refresh_versions(self) -> None:
        installed = self._ctx.versions.list_installed_versions()
        current = self.version_combo.currentData()
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for item in installed:
            self.version_combo.addItem(item["id"], item["id"])
        if current:
            index = self.version_combo.findData(current)
            if index >= 0:
                self.version_combo.setCurrentIndex(index)
        self.version_combo.blockSignals(False)

        count = len(installed)
        self.stat_instances.setText(str(count))
        if count == 0:
            self.sub_label.setText("还没有安装任何游戏版本。先去「下载」装一个，这里才会出现可启动的实例。")
            self.launch_button.setEnabled(False)
            self.version_combo.setEnabled(False)
        else:
            self.sub_label.setText(f"共 {count} 个本地实例，选择一个启动。")
            self.launch_button.setEnabled(True)
            self.version_combo.setEnabled(True)
        self._refresh_worlds()

    def _refresh_account(self) -> None:
        accounts = self._ctx.accounts.list_accounts()
        self.stat_accounts.setText(str(len(accounts)))
        account = self._ctx.accounts.current()
        if account is None:
            self.account_name.setText("未登录")
            self.account_type.setText("目前只能用离线账号启动")
            self.avatar_label.setPixmap(default_head("steve", 64))
            self.account_button.setText("添加离线账号")
            self._window.set_account("未登录")
            return

        self.account_name.setText(account.username)
        kind = "离线账号" if getattr(account, "account_type", "offline") == "offline" else "微软账号"
        self.account_type.setText(kind)
        self.account_button.setText("切换账号")
        self._window.set_account(account.username)
        uuid = getattr(account, "mc_selected_profile", None)
        self._avatar.load(account.username, uuid, 64)

    def _on_avatar(self, key: str, pixmap) -> None:
        self.avatar_label.setPixmap(pixmap)

    def _refresh_worlds(self) -> None:
        while self.worlds_box.count():
            item = self.worlds_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        version_id = self.version_combo.currentData()
        worlds = scan_worlds(version_id) if version_id else []
        self.stat_worlds.setText(str(len(worlds)))
        self.world_count.setText(f"· {len(worlds)} 个" if worlds else "")

        if not version_id:
            self._add_empty("未选择实例")
            return
        if not worlds:
            self._add_empty(f"{version_id} 还没有存档，进入游戏创建后会出现在这里")
            return

        for world in worlds[:8]:
            card = QFrame()
            card.setObjectName("Card")
            row = QHBoxLayout(card)
            row.setContentsMargins(18, 12, 18, 12)
            name = QLabel(world["name"])
            name.setObjectName("CardTitle")
            meta = QLabel(world["mtime"].strftime("%Y-%m-%d %H:%M"))
            meta.setObjectName("CardMeta")
            row.addWidget(name)
            row.addStretch(1)
            row.addWidget(meta)
            self.worlds_box.addWidget(card)

    def _add_empty(self, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("Empty")
        label.setWordWrap(True)
        self.worlds_box.addWidget(label)

    # ------------------------------------------------------------------
    def _on_version_changed(self) -> None:
        self._refresh_worlds()

    def _add_offline(self) -> None:
        accounts = self._ctx.accounts.list_accounts()
        if accounts:
            names = [a["username"] for a in accounts]
            choice, ok = QInputDialog.getItem(self, "切换账号", "选择账号", names, 0, False)
            if ok and choice:
                for acc in accounts:
                    if acc["username"] == choice:
                        self._ctx.accounts.select(acc["id"])
                        break
                self._refresh_account()
            return

        name, ok = QInputDialog.getText(self, "添加离线账号", "用户名（3–16 个字符）")
        if not ok:
            return
        try:
            self._ctx.accounts.add_offline(name.strip())
        except Exception as exc:
            self._window.notify(f"添加失败：{exc}")
            return
        self._refresh_account()

    def _open_saves(self) -> None:
        version_id = self.version_combo.currentData()
        if not version_id:
            return
        import os

        saves = get_version_dir(version_id) / "saves"
        saves.mkdir(parents=True, exist_ok=True)
        os.startfile(str(saves))  # noqa: S606 - Windows 打开资源管理器

    # ------------------------------------------------------------------
    @property
    def selected_version(self) -> Optional[str]:
        return self.version_combo.currentData()

    def launch(self) -> None:
        version_id = self.selected_version
        if not version_id:
            self.launch_failed.emit("没有可启动的实例，请先下载一个版本")
            return

        account = self._ctx.accounts.current()

        def done(result: Any, error: Optional[BaseException]) -> None:
            if error:
                logger.error("启动失败：%s", error)
                self.launch_failed.emit(str(error))
                return
            self.hint_label.setText(f"已启动，PID {result}")

        self.hint_label.setText("正在构建启动参数…")
        self._bridge.submit(
            self._ctx.launcher.launch_with_account(version_id, account), done
        )


__all__ = ["HomePage", "scan_worlds"]
