"""PyInstaller 打包入口（保持独立文件，避免包内相对导入问题）"""

import multiprocessing
import sys

from vein_launcher.presentation.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
