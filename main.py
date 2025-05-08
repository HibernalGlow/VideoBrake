from pathlib import Path
import sys
import argparse
from rich.console import Console
from videobrake import VideoBrake

console = Console()


def main():
    """VideoBrake主程序入口"""
    parser = argparse.ArgumentParser(description="VideoBrake - 视频处理工具集")
    parser.add_argument('--version', '-v', action='store_true', help='显示版本信息')
    parser.add_argument('--demo', '-d', action='store_true', help='运行功能演示')
    
    args = parser.parse_args()
    
    if args.version:
        from videobrake import __version__
        print(f"VideoBrake 版本: {__version__}")
        return 0
        
    if args.demo:
        run_demo()
        return 0
    
    # 默认显示使用信息
    console.print("[bold cyan]VideoBrake - 视频处理工具集[/bold cyan]")
    console.print("提供统一接口调用各个子包功能")
    console.print("\n可用的工具包:")
    console.print("1. bitscaculate - 视频码率分析与分类工具")
    console.print("   - 命令: bitscaculate")
    console.print("2. formatfliter - 视频格式过滤器")
    console.print("   - 命令: formatfliter")
    console.print("\n运行示例演示:")
    console.print("   python main.py --demo")
    
    return 0


def run_demo():
    """运行功能演示"""
    console.print("[bold cyan]VideoBrake 功能演示[/bold cyan]")
    
    # 创建统一接口实例
    vb = VideoBrake(bitrate_step=2.0, max_steps=8)
    
    # 显示统一接口的功能
    console.print("\n[green]1. 统一接口提供的功能:[/green]")
    methods = [method for method in dir(vb) if callable(getattr(vb, method)) and not method.startswith("_")]
    for method in methods:
        doc = getattr(vb, method).__doc__
        if doc:
            console.print(f"   • {method}: {doc}")
    
    # 演示如何使用统一接口
    console.print("\n[green]2. 使用示例:[/green]")
    console.print("[yellow]# 分析单个视频文件[/yellow]")
    console.print("video_path = 'path/to/video.mp4'")
    console.print("video_info = vb.analyze_video(video_path)")
    
    console.print("\n[yellow]# 分析文件夹[/yellow]")
    console.print("folder_path = 'path/to/videos/'")
    console.print("result = vb.analyze_folder(folder_path)")
    console.print("report_path = vb.generate_json_report(result)")
    
    console.print("\n[yellow]# 根据码率分类视频[/yellow]")
    console.print("vb.classify_videos(folder_path, is_move=False)")
    
    console.print("\n[yellow]# 处理视频格式[/yellow]")
    console.print("vb.process_videos_in_dir(folder_path)")
    console.print("vb.add_nov_extension('path/to/video.mp4')")
    console.print("vb.check_duplicates(folder_path)")
    
    console.print("\n[blue]提示：这只是演示代码，实际使用时请替换为真实路径[/blue]")


if __name__ == "__main__":
    sys.exit(main())
