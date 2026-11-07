"""打一个精简发布包（zip），并报告体积构成。

用法：
    python tools/package_release.py                    # 只打代码 + 前端资源
    python tools/package_release.py --jre              # 附带最小 JRE（java/jre-17）
    python tools/package_release.py --jre --python-embed <dir>   # 额外附带嵌入式 Python

产物：dist_release/VeinLauncher-<version>.zip
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "dist_release"

INCLUDE_DIRS = [
    ("vein_launcher", {"__pycache__", ".mypy_cache"}),
    ("assets", set()),
]
INCLUDE_FILES = ["LICENSE", "README.md", "README-zh.md", "requirements.txt"]


def version() -> str:
    sys.path.insert(0, str(ROOT))
    from vein_launcher import __version__

    return __version__


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def copy_tree(src: Path, dst: Path, skip_names: set[str]) -> None:
    for item in src.rglob("*"):
        if any(part in skip_names for part in item.parts):
            continue
        if item.suffix in {".pyc", ".pyo"}:
            continue
        target = dst / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jre", action="store_true", help="附带 VeinLauncher/java/jre-17")
    parser.add_argument("--python-embed", default="", help="附带嵌入式 Python 目录")
    parser.add_argument("--keep-dir", action="store_true", help="保留解压后的目录")
    args = parser.parse_args()

    ver = version()
    stage = OUT_ROOT / f"VeinLauncher-{ver}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    for name, skip in INCLUDE_DIRS:
        src = ROOT / name
        if src.is_dir():
            copy_tree(src, stage / name, skip)

    for name in INCLUDE_FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, stage / name)

    if args.jre:
        jre = ROOT / "VeinLauncher" / "java" / "jre-17"
        if jre.is_dir():
            shutil.copytree(jre, stage / "java" / "jre-17")
            print(f"+ JRE {dir_size(jre) / 1024 / 1024:.1f} MB")
        else:
            print("! 没有找到 jre-17，先运行 tools/make_minimal_jre.py")

    if args.python_embed:
        embed = Path(args.python_embed)
        if embed.is_dir():
            shutil.copytree(embed, stage / "python")
            print(f"+ Python embed {dir_size(embed) / 1024 / 1024:.1f} MB")

    raw = dir_size(stage)
    zip_path = OUT_ROOT / f"VeinLauncher-{ver}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in stage.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(stage))

    packed = zip_path.stat().st_size
    print()
    print(f"staging : {raw / 1024 / 1024:.1f} MB")
    print(f"zip     : {packed / 1024 / 1024:.1f} MB  ({zip_path.name})")
    print(f"ratio   : {packed / raw * 100:.1f}%")
    if not args.keep_dir:
        shutil.rmtree(stage)
        print("(解压目录已清理，加 --keep-dir 可保留)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
