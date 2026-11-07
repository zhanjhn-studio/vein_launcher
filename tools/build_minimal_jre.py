"""用 jlink 生成只含 Minecraft 所需模块的最小 JRE。

用法：
    python tools/make_minimal_jre.py            # 生成 VeinLauncher/java/jre-17
    python tools/make_minimal_jre.py --modules java.base,java.desktop

体积对比：完整 JDK ≈ 300 MB，jlink 最小 JRE ≈ 50 MB。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA_ROOT = ROOT / "VeinLauncher" / "java"

# Minecraft 1.20.1 客户端实际用到的模块：图形、日志、JMX、URL 处理、
# authlib 的 java.net.http、TLS、以及 LWJGL 依赖的 jdk.unsupported
DEFAULT_MODULES = ",".join(
    [
        "java.base",
        "java.desktop",
        "java.logging",
        "java.management",
        "java.naming",
        "java.net.http",
        "java.security.jgss",
        "java.xml",
        "jdk.unsupported",
        "jdk.crypto.ec",
        "jdk.zipfs",
        "jdk.charsets",
    ]
)


def find_jlink() -> Path:
    for candidate in sorted(JAVA_ROOT.glob("*/jdk-*/bin/jlink.exe")) + sorted(JAVA_ROOT.glob("*/bin/jlink.exe")):
        if candidate.is_file():
            return candidate
    raise SystemExit("找不到 jlink，请先安装 JDK 17")


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modules", default=DEFAULT_MODULES)
    parser.add_argument("--output", default=str(JAVA_ROOT / "jre-17"))
    parser.add_argument("--compress", default="2", help="0/1/2（2 最小）")
    args = parser.parse_args()

    jlink = find_jlink()
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)

    command = [
        str(jlink),
        "--add-modules",
        args.modules,
        "--strip-debug",
        "--no-header-files",
        "--no-man-pages",
        f"--compress={args.compress}",
        "--output",
        str(output),
    ]
    print("running:", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return 1

    java = output / "bin" / "java.exe"
    version = subprocess.run([str(java), "-version"], capture_output=True, text=True)
    print((version.stderr or version.stdout).strip().splitlines()[0] if version.stderr or version.stdout else "?")
    print(f"minimal JRE: {dir_size(output) / 1024 / 1024:.1f} MB -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
