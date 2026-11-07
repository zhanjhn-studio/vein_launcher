"""PyInstaller 入口：打包成 VeinLauncher.exe。"""

from __future__ import annotations

import multiprocessing
import sys

from vein_launcher.presentation.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
