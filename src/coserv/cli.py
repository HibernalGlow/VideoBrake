"""
Coserv CLI - 统一命令行入口
支持交互式菜单和子命令
"""

import sys
import argparse
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠ 建议安装 rich 以获得更好的交互体验: pip install rich")


console = Console() if RICH_AVAILABLE else None


def show_banner():
    """显示欢迎信息"""
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]Coser视频自动分类系统[/bold cyan]\n"
            "[dim]让机器帮你整理 Coser 视频[/dim]",
            border_style="cyan"
        ))
    else:
        print("="*60)
        print(" Coser视频自动分类系统")
        print(" 让机器帮你整理 Coser 视频")
        print("="*60)


def interactive_mode():
    """交互式操作模式"""
    show_banner()
    
    if RICH_AVAILABLE:
        console.print("\n[bold]请选择操作：[/bold]\n")
        
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]1[/cyan]", "提取关键帧 (prepare)")
        table.add_row("[cyan]2[/cyan]", "生成识别指令 (generate-prompt)")
        table.add_row("[cyan]3[/cyan]", "合并识别结果 (merge)")
        table.add_row("[cyan]4[/cyan]", "整理视频文件 (organize)")
        table.add_row("[cyan]5[/cyan]", "退出")
        
        console.print(table)
        
        choice = Prompt.ask("\n选择", choices=["1", "2", "3", "4", "5"], default="1")
    else:
        print("\n请选择操作：")
        print("1. 提取关键帧 (prepare)")
        print("2. 生成识别指令 (generate-prompt)")
        print("3. 合并识别结果 (merge)")
        print("4. 整理视频文件 (organize)")
        print("5. 退出")
        choice = input("\n选择 [1]: ").strip() or "1"
    
    if choice == "1":
        run_prepare_interactive()
    elif choice == "2":
        run_generate_prompt()
    elif choice == "3":
        run_merge()
    elif choice == "4":
        run_organize_interactive()
    elif choice == "5":
        sys.exit(0)


def run_prepare_interactive():
    """交互式运行prepare"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📸 提取关键帧[/bold cyan]\n")
        video_dir = Prompt.ask("视频目录路径")
        limit = Prompt.ask("限制处理数量（留空处理全部）", default="")
    else:
        print("\n📸 提取关键帧")
        video_dir = input("视频目录路径: ")
        limit = input("限制处理数量（留空处理全部）: ")
    
    # 构建命令
    from prepare import VideoPreparer
    try:
        preparer = VideoPreparer(video_dir)
        preparer.prepare_all(limit=int(limit) if limit else None)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 错误: {e}[/red]")
        else:
            print(f"❌ 错误: {e}")


def run_generate_prompt():
    """运行generate_prompt"""
    from generate_prompt import generate_instructions
    generate_instructions()


def run_merge():
    """运行merge_results"""
    from merge_results import merge_results
    merge_results()


def run_organize_interactive():
    """交互式运行organize"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📂 整理视频文件[/bold cyan]\n")
        video_dir = Prompt.ask("视频目录路径")
        dry_run = Confirm.ask("测试模式（不实际移动文件）？", default=True)
    else:
        print("\n📂 整理视频文件")
        video_dir = input("视频目录路径: ")
        dry_run_input = input("测试模式（不实际移动文件）？[Y/n]: ").strip().lower()
        dry_run = dry_run_input != 'n'
    
    from organize import VideoOrganizer
    try:
        organizer = VideoOrganizer(video_dir)
        organizer.organize_all(dry_run=dry_run)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 错误: {e}[/red]")
        else:
            print(f"❌ 错误: {e}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Coser视频自动分类系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # prepare 子命令
    prepare_parser = subparsers.add_parser('prepare', help='提取关键帧')
    prepare_parser.add_argument('video_dir', type=str, help='视频目录路径')
    prepare_parser.add_argument('--output', type=str, default='output', help='输出目录')
    prepare_parser.add_argument('--limit', type=int, default=None, help='限制处理数量')
    
    # generate-prompt 子命令
    subparsers.add_parser('generate-prompt', help='生成识别指令')
    
    # merge 子命令  
    subparsers.add_parser('merge', help='合并识别结果')
    
    # organize 子命令
    organize_parser = subparsers.add_parser('organize', help='整理视频文件')
    organize_parser.add_argument('video_dir', type=str, help='视频目录路径')
    organize_parser.add_argument('--results', type=str, default='output/results.json', help='结果文件路径')
    organize_parser.add_argument('--dry-run', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    # 如果没有子命令，进入交互模式
    if not args.command:
        interactive_mode()
        return
    
    # 执行子命令
    if args.command == 'prepare':
        from prepare import VideoPreparer
        preparer = VideoPreparer(args.video_dir, args.output)
        preparer.prepare_all(limit=args.limit)
    
    elif args.command == 'generate-prompt':
        from generate_prompt import generate_instructions
        generate_instructions()
    
    elif args.command == 'merge':
        from merge_results import merge_results
        merge_results()
    
    elif args.command == 'organize':
        from organize import VideoOrganizer
        organizer = VideoOrganizer(args.video_dir, args.results)
        organizer.organize_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
