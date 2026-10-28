"""表现层 - Apple 风格主题令牌

参考 apple.com 的视觉语言：大留白、细字重、浅灰底白卡、蓝色单一强调。
两套：light（默认）/ dark。改色只动 PALETTES。
"""

from __future__ import annotations

from typing import Dict

PALETTES: Dict[str, Dict[str, str]] = {
    "light": {
        "bg": "#f5f5f7",
        "surface": "#ffffff",
        "surface2": "#fbfbfd",
        "text": "#1d1d1f",
        "text2": "#6e6e73",
        "text3": "#86868b",
        "line": "#d2d2d7",
        "accent": "#0071e3",
        "accent_ink": "#ffffff",
        "accent_soft": "#e8f1fd",
        "ok": "#1d7f43",
        "warn": "#b25000",
        "bad": "#c0392b",
    },
    "dark": {
        "bg": "#000000",
        "surface": "#1d1d1f",
        "surface2": "#161617",
        "text": "#f5f5f7",
        "text2": "#a1a1a6",
        "text3": "#86868b",
        "line": "#3a3a3c",
        "accent": "#2997ff",
        "accent_ink": "#ffffff",
        "accent_soft": "#10243a",
        "ok": "#5ac878",
        "warn": "#f0a35e",
        "bad": "#ff6b5e",
    },
}

THEME_NAMES = {"light": "浅色", "dark": "深色"}
DEFAULT_THEME = "light"

FONT_STACK = '"Segoe UI", "Microsoft YaHei UI", system-ui, sans-serif'
FONT_DISPLAY = '"Segoe UI Display", "Segoe UI", "Microsoft YaHei UI", sans-serif'


def palette(theme: str) -> Dict[str, str]:
    return PALETTES.get(theme, PALETTES[DEFAULT_THEME])


def qss(theme: str = DEFAULT_THEME) -> str:
    p = palette(theme)
    return f"""
    * {{
        font-family: {FONT_STACK};
        font-size: 13px;
        color: {p['text']};
    }}
    QWidget {{
        background: {p['bg']};
    }}
    QMainWindow, QDialog {{
        background: {p['bg']};
    }}

    /* ===== 顶部导航 ===== */
    QFrame#TopBar {{
        background: {p['bg']};
        border-bottom: 1px solid {p['line']};
    }}
    QLabel#LogoText {{
        font-family: {FONT_DISPLAY};
        font-size: 15px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: {p['text']};
    }}
    QPushButton#NavTab {{
        background: transparent;
        border: none;
        padding: 6px 14px;
        border-radius: 8px;
        color: {p['text2']};
        font-size: 13px;
    }}
    QPushButton#NavTab:hover {{
        color: {p['text']};
    }}
    QPushButton#NavTab:checked {{
        color: {p['accent']};
        font-weight: 600;
    }}

    /* ===== 标题 ===== */
    QLabel#HeroTitle {{
        font-family: {FONT_DISPLAY};
        font-size: 40px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: {p['text']};
    }}
    QLabel#HeroSub {{
        font-size: 15px;
        color: {p['text2']};
    }}
    QLabel#SectionTitle {{
        font-family: {FONT_DISPLAY};
        font-size: 22px;
        font-weight: 600;
        color: {p['text']};
    }}
    QLabel#SectionSub {{
        font-size: 12px;
        color: {p['text3']};
    }}
    QLabel#CardTitle {{
        font-size: 14px;
        font-weight: 600;
        color: {p['text']};
    }}
    QLabel#CardMeta {{
        font-size: 11px;
        color: {p['text3']};
    }}
    QLabel#Empty {{
        font-size: 13px;
        color: {p['text3']};
    }}
    /* 旧页面标题别名，保证其他页排版一致 */
    QLabel#PageTitle {{
        font-family: {FONT_DISPLAY};
        font-size: 26px;
        font-weight: 600;
        color: {p['text']};
    }}
    QLabel#PageSubtitle, QLabel#Hint {{
        font-size: 12px;
        color: {p['text3']};
    }}
    QLabel#MastTitle {{
        font-family: {FONT_DISPLAY};
        font-size: 26px;
        font-weight: 600;
        color: {p['text']};
    }}
    QLabel#MastIndex {{
        font-size: 11px;
        color: {p['text3']};
    }}
    QLabel#MastSub {{
        font-size: 12px;
        color: {p['text2']};
    }}

    /* ===== 卡片 ===== */
    QFrame#Card {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 18px;
    }}
    QFrame#Card:hover {{
        border-color: {p['text3']};
    }}

    /* ===== 按钮 ===== */
    QPushButton {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 980px;
        padding: 7px 18px;
        color: {p['text']};
        font-size: 13px;
    }}
    QPushButton:hover {{
        border-color: {p['text3']};
    }}
    QPushButton:pressed {{
        background: {p['surface2']};
    }}
    QPushButton:disabled {{
        color: {p['text3']};
        border-color: {p['line']};
    }}
    QPushButton#Primary {{
        background: {p['accent']};
        border: 1px solid {p['accent']};
        color: {p['accent_ink']};
        font-weight: 600;
        padding: 10px 28px;
        font-size: 14px;
    }}
    QPushButton#Primary:hover {{
        background: {p['accent']};
        border-color: {p['accent']};
    }}
    QPushButton#Primary:disabled {{
        background: {p['line']};
        border-color: {p['line']};
        color: {p['text3']};
    }}
    QPushButton#Link {{
        background: transparent;
        border: none;
        color: {p['accent']};
        padding: 2px 0;
        font-size: 13px;
    }}
    QPushButton#Link:hover {{
        text-decoration: underline;
    }}

    /* ===== 输入 ===== */
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 10px;
        padding: 7px 10px;
        color: {p['text']};
        selection-background-color: {p['accent']};
        selection-color: #ffffff;
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{
        border-color: {p['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 10px;
        selection-background-color: {p['accent_soft']};
        selection-color: {p['accent']};
        outline: none;
    }}

    /* ===== 列表 / 表格 ===== */
    QListWidget, QTableWidget, QTreeWidget {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 14px;
        outline: none;
    }}
    QListWidget::item, QTableWidget::item {{
        padding: 9px 12px;
        border-bottom: 1px solid {p['line']};
    }}
    QListWidget::item:selected, QTableWidget::item:selected {{
        background: {p['accent_soft']};
        color: {p['accent']};
    }}
    QHeaderView::section {{
        background: {p['surface']};
        border: none;
        border-bottom: 1px solid {p['line']};
        padding: 8px 12px;
        font-size: 11px;
        color: {p['text3']};
    }}
    QTableCornerButton::section {{
        background: {p['surface']};
        border: none;
    }}

    /* ===== 滚动条 ===== */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['line']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line,
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p['line']};
        border-radius: 4px;
    }}

    /* ===== 进度 ===== */
    QProgressBar {{
        background: {p['line']};
        border: none;
        border-radius: 3px;
        height: 6px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {p['accent']};
        border-radius: 3px;
    }}

    /* ===== 菜单 / 提示 ===== */
    QMenu {{
        background: {p['surface']};
        border: 1px solid {p['line']};
        border-radius: 12px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 7px 20px 7px 14px;
        border-radius: 7px;
        color: {p['text']};
    }}
    QMenu::item:selected {{
        background: {p['accent_soft']};
        color: {p['accent']};
    }}
    QToolTip {{
        background: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['line']};
        border-radius: 6px;
        padding: 5px 8px;
    }}
    QStatusBar {{
        background: {p['bg']};
        color: {p['text3']};
        border-top: 1px solid {p['line']};
    }}
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {p['text2']};
        padding: 8px 16px;
        border: none;
    }}
    QTabBar::tab:selected {{
        color: {p['accent']};
        font-weight: 600;
    }}
    """
