"""原版（vanilla）游戏输入桥：不装任何 mod，通过 Windows SendInput 直接操作游戏窗口。

能做什么：
    - 找到正在运行的 Minecraft 窗口并切到前台
    - 打开聊天框、输入任意指令、回车执行（等价于玩家手打）
    - 读取最新日志（latest.log）与存档 NBT（已有 MlcService 负责）

不能做什么：
    - 不能像 mod 那样读取实时背包/实体数据（原版没有对外接口）
    - 需要游戏窗口能获得前台焦点（全屏失焦时 Windows 会拦截输入）
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_T = 0x54
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


def _send_inputs(events: List[INPUT]) -> None:
    if not events:
        return
    array = (INPUT * len(events))(*events)
    sent = user32.SendInput(len(events), array, ctypes.sizeof(INPUT))
    if sent != len(events):
        logger.warning("SendInput 只发送了 %s/%s 个事件", sent, len(events))


def _key_event(vk: int = 0, scan: int = 0, flags: int = 0) -> INPUT:
    event = INPUT()
    event.type = INPUT_KEYBOARD
    event.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return event


def press_key(vk: int) -> None:
    _send_inputs([_key_event(vk), _key_event(vk, 0, KEYEVENTF_KEYUP)])
    time.sleep(0.02)


def type_text(text: str) -> None:
    """按 Unicode 逐字输入（中文、符号、斜杠都能过）"""
    events: List[INPUT] = []
    for char in text:
        code = ord(char)
        events.append(_key_event(0, code, KEYEVENTF_UNICODE))
        events.append(_key_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
    _send_inputs(events)


def list_windows(keyword: str = "Minecraft") -> List[dict]:
    """枚举可见窗口，返回 {hwnd, title, pid}"""
    result: List[dict] = []
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        if keyword.lower() in title.lower():
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            result.append({"hwnd": int(hwnd), "title": title, "pid": int(pid.value)})
        return True

    user32.EnumWindows(enum_proc(callback), 0)
    return result


def focus_window(hwnd: int) -> bool:
    """切到前台：后台进程直接 SetForegroundWindow 会被 Windows 拒绝，这里两种办法都上"""
    if not user32.IsWindow(hwnd):
        return False
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE

    # 1) ATTACH_THREAD_INPUT：把自己挂到当前前台线程上，绕过前台锁
    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
    current_thread = kernel32.GetCurrentThreadId()
    attached = False
    if foreground_thread and foreground_thread != current_thread:
        attached = bool(user32.AttachThreadInput(current_thread, foreground_thread, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(current_thread, foreground_thread, False)

    time.sleep(0.12)
    if user32.GetForegroundWindow() == hwnd:
        return True

    # 2) 模拟一次 ALT 按键：Windows 允许“刚按下 Alt 的进程”抢前台
    vk_menu = 0x12
    user32.keybd_event(vk_menu, 0, 0, 0)
    user32.keybd_event(vk_menu, 0, KEYEVENTF_KEYUP, 0)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)
    return user32.GetForegroundWindow() == hwnd


def send_chat_command(command: str, hwnd: Optional[int] = None) -> dict:
    """在原版游戏里执行一条指令：T 打开聊天 → 输入 → 回车"""
    command = command.strip()
    if not command:
        raise ValueError("空指令")
    if not command.startswith("/"):
        command = "/" + command

    if hwnd is None:
        windows = list_windows("Minecraft")
        if not windows:
            raise RuntimeError("没有找到 Minecraft 窗口")
        hwnd = windows[0]["hwnd"]

    if not focus_window(int(hwnd)):
        logger.warning("游戏窗口没能切到前台，输入可能不会生效（hwnd=%s）", hwnd)

    press_key(VK_T)
    time.sleep(0.12)
    type_text(command)
    time.sleep(0.05)
    press_key(VK_RETURN)
    return {"sent": True, "command": command, "hwnd": int(hwnd)}


__all__ = ["send_chat_command", "focus_window", "list_windows", "type_text", "press_key"]
