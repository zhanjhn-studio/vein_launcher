"""表现层 - 墨刻主题令牌与 QSS 生成

三套纸色：白墨（paper）/ 夜墨（night）/ 青瓷（celadon）。
所有颜色集中在 PALETTES，改色不需要动界面代码。
"""

from __future__ import annotations

from typing import Dict

PALETTES: Dict[str, Dict[str, str]] = {
    "paper": {
        "paper": "#ece6da",
        "paper2": "#f5f1e8",
        "ink": "#141210",
        "ink2": "#4a443c",
        "ink3": "#8b8377",
        "rule": "#cfc6b6",
        "accent": "#b53a2b",
        "accent_ink": "#f8f2e8",
        "accent_soft": "#e7d3c8",
        "ok": "#3f6b52",
        "warn": "#9a6a1e",
        "bad": "#a8362c",
    },
    "night": {
        "paper": "#12100e",
        "paper2": "#191614",
        "ink": "#ece5d7",
        "ink2": "#b9b0a1",
        "ink3": "#7d756a",
        "rule": "#2b2622",
        "accent": "#d4573f",
        "accent_ink": "#1a0f0b",
        "accent_soft": "#2e1d17",
        "ok": "#7aa888",
        "warn": "#d0a45f",
        "bad": "#d96a5c",
    },
    "celadon": {
        "paper": "#dfe4dd",
        "paper2": "#e9ede7",
        "ink": "#1a2320",
        "ink2": "#46544e",
        "ink3": "#7d8a83",
        "rule": "#c3ccc4",
        "accent": "#8a6a2f",
        "accent_ink": "#f6f2e6",
        "accent_soft": "#e0d6be",
        "ok": "#3f6b52",
        "warn": "#8a6a2f",
        "bad": "#9c4a3f",
    },
}

THEME_NAMES = {"paper": "白墨", "night": "夜墨", "celadon": "青瓷"}
DEFAULT_THEME = "paper"


def palette(theme: str) -> Dict[str, str]:
    return PALETTES.get(theme, PALETTES[DEFAULT_THEME])


def qss(theme: str = DEFAULT_THEME) -> str:
    """生成整套样式表（墨刻）"""
    p = palette(theme)
    return f"""
    /* ===== 基础 ===== */
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 12px;
        color: {p['ink']};
    }}
    QWidget {{
        background: {p['paper2']};
    }}
    QMainWindow, QDialog {{
        background: {p['paper']};
    }}

    /* ===== 顶栏 ===== */
    QFrame#TopBar {{
        background: {p['paper2']};
        border-bottom: 1px solid {p['rule']};
    }}
    QLabel#Brand {{
        font-family: "SimSun", "Songti SC", serif;
        font-size: 17px;
        letter-spacing: 6px;
        color: {p['ink']};
    }}
    QLabel#BrandSub {{
        font-size: 10px;
        letter-spacing: 5px;
        color: {p['ink3']};
    }}
    QLineEdit#Search {{
        border: none;
        border-bottom: 1px solid {p['rule']};
        background: transparent;
        padding: 3px 2px;
        color: {p['ink']};
    }}
    QLineEdit#Search:focus {{
        border-bottom: 1px solid {p['accent']};
    }}

    /* ===== 书脊导航 ===== */
    QFrame#Spine {{
        background: {p['paper']};
        border-right: 1px solid {p['rule']};
    }}

    /* ===== 底部发射台 ===== */
    QFrame#Dock {{
        background: {p['paper']};
        border-top: 1px solid {p['rule']};
    }}
    QLabel#DockVersion {{
        font-family: "Consolas", monospace;
        font-size: 13px;
        color: {p['ink']};
    }}
    QLabel#DockMeta {{
        font-size: 9px;
        letter-spacing: 2px;
        color: {p['ink3']};
    }}
    QLabel#DockState {{
        font-family: "Consolas", monospace;
        font-size: 10px;
        color: {p['ink3']};
    }}
    QPushButton#Launch {{
        background: {p['accent']};
        color: {p['accent_ink']};
        border: none;
        padding: 0 40px;
        height: 42px;
        font-family: "SimSun", "Songti SC", serif;
        font-size: 15px;
        letter-spacing: 8px;
    }}
    QPushButton#Launch:hover {{
        background: {p['accent']};
        color: {p['accent_ink']};
    }}
    QPushButton#Launch:disabled {{
        background: {p['rule']};
        color: {p['ink3']};
    }}

    /* ===== 页面标题 ===== */
    QLabel#MastIndex {{
        font-family: "Consolas", monospace;
        font-size: 10px;
        letter-spacing: 2px;
        color: {p['ink3']};
    }}
    QLabel#MastTitle {{
        font-family: "SimSun", "Songti SC", serif;
        font-size: 28px;
        color: {p['ink']};
    }}
    QLabel#MastSub {{
        font-size: 11px;
        color: {p['ink3']};
    }}
    QLabel#PageTitle {{
        font-family: "SimSun", "Songti SC", serif;
        font-size: 26px;
        color: {p['ink']};
    }}
    QLabel#PageSubtitle {{
        font-size: 11px;
        color: {p['ink3']};
    }}
    QLabel#Hint {{
        font-size: 10px;
        color: {p['ink3']};
    }}
    QLabel#Lead {{
        font-family: "SimSun", "Songti SC", serif;
        font-size: 34px;
        color: {p['ink']};
    }}
    QLabel#Lede {{
        font-size: 12px;
        color: {p['ink2']};
    }}
    QLabel#StatKey {{
        font-size: 9px;
        letter-spacing: 2px;
        color: {p['ink3']};
    }}
    QLabel#StatValue {{
        font-family: "Consolas", monospace;
        font-size: 15px;
        color: {p['ink']};
    }}
    QLabel#ProfileName {{
        font-family: "SimSun", "Songti SC", serif;
        font-size: 20px;
        color: {p['ink']};
    }}
    QLabel#ProfileMeta {{
        font-family: "Consolas", monospace;
        font-size: 10px;
        color: {p['ink3']};
    }}
    QLabel#ProfileFace {{
        font-size: 38px;
        background: {p['paper']};
        border: 1px solid {p['ink']};
    }}
    QFrame#Rule {{
        background: {p['rule']};
        max-height: 1px;
        border: none;
    }}

    /* ===== 按钮 ===== */
    QPushButton {{
        background: transparent;
        border: 1px solid {p['ink']};
        padding: 6px 14px;
        color: {p['ink']};
    }}
    QPushButton:hover {{
        background: {p['ink']};
        color: {p['paper2']};
    }}
    QPushButton:disabled {{
        border-color: {p['rule']};
        color: {p['ink3']};
    }}
    QPushButton#Primary {{
        background: {p['accent']};
        border: 1px solid {p['accent']};
        color: {p['accent_ink']};
    }}
    QPushButton#Primary:hover {{
        background: {p['accent']};
        color: {p['accent_ink']};
    }}
    QPushButton#Ghost {{
        border: 1px solid {p['rule']};
        color: {p['ink2']};
    }}
    QPushButton#Ghost:hover {{
        border-color: {p['ink']};
        background: transparent;
        color: {p['ink']};
    }}
    QPushButton#WinBtn {{
        border: none;
        padding: 0;
        font-size: 12px;
        color: {p['ink3']};
    }}
    QPushButton#WinBtn:hover {{
        background: {p['paper']};
        color: {p['ink']};
    }}
    QPushButton#WinClose:hover {{
        background: {p['accent']};
        color: {p['accent_ink']};
    }}

    /* ===== 输入 ===== */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
        background: {p['paper2']};
        border: 1px solid {p['rule']};
        padding: 5px 7px;
        color: {p['ink']};
        selection-background-color: {p['accent']};
        selection-color: {p['accent_ink']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{
        border-color: {p['ink']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 18px;
    }}
    QComboBox QAbstractItemView {{
        background: {p['paper2']};
        border: 1px solid {p['rule']};
        selection-background-color: {p['accent_soft']};
        selection-color: {p['accent']};
        outline: none;
    }}

    /* ===== 列表 / 表格 ===== */
    QListWidget, QTableWidget, QTreeWidget {{
        background: {p['paper2']};
        border: 1px solid {p['rule']};
        outline: none;
    }}
    QListWidget::item, QTableWidget::item {{
        padding: 7px 9px;
        border-bottom: 1px solid {p['rule']};
    }}
    QListWidget::item:selected, QTableWidget::item:selected {{
        background: {p['accent_soft']};
        color: {p['accent']};
    }}
    QHeaderView::section {{
        background: {p['paper2']};
        border: none;
        border-bottom: 1px solid {p['ink']};
        padding: 6px;
        font-size: 9px;
        letter-spacing: 2px;
        color: {p['ink3']};
    }}
    QTableCornerButton::section {{
        background: {p['paper2']};
        border: none;
    }}

    /* ===== 卡片 ===== */
    QFrame#Card {{
        background: {p['paper2']};
        border: 1px solid {p['rule']};
    }}

    /* ===== 滚动条 ===== */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p['rule']};
        min-height: 24px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line,
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
        height: 0;
        width: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p['rule']};
        min-width: 24px;
    }}

    /* ===== 进度条 ===== */
    QProgressBar {{
        background: {p['paper']};
        border: none;
        height: 4px;
        text-align: center;
        color: {p['ink3']};
        font-size: 9px;
    }}
    QProgressBar::chunk {{
        background: {p['accent']};
    }}

    /* ===== 菜单 ===== */
    QMenu {{
        background: {p['paper2']};
        border: 1px solid {p['rule']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 7px 22px 7px 14px;
        color: {p['ink2']};
    }}
    QMenu::item:selected {{
        background: {p['accent_soft']};
        color: {p['accent']};
    }}
    QToolTip {{
        background: {p['paper2']};
        color: {p['ink']};
        border: 1px solid {p['ink']};
        padding: 4px 8px;
    }}

    /* ===== 状态栏 ===== */
    QStatusBar {{
        background: {p['paper']};
        color: {p['ink3']};
        border-top: 1px solid {p['rule']};
    }}

    /* ===== 标签页 ===== */
    QTabWidget::pane {{
        border: 1px solid {p['rule']};
        background: {p['paper2']};
    }}
    QTabBar::tab {{
        background: transparent;
        color: {p['ink3']};
        padding: 7px 14px;
        border-bottom: 1px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {p['ink']};
        border-bottom: 1px solid {p['accent']};
    }}
    """
