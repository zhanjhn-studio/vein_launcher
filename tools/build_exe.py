"""打包 Vein Launcher 为 Windows onedir 发布包。

用法：
    python tools/build_exe.py [--version 0.5.0] [--skip-zip]

产物：
    dist_exe/VeinLauncher/VeinLauncher.exe        （可直接运行）
    dist_exe/VeinLauncher-<版本>-win64.zip        （发布资产）
    dist_exe/latest.json                          （更新兜底清单）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist_exe"
APP_DIR = DIST / "VeinLauncher"
WORK = ROOT / "build" / "pyinstaller"
SPEC = ROOT / "build"
ENTRY = ROOT / "packaging" / "entry.py"
WEBUI_DIST = ROOT / "vein_launcher" / "presentation" / "webui" / "dist"

# 运行需要的额外数据（PyInstaller --add-data）
DATA_DIRS = [
    (WEBUI_DIST, "webui/dist"),
    (ROOT / "assets", "assets"),
    (ROOT / "vein_launcher" / "infrastructure" / "plugin_host" / "runtime",
     "vein_launcher/infrastructure/plugin_host/runtime"),
    (ROOT / "vein_launcher" / "common" / "i18n" / "locales",
     "vein_launcher/common/i18n/locales"),
    (ROOT / "plugins_examples", "plugins_examples"),
    (ROOT / "VeinLauncher" / "agent", "agent"),
]

DROP_DIRS = {"translations", "qml", "include", "typesystems", "metatypes", "scripts"}
DROP_FILES = {"opengl32sw.dll"}
DROP_SUFFIXES = {".debug.pak", ".debug.bin"}


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.5.0")
    parser.add_argument("--skip-zip", action="store_true")
    args = parser.parse_args()
    version = args.version.lstrip("v")

    if not (WEBUI_DIST / "app.js").is_file():
        print("缺少 webui/dist/app.js：先运行 build.ps1 构建前端")
        return 1

    started = time.time()
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed",
        "--name", "VeinLauncher",
        "--icon", str(ROOT / "assets" / "logo.ico"),
        "--distpath", str(DIST),
        "--workpath", str(WORK),
        "--specpath", str(SPEC),
    ]
    for source, target in DATA_DIRS:
        if source.is_dir():
            cmd += ["--add-data", f"{source};{target}"]
    # 体积优化：排除用不到的大模块
    for module in ("tkinter", "unittest", "pytest", "IPython", "matplotlib", "numpy", "pandas"):
        cmd += ["--exclude-module", module]
    cmd.append(str(ENTRY))
    run(cmd)

    if not (APP_DIR / "VeinLauncher.exe").is_file():
        print("PyInstaller 产物缺失")
        return 1

    # 裁剪运行不需要的 Qt 组件
    removed = 0
    for path in sorted(APP_DIR.rglob("*"), reverse=True):
        if path.is_dir() and path.name in DROP_DIRS:
            removed += dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and (path.name in DROP_FILES or path.suffix in DROP_SUFFIXES):
            removed += path.stat().st_size
            path.unlink(missing_ok=True)

    print(f"app size: {dir_size(APP_DIR) / 1024 / 1024:.0f} MB (trimmed {removed / 1024 / 1024:.0f} MB)")

    zip_path = DIST / f"VeinLauncher-{version}-win64.zip"
    if args.skip_zip:
        print("skip zip")
        return 0

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for item in APP_DIR.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(APP_DIR))
    size_mb = zip_path.stat().st_size / 1024 / 1024
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"zip: {zip_path.name} {size_mb:.0f} MB sha256={digest[:16]}...")

    manifest = {
        "version": version,
        "name": f"Vein Launcher {version}",
        "asset": zip_path.name,
        "url": f"https://github.com/zhanjhn-studio/vein_launcher/releases/download/v{version}/{zip_path.name}",
        "html_url": f"https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v{version}",
        "sha256": digest,
        "size": zip_path.stat().st_size,
    }
    (DIST / "latest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"latest.json written; total {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
