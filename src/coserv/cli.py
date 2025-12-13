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
        console.print("\n[bold]请选择工作流程：[/bold]\n")
        console.print("[dim]新工作流程（推荐）：[/dim]")
        
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]1[/cyan]", "扫描文件夹 (scan) - 新")
        table.add_row("[cyan]2[/cyan]", "批量识别 (identify) - 新")
        table.add_row("[cyan]3[/cyan]", "批量处理 (process) - 新")
        table.add_row("")
        table.add_row("[dim]旧工作流程：[/dim]")
        table.add_row("[cyan]4[/cyan]", "提取关键帧 (prepare)")
        table.add_row("[cyan]5[/cyan]", "生成识别指令 (generate-prompt)")
        table.add_row("[cyan]6[/cyan]", "合并识别结果 (merge)")
        table.add_row("[cyan]7[/cyan]", "整理视频文件 (organize)")
        table.add_row("")
        table.add_row("[cyan]0[/cyan]", "退出")
        
        console.print(table)
        
        choice = Prompt.ask("\n选择", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")
    else:
        print("\n请选择工作流程：")
        print("\n新工作流程（推荐）：")
        print("1. 扫描文件夹 (scan)")
        print("2. 批量识别 (identify)")
        print("3. 批量处理 (process)")
        print("\n旧工作流程：")
        print("4. 提取关键帧 (prepare)")
        print("5. 生成识别指令 (generate-prompt)")
        print("6. 合并识别结果 (merge)")
        print("7. 整理视频文件 (organize)")
        print("\n0. 退出")
        choice = input("\n选择 [1]: ").strip() or "1"
    
    if choice == "1":
        run_scan_interactive()
    elif choice == "2":
        run_identify_interactive()
    elif choice == "3":
        run_process_interactive()
    elif choice == "4":
        run_prepare_interactive()
    elif choice == "5":
        run_generate_prompt()
    elif choice == "6":
        run_merge()
    elif choice == "7":
        run_organize_interactive()
    elif choice == "0":
        sys.exit(0)




def run_scan_interactive():
    """交互式运行 scan"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📂 扫描文件夹[/bold cyan]\n")
        target_dir = Prompt.ask("目标文件夹目录路径")
        limit = Prompt.ask("限制处理数量（留空处理全部）", default="")
        max_frames = Prompt.ask("每个文件夹提取的图片数量", default="5")
        image_size = Prompt.ask("图片压缩目标大小（KB）", default="25")
        save_json = Confirm.ask("是否保存 JSON 文件？", default=True)
    else:
        print("\n📂 扫描文件夹")
        target_dir = input("目标文件夹目录路径: ")
        limit = input("限制处理数量（留空处理全部）: ")
        max_frames = input("每个文件夹提取的图片数量 [5]: ") or "5"
        image_size = input("图片压缩目标大小（KB）[25]: ") or "25"
        save_json_input = input("是否保存 JSON 文件？[Y/n]: ").strip().lower()
        save_json = save_json_input != 'n'
    
    from scan import FolderScanner
    try:
        scanner = FolderScanner(
            target_dir,
            max_frames=int(max_frames),
            image_size_kb=int(image_size),
            save_json = save_json
        )
        scanner.scan_all_folders(limit=int(limit) if limit else None)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 错误: {e}[/red]")
        else:
            print(f"❌ 错误: {e}")


def run_identify_interactive():
    """交互式运行 identify"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]🤖 批量识别[/bold cyan]\n")
        scan_file = Prompt.ask("扫描文件名（例如: scan_20231214_120000.json）")
        no_skip = Confirm.ask("重新识别所有（包括已识别的）？", default=False)
    else:
        print("\n🤖 批量识别")
        scan_file = input("扫描文件名: ")
        no_skip_input = input("重新识别所有（包括已识别的）？[y/N]: ").strip().lower()
        no_skip = no_skip_input == 'y'
    
    from identify import BatchIdentifier
    try:
        identifier = BatchIdentifier(scan_file)
        identifier.identify_all(skip_identified=not no_skip)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 错误: {e}[/red]")
        else:
            print(f"❌ 错误: {e}")


def run_process_interactive():
    """交互式运行 process"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]⚙️ 批量处理[/bold cyan]\n")
        scan_file = Prompt.ask("扫描文件名（例如: scan_20231214_120000.json）")
        mode = Prompt.ask("处理模式", choices=["move", "copy"], default="move")
        dry_run = Confirm.ask("测试模式（不实际移动/复制文件）？", default=True)
    else:
        print("\n⚙️ 批量处理")
        scan_file = input("扫描文件名: ")
        mode = input("处理模式 [move/copy, 默认 move]: ").strip().lower() or "move"
        dry_run_input = input("测试模式（不实际移动/复制文件）？[Y/n]: ").strip().lower()
        dry_run = dry_run_input != 'n'
    
    from process import BatchProcessor
    try:
        processor = BatchProcessor(scan_file, mode=mode)
        processor.process_all(dry_run=dry_run)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 错误: {e}[/red]")
        else:
            print(f"❌ 错误: {e}")


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
    
    # === 新工作流程子命令 ===
    # scan 子命令
    scan_parser = subparsers.add_parser('scan', help='扫描文件夹（新工作流程）')
    scan_parser.add_argument('target_dir', type=str, help='目标文件夹目录路径')
    scan_parser.add_argument('--output', type=str, default=None, help='输出目录（默认: 视频目录/coserv_output）')
    scan_parser.add_argument('--limit', type=int, default=None, help='限制处理数量')
    scan_parser.add_argument('--max-frames', type=int, default=5, help='每个文件夹提取的最大图片数量（默认: 5）')
    scan_parser.add_argument('--image-size', type=int, default=25, help='图片压缩目标大小（KB，默认: 25）')
    scan_parser.add_argument('--no-json', action='store_true', help='不保存 JSON 文件，只生成图片')
    
    # identify 子命令
    identify_parser = subparsers.add_parser('identify', help='批量识别（新工作流程）')
    identify_parser.add_argument('--scan-file', type=str, required=True, help='扫描文件名')
    identify_parser.add_argument('--output', type=str, default=None, help='输出目录（默认: 从扫描文件推断）')
    identify_parser.add_argument('--no-skip', action='store_true', help='重新识别所有')
    identify_parser.add_argument('--no-auto-save', action='store_true', help='不自动保存')
    
    # process 子命令
    process_parser = subparsers.add_parser('process', help='批量处理（新工作流程）')
    process_parser.add_argument('--scan-file', type=str, required=True, help='扫描文件名')
    process_parser.add_argument('--output', type=str, default=None, help='输出目录（默认: 从扫描文件推断）')
    process_parser.add_argument('--mode', type=str, choices=['move', 'copy'], default='move', help='处理模式')
    process_parser.add_argument('--dry-run', action='store_true', help='测试模式')
    
    # === 旧工作流程子命令 ===
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
    # === 新工作流程命令 ===
    if args.command == 'scan':
        from scan import FolderScanner
        scanner = FolderScanner(
            args.target_dir, 
            args.output,
            max_frames=args.max_frames,
            image_size_kb=args.image_size,
            save_json=not args.no_json
        )
        scanner.scan_all_folders(limit=args.limit)
    
    elif args.command == 'identify':
        from identify import BatchIdentifier
        identifier = BatchIdentifier(args.scan_file, args.output)
        identifier.identify_all(
            skip_identified=not args.no_skip,
            auto_save=not args.no_auto_save
        )
    
    elif args.command == 'process':
        from process import BatchProcessor
        processor = BatchProcessor(args.scan_file, args.output, args.mode)
        processor.process_all(dry_run=args.dry_run)
    
    # === 旧工作流程命令 ===
    elif args.command == 'prepare':
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
