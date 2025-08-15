"""
Wallpaper Engine 工坊管理工具 - 主入口
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
from loguru import logger

from engingv.core.cli import main

if __name__ == "__main__":
    main()
