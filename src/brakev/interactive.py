"""
brakev - 交互式用户界面模块

提供菜单驱动的交互式界面，统一访问所有功能
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# 导入Rich库用于美化输出
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table

# 导入版本信息
from brakev import __version__

console = Console()

def display_header():
    """显示程序标题"""
    console.print(Panel.fit(
        "brakev 视频处理工具集",
        subtitle=f"版本 {__version__}",
        border_style="green"
    ))
    console.print()

def display_menu():
    """显示主菜单"""
    table = Table(title="功能选择", show_header=False, box=None)
    table.add_column("选项", style="cyan")
    table.add_column("描述")
    
    table.add_row("1", "视频分析 (使用 bitv 功能)")
    table.add_row("2", "视频格式处理 (使用 formatv 功能)")
    table.add_row("3", "功能3 (待添加)")
    table.add_row("q", "退出程序")
    
    console.print(table)
    console.print()

def run_interactive() -> int:
    """运行交互式界面
    
    Returns:
        int: 程序返回码，0表示正常退出
    """
    try:
        while True:
            display_header()
            display_menu()
            
            choice = Prompt.ask("请选择功能", choices=["1", "2", "3", "q"], default="q")
            
            if choice == "q":
                console.print("[green]感谢使用 brakev，再见！[/green]")
                return 0
                
            elif choice == "1":
                # 调用 bitv 包的功能
                try:
                    from bitv.__main__ import interactive_main
                    interactive_main()
                except ImportError:
                    console.print("[red]错误: 无法加载 bitv 模块[/red]")
                
            elif choice == "2":
                # 调用 formatv 包的功能
                try:
                    from formatv.__main__ import interactive_main
                    interactive_main()
                except ImportError:
                    console.print("[red]错误: 无法加载 formatv 模块[/red]")
                
            elif choice == "3":
                console.print("[yellow]此功能尚未实现[/yellow]")
            
            # 每次操作后等待用户确认
            console.print()
            if not Confirm.ask("是否继续使用其他功能?"):
                console.print("[green]感谢使用 brakev，再见！[/green]")
                return 0
                
    except KeyboardInterrupt:
        console.print("\n[yellow]操作被用户中断[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]程序出错: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(run_interactive())