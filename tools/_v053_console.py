"""隐藏所有控制台子进程窗口 + 下载任务删除。"""

from pathlib import Path

root = Path(r"Z:\Vein Launche")

# ---------------------------------------------------------------- 1. 公共 helper
console = root / "vein_launcher" / "common" / "utils" / "console.py"
console.write_text('''"""Windows 下隐藏子进程控制台窗口（避免 cmd 闪窗）。"""

from __future__ import annotations

import subprocess
import sys

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def hidden_kwargs() -> dict:
    """asyncio.create_subprocess_exec 用：隐藏控制台窗口。"""
    if sys.platform != "win32":
        return {}
    kwargs = {"creationflags": CREATE_NO_WINDOW}
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs


def hidden_popen_kwargs() -> dict:
    """subprocess.Popen 用：隐藏控制台窗口。"""
    return hidden_kwargs()
''', encoding="utf-8")
print("console helper")

# ---------------------------------------------------------------- 2. 各 spawn 点
def patch(path: Path, replacements):
    t = path.read_text(encoding="utf-8")
    changed = 0
    for old, new in replacements:
        if old in t:
            t = t.replace(old, new, 1)
            changed += 1
    path.write_text(t, encoding="utf-8")
    print(path.name, "patched:", changed)


patch(root / "vein_launcher" / "infrastructure" / "plugin_host" / "host.py", [
    ("from vein_launcher.common.events.event_bus import event_bus",
     "from vein_launcher.common.events.event_bus import event_bus\nfrom vein_launcher.common.utils.console import hidden_kwargs"),
    ("""            stderr=asyncio.subprocess.PIPE,
            limit=MAX_LINE,
        )""",
     """            stderr=asyncio.subprocess.PIPE,
            limit=MAX_LINE,
            **hidden_kwargs(),
        )"""),
])

patch(root / "vein_launcher" / "application" / "services" / "plugin_service.py", [
    ("                version = subprocess.run(\n                    [path, \"-v\"], capture_output=True, text=True, timeout=5\n                ).stdout.strip()",
     "                from vein_launcher.common.utils.console import hidden_kwargs\n\n                version = subprocess.run(\n                    [path, \"-v\"], capture_output=True, text=True, timeout=5, **hidden_kwargs()\n                ).stdout.strip()"),
])

patch(root / "vein_launcher" / "infrastructure" / "process" / "game_process.py", [
    ("                stderr=asyncio.subprocess.STDOUT,\n            )",
     "                stderr=asyncio.subprocess.STDOUT,\n                **hidden_kwargs(),\n            )"),
])

patch(root / "vein_launcher" / "infrastructure" / "process" / "java_detector.py", [
    ("                stderr=asyncio.subprocess.STDOUT,\n            )",
     "                stderr=asyncio.subprocess.STDOUT,\n                **hidden_kwargs(),\n            )"),
])

patch(root / "vein_launcher" / "application" / "services" / "loader_service.py", [
    ("            stderr=asyncio.subprocess.STDOUT,\n        )",
     "            stderr=asyncio.subprocess.STDOUT,\n            **hidden_kwargs(),\n        )"),
])

patch(root / "vein_launcher" / "presentation" / "bridge.py", [
    ("import asyncio as _asyncio",
     "import asyncio as _asyncio\n\nfrom vein_launcher.common.utils.console import hidden_kwargs, hidden_popen_kwargs"),
    ('        subprocess.Popen(["explorer", path])',
     '        subprocess.Popen(["explorer", path], **hidden_popen_kwargs())'),
    ('        subprocess.Popen(["explorer", str(path)])',
     '        subprocess.Popen(["explorer", str(path)], **hidden_popen_kwargs())'),
    ("""            stderr=_asyncio.subprocess.PIPE,
        )""",
     """            stderr=_asyncio.subprocess.PIPE,
            **hidden_kwargs(),
        )"""),
])

patch(root / "vein_launcher" / "application" / "services" / "update_service.py", [
    ('                subprocess.Popen([str(target)], close_fds=True)',
     '                from vein_launcher.common.utils.console import hidden_popen_kwargs\n\n                subprocess.Popen([str(target)], close_fds=True, **hidden_popen_kwargs())'),
])

# python 脚本类 spawn（皮肤支持）
br = root / "vein_launcher" / "presentation" / "bridge.py"
t = br.read_text(encoding="utf-8")
if "sys.executable" in t and "hidden_popen_kwargs()" in t:
    pass

# ---------------------------------------------------------------- 3. 下载任务删除
if "downloads.remove" not in t:
    t = t.replace('            "downloads.list": self._downloads_list,',
                  '            "downloads.list": self._downloads_list,\n            "downloads.remove": self._downloads_remove,')
    t = t.replace("""    async def _downloads_list(self) -> list:""",
"""    async def _downloads_remove(self, task_id: str) -> dict:
        removed = self._downloads.pop(str(task_id), None)
        return {"removed": bool(removed), "id": str(task_id)}

    async def _downloads_list(self) -> list:""", 1)
    br.write_text(t, encoding="utf-8")
    print("downloads.remove RPC")
