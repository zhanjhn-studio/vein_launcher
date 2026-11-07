"""输入桥自检：用一个 Tk 窗口当靶子，验证 SendInput 能真的把字符送进前台窗口。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(r"Z:\Vein Launche")
sys.path.insert(0, str(ROOT))

from vein_launcher.infrastructure.process import game_input  # noqa: E402

CHILD = r'''
import tkinter as tk
from pathlib import Path

out = Path(r"__OUT__")
root = tk.Tk()
root.title("VL Input Target")
root.geometry("420x160")
text = tk.Text(root, height=6)
text.pack(fill="both", expand=True)
text.focus_set()

def dump(_event=None):
    out.write_text(text.get("1.0", "end"), encoding="utf-8")

text.bind("<KeyRelease>", dump)
root.after(25000, root.destroy)
root.mainloop()
'''


def main() -> int:
    out = Path(tempfile.gettempdir()) / "vl_input_target.txt"
    out.unlink(missing_ok=True)
    script = Path(tempfile.gettempdir()) / "vl_input_target.py"
    script.write_text(CHILD.replace("__OUT__", str(out).replace("\\", "\\\\")), encoding="utf-8")

    child = subprocess.Popen([sys.executable, str(script)])
    try:
        time.sleep(2.0)
        windows = game_input.list_windows("VL Input Target")
        if not windows:
            print("FAIL: 没找到测试窗口")
            return 1
        print("found window:", windows[0])

        focused = game_input.focus_window(int(windows[0]["hwnd"]))
        print("focused:", focused)
        time.sleep(0.3)
        game_input.type_text("hello vein 123")
        time.sleep(1.0)

        content = out.read_text(encoding="utf-8") if out.exists() else ""
        print("typed into target:", repr(content))
        ok = "hello vein 123" in content
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()


if __name__ == "__main__":
    raise SystemExit(main())
