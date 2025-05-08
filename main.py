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
    vb = VideoBrake()
    
    # 显示两个主要子包
    console.print("\n[green]1. 可用的子包:[/green]")
    console.print("   • bitscaculate: 视频码率分析与分类模块")
    console.print("   • formatfliter: 视频格式过滤器模块")
    
    # 演示如何使用统一接口
    console.print("\n[green]2. 使用示例:[/green]")
    console.print("[yellow]# 通过统一接口调用码率分析模块[/yellow]")
    console.print("from videobrake import VideoBrake")
    console.print("vb = VideoBrake()")
    console.print("analyzer = vb.bitscaculate.video_analyzer.VideoAnalyzer()")
    console.print("processor = vb.bitscaculate.video_processor.VideoProcessor(analyzer)")
    console.print("result = processor.classify_videos_by_bitrate('path/to/videos')")
    
    console.print("\n[yellow]# 通过统一接口调用格式过滤器模块[/yellow]")
    console.print("from videobrake import VideoBrake")
    console.print("vb = VideoBrake()")
    console.print("vb.formatfliter.core.process_videos('path/to/videos')")
    
    console.print("\n[yellow]# 也可以直接导入常用类[/yellow]")
    console.print("from videobrake import VideoAnalyzer, VideoProcessor, FormatFilter")
    console.print("analyzer = VideoAnalyzer()")
    console.print("processor = VideoProcessor(analyzer)")
    console.print("format_filter = FormatFilter()")
    
    console.print("\n[blue]提示：这只是演示代码，实际使用时请替换为真实路径[/blue]")


if __name__ == "__main__":
    sys.exit(main())
