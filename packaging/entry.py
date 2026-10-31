"""PyInstaller 入口：把包导入路径固定到仓库根目录"""

from __future__ import annotations

import multiprocessing
import sys

from vein_launcher.presentation.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
