"""
brakev - 视频处理工具集

命令行入口模块 - 负责中转命令到不同的功能实现
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# 导入 Typer CLI
from brakev.cli import app
from brakev.interactive import run_interactive


def main():
    """命令行主入口点 - 负责中转
    
    如果没有命令行参数，启动交互式界面
    否则将控制权交给 Typer CLI
    """
    try:
        # 检查是否有特殊的运行模式参数
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        # 判断是否显式请求交互模式
        if len(args) == 1 and args[0] in ['interactive', '-i', '--interactive']:
            return run_interactive()
        
        # 判断是否没有参数或只有帮助参数
        if len(args) == 0 or args[0] in ['--help', '-h']:
            # 如果没有参数或只有帮助参数，运行交互式界面
            return run_interactive()
        
        # 其他情况，使用 Typer CLI 处理
        app()
        return 0
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"程序出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())