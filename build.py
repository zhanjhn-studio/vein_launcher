"""Vein Launcher 打包脚本（PyInstaller）

用法：
    python build.py                 # 清理并打包
    python build.py --no-clean      # 保留 build/ 加快二次打包
    python build.py --onedir        # 目录模式（默认，启动更快）
    python build.py --onefile       # 单文件模式（分发方便，首次启动慢）

产物：
    dist/VeinLauncher/VeinLauncher.exe
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
APP_NAME = "VeinLauncher"

# 需要随包分发的非 Python 资源（源目录;包内相对路径）
DATA_FILES = [
    ("vein_launcher/presentation/ui/theme", "vein_launcher/presentation/ui/theme"),
    ("vein_launcher/common/i18n/locales", "vein_launcher/common/i18n/locales"),
    (
        "vein_launcher/infrastructure/plugin_host/runtime",
        "vein_launcher/infrastructure/plugin_host/runtime",
    ),
    ("plugins_examples", "plugins_examples"),
]


def build(clean: bool, onefile: bool) -> int:
    if clean:
        for directory in (ROOT / "build", ROOT / "dist"):
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean" if clean else "--noconfirm",
        "--windowed",
        "--name",
        APP_NAME,
        "--collect-submodules",
        "vein_launcher",
        "--hidden-import",
        "pydantic",
    ]

    if onefile:
        command.append("--onefile")

    for source, target in DATA_FILES:
        command += ["--add-data", f"{ROOT / source}{';' if sys.platform == 'win32' else ':'}{target}"]

    command.append(str(ROOT / "run_launcher.py"))

    print("执行:", " ".join(command))
    return subprocess.call(command, cwd=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="打包 Vein Launcher")
    parser.add_argument("--no-clean", action="store_true", help="不清理 build/dist")
    parser.add_argument("--onefile", action="store_true", help="单文件模式")
    parser.add_argument("--onedir", action="store_true", help="目录模式（默认）")
    args = parser.parse_args()

    if args.onefile and args.onedir:
        parser.error("--onefile 与 --onedir 不能同时使用")

    return build(clean=not args.no_clean, onefile=args.onefile)


if __name__ == "__main__":
    raise SystemExit(main())
