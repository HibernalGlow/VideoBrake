"""
视频码率分析与分类工具 - 主程序入口

提供命令行接口和主要功能入口
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# 导入Rich库用于美化输出
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.logging import RichHandler
from rich.prompt import IntPrompt, FloatPrompt

# 导入程序模块
from bitv.video_analyzer import VideoAnalyzer
from bitv.video_processor import VideoProcessor
from bitv.common_utils import create_bitrate_levels

# 设置控制台对象
console = Console()

# 创建日志记录器
from loguru import logger
# def setup_logger(app_name="app", project_root=None):
#     """配置 Loguru 日志系统"""
#     # 获取项目根目录
#     if project_root is None:
#         project_root = Path(__file__).parent.parent.resolve()
    
#     # 清除默认处理器
#     logger.remove()
    
#     # 添加控制台处理器（简洁版格式）
#     logger.add(
#         sys.stdout,
#         level="INFO",
#         format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <blue>{elapsed}</blue> | <level>{level.icon} {level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
#     )
    
#     # 使用 datetime 构建日志路径
#     current_time = datetime.now()
#     date_str = current_time.strftime("%Y-%m-%d")
#     hour_str = current_time.strftime("%H")
#     minute_str = current_time.strftime("%M%S")
    
#     # 构建日志目录和文件路径
#     log_dir = os.path.join(project_root, "logs", app_name, date_str, hour_str)
#     os.makedirs(log_dir, exist_ok=True)
#     log_file = os.path.join(log_dir, f"{minute_str}.log")
    
#     # 添加文件处理器
#     logger.add(
#         log_file,
#         level="DEBUG",
#         rotation="10 MB",
#         retention="30 days",
#         compression="zip",
#         encoding="utf-8",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {elapsed} | {level.icon} {level: <8} | {name}:{function}:{line} - {message}",
#     )
    
#     # 创建配置信息字典
#     config_info = {
#         'log_file': log_file,
#     }
    
#     logger.info(f"日志系统已初始化，应用名称: {app_name}")
#     return logger, config_info

# # 初始化日志
# logger, _ = setup_logger(app_name="brakev")


def create_arg_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description='视频码率分析与分类工具')
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # analyze 子命令 - 分析视频文件夹
    analyze_parser = subparsers.add_parser('analyze', help='分析视频文件夹')
    analyze_parser.add_argument('--path', '-p', type=str, help='视频文件夹路径', required=True)
    analyze_parser.add_argument('--recursive', '-r', action='store_true', help='是否递归搜索子文件夹')
    analyze_parser.add_argument('--output', '-o', type=str, help='输出JSON报告路径')
    analyze_parser.add_argument('--step', '-s', type=float, default=5, help='码率等级步长(Mbps)')
    analyze_parser.add_argument('--levels', '-l', type=int, default=10, help='码率等级数量')
    
    # classify 子命令 - 对视频进行分类
    classify_parser = subparsers.add_parser('classify', help='对视频进行分类')
    classify_parser.add_argument('--path', '-p', type=str, help='源目录路径', required=True)
    classify_parser.add_argument('--target', '-t', type=str, help='目标目录路径')
    classify_parser.add_argument('--move', '-m', action='store_true', help='移动文件（默认为复制）')
    classify_parser.add_argument('--recursive', '-r', action='store_true', help='是否递归搜索子文件夹')
    classify_parser.add_argument('--step', '-s', type=float, default=5, help='码率等级步长(Mbps)')
    classify_parser.add_argument('--levels', '-l', type=int, default=10, help='码率等级数量')
    
    # report 子命令 - 根据JSON报告进行分类
    report_parser = subparsers.add_parser('report', help='根据JSON分析报告进行分类')
    report_parser.add_argument('--report', '-r', type=str, help='分析报告路径', required=True)
    report_parser.add_argument('--move', '-m', action='store_true', help='移动文件（默认为复制）')
    
    # analyze-file 子命令 - 分析单个视频文件
    analyze_file_parser = subparsers.add_parser('analyze-file', help='分析单个视频文件')
    analyze_file_parser.add_argument('--file', '-f', type=str, help='视频文件路径', required=True)
    
    return parser


def get_path_from_input(message: str = "请输入文件夹路径") -> str:
    """从用户输入获取路径"""
    while True:
        path = Prompt.ask(message)
        
        # 处理带引号的路径
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]  # 去除首尾的引号
            
        if not path:
            console.print("[yellow]路径不能为空[/yellow]")
            continue
            
        if not os.path.exists(path):
            console.print(f"[red]路径不存在: {path}[/red]")
            continue
            
        return path


def interactive_analyze():
    """交互式分析视频文件夹"""
    console.print(Panel.fit("[bold cyan]视频文件分析[/bold cyan]"))
    
    # 获取文件夹路径
    folder_path = get_path_from_input("请输入视频文件夹路径")
    
    # 询问是否递归搜索
    recursive = Confirm.ask("是否递归搜索子文件夹?", default=True)
    
    # 询问码率等级设置
    console.print("[cyan]设置码率等级参数[/cyan]")
    step_mb = FloatPrompt.ask("每档码率大小(Mbps)", default=1.0)
    max_levels = IntPrompt.ask("最大档位数量", default=10)
    
    # 创建分析器并分析文件夹
    try:
        analyzer = VideoAnalyzer(bitrate_step=step_mb, max_steps=max_levels)
        console.print(f"[cyan]开始分析文件夹: {folder_path}[/cyan]")
        
        # 分析文件夹
        result = analyzer.analyze_folder(folder_path, recursive=recursive)
        
        # 生成JSON报告
        if Confirm.ask("是否生成JSON报告?", default=True):
            report_path = analyzer.generate_json_report(result)
            console.print(f"[green]分析报告已保存: {report_path}[/green]")
            
            # 询问是否根据分析结果进行分类
            if Confirm.ask("是否根据分析结果对视频进行分类?", default=False):
                is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
                processor = VideoProcessor(analyzer)
                processor.classify_from_json_report(report_path, is_move=is_move)
        
        return True
    except Exception as e:
        console.print(f"[red]分析过程中出错: {str(e)}[/red]")
        logger.error(f"分析过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def interactive_classify():
    """交互式分类视频文件"""
    console.print(Panel.fit("[bold cyan]视频文件分类[/bold cyan]"))
    
    # 获取源文件夹路径
    source_dir = get_path_from_input("请输入源文件夹路径")
    
    # 询问目标目录
    use_same_dir = Confirm.ask("是否使用源文件夹作为目标文件夹?", default=True)
    target_dir = source_dir if use_same_dir else get_path_from_input("请输入目标文件夹路径")
    
    # 询问是否递归搜索
    recursive = Confirm.ask("是否递归搜索子文件夹?", default=True)
    
    # 询问是否移动文件
    is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
    
    # 询问码率等级设置
    console.print("[cyan]设置码率等级参数[/cyan]")
    step_mb = FloatPrompt.ask("每档码率大小(Mbps)", default=1.0)
    max_levels = IntPrompt.ask("最大档位数量", default=10)
    
    # 显示码率等级
    bitrate_levels = create_bitrate_levels(step_mb, max_levels)
    console.print("[cyan]码率等级设置:[/cyan]")
    for level, threshold in bitrate_levels.items():
        if threshold != float('inf'):
            console.print(f"  • {level}: {threshold/1000000:.1f}Mbps")
        else:
            console.print(f"  • {level}: 无限制")
    
    # 确认是否继续
    if not Confirm.ask("确认以上设置并开始分类?", default=True):
        console.print("[yellow]操作已取消[/yellow]")
        return False
    
    # 创建分析器和处理器
    try:
        analyzer = VideoAnalyzer(bitrate_step=step_mb, max_steps=max_levels)
        processor = VideoProcessor(analyzer)
        
        # 执行分类
        processor.classify_videos_by_bitrate(
            source_dir=source_dir,
            target_dir=target_dir,
            is_move=is_move,
            recursive=recursive,
            json_report=True
        )
        
        return True
    except Exception as e:
        console.print(f"[red]分类过程中出错: {str(e)}[/red]")
        logger.error(f"分类过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def interactive_report_classify():
    """交互式根据报告分类视频"""
    console.print(Panel.fit("[bold cyan]根据报告分类视频[/bold cyan]"))
    
    # 获取报告路径
    report_path = get_path_from_input("请输入JSON分析报告路径")
    
    # 询问是否移动文件
    is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
    
    # 创建处理器
    try:
        processor = VideoProcessor()
        
        # 执行分类
        processor.classify_from_json_report(report_path, is_move=is_move)
        
        return True
    except Exception as e:
        console.print(f"[red]分类过程中出错: {str(e)}[/red]")
        logger.error(f"分类过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def analyze_single_file(file_path: str):
    """分析单个视频文件"""
    console.print(Panel.fit("[bold cyan]视频文件分析[/bold cyan]"))
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        console.print(f"[red]文件不存在: {file_path}[/red]")
        return False
    
    try:
        analyzer = VideoAnalyzer()
        video_info = analyzer.analyze_video(file_path)
        
        if not video_info:
            console.print(f"[red]无法分析视频文件: {file_path}[/red]")
            return False
        
        # 获取码率等级
        bitrate_level = analyzer.get_video_bitrate_level(video_info)
        
        # 显示视频信息
        console.print(f"[green]文件名:[/green] {os.path.basename(file_path)}")
        console.print(f"[green]路径:[/green] {file_path}")
        console.print(f"[green]码率:[/green] {video_info.bitrate_mbps:.2f} Mbps")
        console.print(f"[green]码率等级:[/green] {bitrate_level}")
        console.print(f"[green]时长:[/green] {video_info.duration:.2f} 秒 ({video_info.duration / 60:.2f} 分钟)")
        console.print(f"[green]分辨率:[/green] {video_info.width}x{video_info.height}")
        console.print(f"[green]帧率:[/green] {video_info.fps:.2f} fps")
        console.print(f"[green]文件大小:[/green] {video_info.size_mb:.2f} MB")
        
        return True
    except Exception as e:
        console.print(f"[red]分析过程中出错: {str(e)}[/red]")
        logger.error(f"分析过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def interactive_menu():
    """交互式菜单"""
    while True:
        console.print(Panel.fit("[bold cyan]视频码率分析与分类工具[/bold cyan]"))
        console.print("1. 分析视频文件夹")
        console.print("2. 对视频进行分类")
        console.print("3. 根据JSON报告分类视频")
        console.print("4. 分析单个视频文件")
        console.print("0. 退出")
        
        choice = Prompt.ask("请选择功能", choices=["0", "1", "2", "3", "4"], default="1")
        
        if choice == "0":
            console.print("[yellow]程序已退出[/yellow]")
            break
        elif choice == "1":
            interactive_analyze()
        elif choice == "2":
            interactive_classify()
        elif choice == "3":
            interactive_report_classify()
        elif choice == "4":
            file_path = get_path_from_input("请输入视频文件路径")
            analyze_single_file(file_path)
        
        # 询问是否继续
        if not Confirm.ask("是否继续使用其他功能?", default=True):
            console.print("[yellow]程序已退出[/yellow]")
            break


def run_with_args(args):
    """使用命令行参数运行程序"""
    try:
        if args.command == 'analyze':
            # 创建分析器
            analyzer = VideoAnalyzer(bitrate_step=args.step, max_steps=args.levels)
            
            # 分析文件夹
            result = analyzer.analyze_folder(args.path, recursive=args.recursive)
            
            # 生成JSON报告
            analyzer.generate_json_report(result, args.output)
            
        elif args.command == 'classify':
            # 创建分析器和处理器
            analyzer = VideoAnalyzer(bitrate_step=args.step, max_steps=args.levels)
            processor = VideoProcessor(analyzer)
            
            # 执行分类
            processor.classify_videos_by_bitrate(
                source_dir=args.path,
                target_dir=args.target,
                is_move=args.move,
                recursive=args.recursive
            )
            
        elif args.command == 'report':
            # 创建处理器
            processor = VideoProcessor()
            
            # 根据报告分类
            processor.classify_from_json_report(args.report, is_move=args.move)
            
        elif args.command == 'analyze-file':
            # 分析单个文件
            analyze_single_file(args.file)
            
        return 0
    except Exception as e:
        console.print(f"[red]程序运行时出错: {str(e)}[/red]")
        logger.error(f"程序运行时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


def main():
    """主函数"""
    try:
        # 创建命令行参数解析器
        parser = create_arg_parser()
        
        # 解析命令行参数
        args = parser.parse_args()
        
        # 如果没有提供子命令，使用交互式菜单
        if not args.command:
            return interactive_menu()
        
        # 使用命令行参数运行
        return run_with_args(args)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]程序被用户中断[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]程序运行时出错: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


def interactive_main():
    """交互式界面主入口，供主包调用"""
    # setup_logger("bitv")
    interactive_menu()


def analyze_file(file_path: str):
    """分析单个视频文件，供主包调用
    
    Args:
        file_path: 视频文件路径
    """
    # setup_logger("bitv")
    analyze_single_file(file_path)


def analyze_dir(dir_path: str, recursive: bool = False):
    """分析文件夹中的所有视频，供主包调用
    
    Args:
        dir_path: 视频文件夹路径
        recursive: 是否递归处理子文件夹
    """
    # setup_logger("bitv")
    # 创建分析器
    analyzer = VideoAnalyzer()
    
    # 分析文件夹
    result = analyzer.analyze_folder(dir_path, recursive=recursive)
    
    # 生成JSON报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(dir_path, f"video_analysis_{timestamp}.json")
    analyzer.generate_json_report(result, output_file)


def main():
    """命令行主入口"""
    # setup_logger("bitv")
    
    # 如果没有命令行参数，进入交互式菜单
    if len(sys.argv) == 1:
        interactive_menu()
        return


if __name__ == "__main__":
    sys.exit(main())