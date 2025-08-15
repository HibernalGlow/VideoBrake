"""
AudioV - 视频音频提取工具主入口
"""

import sys
from pathlib import Path

# 将 src 目录添加到 Python 路径
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from audiov.interactive import main

if __name__ == "__main__":
    main()
