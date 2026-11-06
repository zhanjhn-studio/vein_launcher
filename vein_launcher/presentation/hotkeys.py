"""Windows 全局热键：RegisterHotKey + Qt 原生事件过滤。

用途：启动器退到后台、游戏窗口在前台时，按 Ctrl+Alt+<数字> 直接把对应指令
复制到系统剪贴板，切回游戏 Ctrl+V 就能粘贴。

只依赖 ctypes，不引入额外依赖；非 Windows 平台会直接返回不可用。
"""

from __future__ import annotations

import ctypes
import logging
import sys
import time
from ctypes import wintypes
from typing import Callable, Dict, Iterable, Optional

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

logger = logging.getLogger(__name__)

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
ERROR_HOTKEY_ALREADY_REGISTERED = 1409

HOTKEY_ID_BASE = 0xB300
SUPPORTED_SLOTS = tuple(range(0, 10))  # Ctrl+Alt+0 .. Ctrl+Alt+9
PALETTE_ID = HOTKEY_ID_BASE + 100      # Ctrl+Alt+<key>：唤起指令速查小窗
PALETTE_VK = 0x51                      # 默认 'Q'

# 允许把小窗热键改成这些键（Ctrl+Alt + 键）
PALETTE_KEYS: Dict[str, int] = {ch: ord(ch) for ch in "QWERTYUIOPASDFGHJKLZXCVBNM"}
PALETTE_KEYS.update({f"F{i}": 0x6F + i for i in range(1, 13)})  # F1=0x70


def palette_vk(key: str) -> int:
    """把配置里的按键名转成虚拟键码，未知则回退 Q"""
    return PALETTE_KEYS.get(str(key or "").upper(), PALETTE_VK)



def _load_user32():
    if sys.platform != "win32":
        return None
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
    except OSError:  # pragma: no cover - 非 Windows 环境
        return None
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    return user32


class GlobalHotkeys(QAbstractNativeEventFilter):
    """把 Ctrl+Alt+<slot> 绑定到一条指令文本上"""

    def __init__(
        self,
        hwnd_getter: Callable[[], int],
        on_trigger: Callable[[int, str, str], None],
    ) -> None:
        super().__init__()
        self._hwnd_getter = hwnd_getter
        self._on_trigger = on_trigger
        self._user32 = _load_user32()
        self._bound: Dict[int, dict] = {}
        self._last_fire: Dict[int, float] = {}
        self._hwnd: int = 0
        self._installed = False
        self._palette_cb = None
        self._palette_bound = False
        self._palette_vk = PALETTE_VK
        self._palette_key = "Q"

    def set_palette_callback(self, callback) -> None:
        """Ctrl+Alt+<key> 唤起指令速查窗的回调"""
        self._palette_cb = callback

    def set_palette_key(self, key: str) -> str:
        """切换小窗热键（字母或 F1-F12），立即重新注册"""
        name = str(key or "Q").upper()
        self._palette_key = name if name in PALETTE_KEYS else "Q"
        self._palette_vk = palette_vk(self._palette_key)
        if self._palette_bound:
            self.clear()
            try:
                self._hwnd = int(self._hwnd_getter() or 0)
            except Exception:
                self._hwnd = 0
            self._register_palette()
        return self._palette_key

    def enable_palette(self) -> bool:
        """窗口创建后单独注册 Ctrl+Alt+<key>（不依赖工具页是否打开过）"""
        if self._user32 is None:
            return False
        try:
            self._hwnd = int(self._hwnd_getter() or 0)
        except Exception:
            self._hwnd = 0
        return self._register_palette()

    # ------------------------------------------------------------------ 生命周期
    def install(self) -> None:
        if self._installed or self._user32 is None:
            return
        app = QCoreApplication.instance()
        if app is not None:
            app.installNativeEventFilter(self)
            self._installed = True
            logger.info("全局热键事件过滤器已安装")

    def uninstall(self) -> None:
        self.clear()
        if self._installed:
            app = QCoreApplication.instance()
            if app is not None:
                app.removeNativeEventFilter(self)
            self._installed = False

    # ------------------------------------------------------------------ 绑定
    def bind(self, entries: Optional[Iterable[dict]]) -> dict:
        """entries: [{slot, text, title}]

        返回 {ok, bound: [slot], failed: [{slot, error}]}
        """
        result: dict = {"ok": True, "bound": [], "failed": [], "keys": "Ctrl+Alt+0..9"}
        if self._user32 is None:
            result["ok"] = False
            result["error"] = "全局热键只支持 Windows"
            return result

        self.clear()
        try:
            self._hwnd = int(self._hwnd_getter() or 0)
        except Exception:
            self._hwnd = 0
        if not self._hwnd:
            result["ok"] = False
            result["error"] = "窗口句柄不可用，热键未注册"
            return result

        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            try:
                slot = int(entry.get("slot"))
            except (TypeError, ValueError):
                continue
            text = str(entry.get("text") or "")
            title = str(entry.get("title") or "")
            if slot not in SUPPORTED_SLOTS or not text:
                continue
            hotkey_id = HOTKEY_ID_BASE + slot
            vk = 0x30 + slot  # '0' ~ '9'
            ok = bool(
                self._user32.RegisterHotKey(
                    wintypes.HWND(self._hwnd),
                    hotkey_id,
                    MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
                    vk,
                )
            )
            if ok:
                self._bound[hotkey_id] = {"slot": slot, "text": text, "title": title}
                result["bound"].append(slot)
            else:
                code = ctypes.get_last_error()
                reason = (
                    "已被其它程序占用"
                    if code == ERROR_HOTKEY_ALREADY_REGISTERED
                    else f"注册失败（错误码 {code}）"
                )
                result["failed"].append({"slot": slot, "error": reason})

        result["ok"] = bool(result["bound"])
        if not result["ok"] and "error" not in result:
            result["error"] = "所有热键都被占用"

        result["palette"] = self._register_palette()
        if not result["palette"]:
            result["paletteError"] = "Ctrl+Alt+Q 被占用，速查窗热键不可用"

        logger.info(
            "全局热键绑定：成功 %s，失败 %s，速查窗 %s",
            result["bound"],
            [f.get("slot") for f in result["failed"]],
            f"Ctrl+Alt+{self._palette_key}" if result["palette"] else "未注册",
        )
        return result

    def _register_palette(self) -> bool:
        """Ctrl+Alt+Q：唤起指令速查小窗"""
        if self._user32 is None or not self._hwnd or self._palette_cb is None:
            return False
        ok = bool(
            self._user32.RegisterHotKey(
                wintypes.HWND(self._hwnd),
                PALETTE_ID,
                MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
                self._palette_vk,
            )
        )
        self._palette_bound = ok
        if not ok:
            logger.warning("Ctrl+Alt+Q 注册失败（错误码 %s）", ctypes.get_last_error())
        return ok

    def clear(self) -> None:
        if self._user32 is None:
            return
        if self._palette_bound:
            try:
                self._user32.UnregisterHotKey(wintypes.HWND(self._hwnd), PALETTE_ID)
            except Exception:  # pragma: no cover
                logger.debug("注销速查窗热键失败", exc_info=True)
            self._palette_bound = False
        if not self._bound:
            return
        for hotkey_id in list(self._bound):
            try:
                self._user32.UnregisterHotKey(wintypes.HWND(self._hwnd), hotkey_id)
            except Exception:  # pragma: no cover - 注销失败不影响退出
                logger.debug("注销热键 %s 失败", hotkey_id, exc_info=True)
        self._bound.clear()

    # ------------------------------------------------------------------ 事件
    def nativeEventFilter(self, event_type, message):  # noqa: N802 - Qt 约定
        try:
            name = bytes(event_type) if not isinstance(event_type, bytes) else event_type
        except Exception:
            name = b""
        if name == b"windows_generic_MSG" and (self._bound or self._palette_bound):
            try:
                msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
                if msg.message == WM_HOTKEY:
                    self._fire(int(msg.wParam))
            except Exception:  # pragma: no cover
                logger.debug("解析 WM_HOTKEY 失败", exc_info=True)
        return False  # 不拦截，继续交给 Qt 处理

    def _fire(self, hotkey_id: int) -> None:
        if hotkey_id == PALETTE_ID:
            if self._palette_bound and self._palette_cb is not None:
                now = time.monotonic()
                if now - self._last_fire.get(hotkey_id, 0.0) < 0.25:
                    return
                self._last_fire[hotkey_id] = now
                try:
                    self._palette_cb()
                except Exception:
                    logger.exception("唤起指令速查窗失败")
            return

        entry = self._bound.get(hotkey_id)
        if not entry:
            return
        # 同一条热键 250ms 内的重复消息（Qt 会同时投递两种原生事件）只处理一次
        now = time.monotonic()
        if now - self._last_fire.get(hotkey_id, 0.0) < 0.25:
            return
        self._last_fire[hotkey_id] = now
        try:
            self._on_trigger(entry["slot"], entry["text"], entry["title"])
        except Exception:
            logger.exception("热键回调失败")


__all__ = ["GlobalHotkeys", "SUPPORTED_SLOTS"]
