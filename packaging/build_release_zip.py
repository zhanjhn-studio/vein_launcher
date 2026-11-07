"""把 PyInstaller 产物裁剪并打成发布 zip（供安装器嵌入/下载）。"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(r"Z:\Vein Launche")
SRC = ROOT / "dist_exe" / "VeinLauncher"
OUT_DIR = ROOT / "packaging" / "release"
STAGE = OUT_DIR / "VeinLauncher"
ZIP = OUT_DIR / "VeinLauncher-win64.zip"

# 运行不需要、但占体积的目录/文件
DROP_DIRS = {"translations", "qml", "include", "typesystems", "metatypes", "scripts"}
DROP_FILES = {"opengl32sw.dll"}
DROP_SUFFIXES = {".debug.pak", ".debug.bin"}


def size_of(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def main() -> int:
    if not SRC.is_dir():
        print("先运行 PyInstaller 生成 dist_exe/VeinLauncher")
        return 1

    if STAGE.exists():
        shutil.rmtree(STAGE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC, STAGE)

    removed = 0
    for path in sorted(STAGE.rglob("*"), reverse=True):
        if path.is_dir() and path.name in DROP_DIRS:
            removed += size_of(path)
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and (path.name in DROP_FILES or path.suffix in DROP_SUFFIXES):
            removed += path.stat().st_size
            path.unlink(missing_ok=True)
        elif path.is_file() and path.name.endswith(".debug.pak"):
            removed += path.stat().st_size
            path.unlink(missing_ok=True)

    trimmed = size_of(STAGE)
    print(f"trimmed: {trimmed / 1024 / 1024:.0f} MB (removed {removed / 1024 / 1024:.0f} MB)")

    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for item in STAGE.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(STAGE))
    print(f"zip: {ZIP.stat().st_size / 1024 / 1024:.0f} MB -> {ZIP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
