"""
VideoBrake - 视频处理工具集

命令行入口
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console

from videobrake import VideoBrake, __version__
from videobrake.interactive import run_interactive

console = Console()


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description="VideoBrake - 视频处理工具集")
    
    # 添加全局选项
    parser.add_argument('--version', '-v', action='store_true', help='显示版本信息')
    parser.add_argument('--interactive', '-i', action='store_true', help='启动交互式界面')
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='可用子命令')
    
    # analyze 子命令
    analyze_parser = subparsers.add_parser('analyze', help='分析视频文件或文件夹')
    analyze_parser.add_argument('--file', '-f', help='分析单个视频文件')
    analyze_parser.add_argument('--dir', '-d', help='分析文件夹')
    analyze_parser.add_argument('--recursive', '-r', action='store_true', help='递归搜索子文件夹')
    
    # classify 子命令
    classify_parser = subparsers.add_parser('classify', help='按码率对视频进行分类')
    classify_parser.add_argument('--dir', '-d', required=True, help='源目录')
    classify_parser.add_argument('--target', '-t', help='目标目录(默认与源目录相同)')
    classify_parser.add_argument('--move', '-m', action='store_true', help='移动文件(默认为复制)')
    
    # format 子命令
    format_parser = subparsers.add_parser('format', help='格式过滤器功能')
    format_parser.add_argument('--dir', '-d', help='要处理的目录')
    format_parser.add_argument('--add-nov', '-a', help='添加.nov后缀的文件路径')
    format_parser.add_argument('--remove-nov', '-r', help='移除.nov后缀的文件路径')
    format_parser.add_argument('--check', '-c', help='检查重复项的目录')
    
    return parser


def main():
    """主函数"""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        # 显示版本信息
        if args.version:
            console.print(f"VideoBrake 版本: {__version__}")
            return 0
        
        # 启动交互式界面
        if args.interactive:
            return run_interactive()
        
        # 如果没有指定命令，默认启动交互式界面
        if not args.command:
            return run_interactive()
            
        # 创建VideoBrake实例
        vb = VideoBrake()
        
        # 根据命令执行相应的功能
        if args.command == 'analyze':
            if args.file:
                # 分析单个文件
                console.print(f"[blue]正在分析视频: {args.file}[/blue]")
                video_info = vb.analyze_video(args.file)
                if video_info:
                    console.print(f"[green]文件名:[/green] {video_info.filename}")
                    console.print(f"[green]码率:[/green] {video_info.bitrate_mbps:.2f} Mbps")
                    console.print(f"[green]时长:[/green] {video_info.duration:.2f} 秒")
                    console.print(f"[green]分辨率:[/green] {video_info.width}x{video_info.height}")
                else:
                    console.print("[red]无法分析该视频文件[/red]")
            
            elif args.dir:
                # 分析文件夹
                console.print(f"[blue]正在分析文件夹: {args.dir}[/blue]")
                result = vb.analyze_folder(args.dir, args.recursive)
                
                # 生成报告
                if result and result.get("videos"):
                    report_path = vb.generate_json_report(result)
                    console.print(f"[green]分析完成，报告保存至: {report_path}[/green]")
                else:
                    console.print("[yellow]未找到视频文件或分析失败[/yellow]")
            else:
                console.print("[yellow]请指定文件或目录[/yellow]")
                return 1
        
        elif args.command == 'classify':
            # 分类视频
            target_dir = args.target if args.target else args.dir
            console.print(f"[blue]正在{'移动' if args.move else '复制'}视频到分类文件夹...[/blue]")
            result = vb.classify_videos(args.dir, target_dir, args.move)
            
            if result.get("success"):
                console.print(f"[green]操作完成! 处理了 {result.get('total_files', 0)} 个文件[/green]")
            else:
                console.print(f"[red]操作失败: {result.get('error', '未知错误')}[/red]")
        
        elif args.command == 'format':
            if args.dir:
                # 处理整个目录
                console.print(f"[blue]处理目录: {args.dir}[/blue]")
                vb.process_videos_in_dir(args.dir)
            
            elif args.add_nov:
                # 添加.nov后缀
                success, result = vb.add_nov_extension(args.add_nov)
                if success:
                    console.print(f"[green]成功添加.nov后缀: {args.add_nov}.nov[/green]")
                else:
                    console.print(f"[red]添加.nov后缀失败: {result}[/red]")
            
            elif args.remove_nov:
                # 移除.nov后缀
                success, result = vb.remove_nov_extension(args.remove_nov)
                if success:
                    console.print(f"[green]成功移除.nov后缀: {os.path.splitext(args.remove_nov)[0]}[/green]")
                else:
                    console.print(f"[red]移除.nov后缀失败: {result}[/red]")
            
            elif args.check:
                # 检查重复项
                console.print(f"[blue]检查目录中的重复项: {args.check}[/blue]")
                nov_files, normal_files, hb_files = vb.find_video_files(args.check)
                vb.check_duplicates(args.check, nov_files, normal_files, hb_files)
            else:
                console.print("[yellow]请指定一个操作选项[/yellow]")
                return 1
        
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
    sys.exit(main())