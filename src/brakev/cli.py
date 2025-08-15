"""
brakev - 命令行界面模块

提供基于 Typer 的命令行界面，用于访问所有 brakev 功能。
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console

# 导入版本信息
from brakev import __version__

# 创建 Typer 应用
app = typer.Typer(
    name="brakev",
    help="brakev - 视频处理工具集",
    no_args_is_help=True,
    add_completion=False,
    invoke_without_command=True
)

# 子命令组
analyze_app = typer.Typer(help="视频分析功能")
format_app = typer.Typer(help="视频格式处理功能")

# 添加子命令组到主应用
app.add_typer(analyze_app, name="analyze", help="视频分析功能")
app.add_typer(format_app, name="format", help="视频格式处理功能")

# 创建控制台对象
console = Console()

def version_callback(value: bool):
    """版本信息回调函数"""
    if value:
        console.print(f"brakev 版本: {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="显示版本信息", callback=version_callback),
):
    """brakev 主命令"""
    pass

# ============== 视频分析子命令 ==============

@analyze_app.callback(invoke_without_command=True)
def analyze_main(ctx: typer.Context):
    """视频分析子命令 (调用 bitv 包的功能)"""
    if ctx.invoked_subcommand is None:
        # 导入并调用子包的功能
        from bitv.__main__ import main as analyze_main
        analyze_main()

@analyze_app.command("file")
def analyze_file(
    file_path: str = typer.Argument(..., help="视频文件路径"),
):
    """分析单个视频文件"""
    # 导入并调用子包的功能
    from bitv.__main__ import analyze_file as analyze_single_file
    analyze_single_file(file_path)

@analyze_app.command("dir")
def analyze_dir(
    dir_path: str = typer.Argument(..., help="视频文件夹路径"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="是否递归处理子文件夹"),
):
    """分析文件夹中的所有视频"""
    # 导入并调用子包的功能
    from bitv.__main__ import analyze_dir as analyze_directory
    analyze_directory(dir_path, recursive)

# ============== 视频格式处理子命令 ==============

@format_app.callback(invoke_without_command=True)
def format_main(ctx: typer.Context):
    """视频格式处理子命令 (调用 formatv 包的功能)"""
    if ctx.invoked_subcommand is None:
        # 导入并调用子包的功能
        from formatv.__main__ import main as format_main
        format_main()

@format_app.command("add-nov")
def add_nov_cmd(
    path: str = typer.Argument(..., help="视频文件或文件夹路径"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="是否递归处理子文件夹"),
):
    """添加.nov扩展名到视频文件"""
    # 导入并调用子包的功能
    from formatv.__main__ import add_nov_extension
    add_nov_extension(path, recursive)

@format_app.command("remove-nov")
def remove_nov_cmd(
    path: str = typer.Argument(..., help="视频文件或文件夹路径"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="是否递归处理子文件夹"),
):
    """移除视频文件的.nov扩展名"""
    # 导入并调用子包的功能
    from formatv.__main__ import remove_nov_extension
    remove_nov_extension(path, recursive)

if __name__ == "__main__":
    app()
