"""
VideoBrake - 命令行界面模块

提供基于 Typer 的命令行界面，用于访问所有 VideoBrake 功能。
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel

from videobrake import VideoBrake
from formatfliter.__main__ import find_video_files

# 创建 Typer 应用
app = typer.Typer(
    name="videobrake",
    help="VideoBrake - 视频处理工具集",
    no_args_is_help=True,
    add_completion=False,
)

# 子命令组
analyze_app = typer.Typer(help="视频分析功能")
classify_app = typer.Typer(help="视频分类功能")
format_app = typer.Typer(help="视频格式处理功能")

# 添加子命令组到主应用
app.add_typer(analyze_app, name="analyze", help="视频分析功能")
app.add_typer(classify_app, name="classify", help="视频分类功能")
app.add_typer(format_app, name="format", help="视频格式处理功能")

# 创建控制台对象
console = Console()


def version_callback(value: bool):
    """版本信息回调函数"""
    if value:
        console.print(f"VideoBrake 版本: ")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(False, "--version", "-v", help="显示版本信息", callback=version_callback),
):
    """
    VideoBrake - 视频处理工具集

    提供视频分析、分类和格式转换功能
    """
    pass


@app.command("demo")
def demo():
    """运行功能演示"""
    console.print("[bold cyan]VideoBrake 功能演示[/bold cyan]")
    
    # 创建统一接口实例
    vb = VideoBrake()
    
    # 显示两个主要子包
    console.print("\n[green]1. 可用的子包:[/green]")
    console.print("   • bitscaculate: 视频码率分析与分类模块")
    console.print("   • formatfliter: 视频格式过滤器模块")
    
    # 显示功能概述
    console.print("\n[green]2. 主要功能:[/green]")
    console.print("   • 视频分析: 分析视频文件的码率、大小、时长等信息")
    console.print("   • 视频分类: 根据码率将视频文件分类到不同文件夹")
    console.print("   • 格式处理: 添加/移除.nov后缀，处理重复视频")


# 视频分析命令
@analyze_app.command("file")
def analyze_file(
    file_path: Path = typer.Argument(..., help="视频文件路径", exists=True)
):
    """分析单个视频文件"""
    vb = VideoBrake()
    
    console.print(f"[blue]正在分析视频: {file_path}[/blue]")
    video_info = vb.analyze_video(str(file_path))
    
    if video_info:
        console.print(f"[green]文件名:[/green] {video_info.filename}")
        console.print(f"[green]码率:[/green] {video_info.bitrate_mbps:.2f} Mbps")
        console.print(f"[green]时长:[/green] {video_info.duration:.2f} 秒 ({video_info.duration / 60:.2f} 分钟)")
        console.print(f"[green]分辨率:[/green] {video_info.width}x{video_info.height}")
        console.print(f"[green]帧率:[/green] {video_info.fps:.2f} fps")
        console.print(f"[green]文件大小:[/green] {video_info.size_mb:.2f} MB")
    else:
        console.print(f"[red]无法分析视频文件: {file_path}[/red]")


@analyze_app.command("folder")
def analyze_folder(
    folder_path: Path = typer.Argument(..., help="视频文件夹路径", exists=True),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-nr", help="是否递归搜索子文件夹"),
    step_mb: float = typer.Option(1.0, "--step", "-s", help="每档码率大小(Mbps)"),
    max_levels: int = typer.Option(10, "--max-levels", "-m", help="最大档位数量"),
    generate_report: bool = typer.Option(True, "--report/--no-report", help="是否生成JSON报告"),
    classify: bool = typer.Option(False, "--classify", "-c", help="是否根据分析结果对视频进行分类"),
    move: bool = typer.Option(False, "--move", help="是否移动文件（否则复制）")
):
    """分析视频文件夹"""
    try:
        # 创建带有自定义参数的实例
        vb = VideoBrake(bitrate_step=step_mb, max_steps=max_levels)
        console.print(f"[cyan]开始分析文件夹: {folder_path}[/cyan]")
        
        # 分析文件夹
        result = vb.analyze_folder(str(folder_path), recursive=recursive)
        
        # 生成JSON报告
        if generate_report:
            report_path = vb.generate_json_report(result)
            console.print(f"[green]分析报告已保存: {report_path}[/green]")
            
            # 根据分析结果进行分类
            if classify:
                vb.classify_from_report(report_path, is_move=move)
                action = "移动" if move else "复制"
                console.print(f"[green]已完成文件{action}分类[/green]")
    except Exception as e:
        console.print(f"[red]分析过程中出错: {str(e)}[/red]")


# 视频分类命令
@classify_app.command("by-bitrate")
def classify_by_bitrate(
    source_dir: Path = typer.Argument(..., help="源文件夹路径", exists=True),
    target_dir: Optional[Path] = typer.Option(None, "--target", "-t", help="目标文件夹路径"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-nr", help="是否递归搜索子文件夹"),
    move: bool = typer.Option(False, "--move", help="是否移动文件（否则复制）"),
    step_mb: float = typer.Option(1.0, "--step", "-s", help="每档码率大小(Mbps)"),
    max_levels: int = typer.Option(10, "--max-levels", "-m", help="最大档位数量")
):
    """按码率分类视频文件"""
    # 如果未指定目标目录，使用源目录
    if target_dir is None:
        target_dir = source_dir
    
    # 创建带有自定义参数的实例
    vb = VideoBrake(bitrate_step=step_mb, max_steps=max_levels)
    
    # 执行分类
    vb.classify_videos(
        source_dir=str(source_dir),
        target_dir=str(target_dir),
        is_move=move,
        recursive=recursive
    )
    
    action = "移动" if move else "复制"
    console.print(f"[green]已完成文件{action}分类[/green]")


@classify_app.command("from-report")
def classify_from_report(
    report_path: Path = typer.Argument(..., help="JSON分析报告路径", exists=True),
    move: bool = typer.Option(False, "--move", help="是否移动文件（否则复制）")
):
    """根据报告分类视频"""
    vb = VideoBrake()
    vb.classify_from_report(str(report_path), is_move=move)
    
    action = "移动" if move else "复制"
    console.print(f"[green]已完成文件{action}分类[/green]")


# 视频格式处理命令
@format_app.command("process")
def process_dir(
    folder_path: Path = typer.Argument(..., help="要处理的文件夹路径", exists=True)
):
    """处理目录(添加/移除.nov后缀和检查重复项)"""
    vb = VideoBrake()
    vb.process_videos_in_dir(str(folder_path))
    console.print(f"[green]已完成对目录 {folder_path} 的处理[/green]")


@format_app.command("add-nov")
def add_nov(
    file_path: Path = typer.Argument(..., help="要添加.nov后缀的视频文件路径", exists=True)
):
    """添加.nov后缀到单个文件"""
    vb = VideoBrake()
    success, result = vb.add_nov_extension(str(file_path))
    if success:
        console.print(f"[green]成功添加.nov后缀: {file_path}.nov[/green]")
    else:
        console.print(f"[red]添加.nov后缀失败: {result}[/red]")


@format_app.command("remove-nov")
def remove_nov(
    file_path: Path = typer.Argument(..., help="要移除.nov后缀的文件路径", exists=True)
):
    """移除单个文件的.nov后缀"""
    vb = VideoBrake()
    success, result = vb.remove_nov_extension(str(file_path))
    if success:
        console.print(f"[green]成功移除.nov后缀: {os.path.splitext(str(file_path))[0]}[/green]")
    else:
        console.print(f"[red]移除.nov后缀失败: {result}[/red]")


@format_app.command("check-duplicates")
def check_duplicates(
    folder_path: Path = typer.Argument(..., help="要检查重复项的文件夹路径", exists=True)
):
    """检查重复项"""
    vb = VideoBrake()
    nov_files, normal_files, hb_files = find_video_files(str(folder_path))
    vb.check_duplicates(str(folder_path), nov_files, normal_files, hb_files)


# 添加一个交互模式命令
@app.command("interactive")
def interactive():
    """启动交互式用户界面"""
    from videobrake.interactive import run_interactive
    sys.exit(run_interactive())


if __name__ == "__main__":
    app()
