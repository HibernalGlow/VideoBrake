"""
AudioV 命令行版本
提供简单的命令行接口用于快速测试，默认使用极速模式
"""

import sys
import argparse
from pathlib import Path

# 添加 src 目录到路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from audiov.ffmpeg_wrapper import ffmpeg_wrapper
from audiov.file_handler import video_handler
from rich.console import Console

console = Console()

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="AudioV - 视频音频提取工具 (命令行版)")
    parser.add_argument("input", help="输入视频文件或目录")
    parser.add_argument("-o", "--output", help="输出目录 (默认: extracted_audio)")
    parser.add_argument("-f", "--format", choices=["mp3", "aac", "wav", "flac", "m4a", "copy"], 
                       default="copy", help="音频格式 (默认: copy 极速模式)")
    parser.add_argument("-q", "--quality", help="质量参数 (如: -q:a 2)")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归扫描子目录")
    parser.add_argument("--test", action="store_true", help="仅测试 FFmpeg 可用性")
    parser.add_argument("--slow", action="store_true", help="禁用极速模式，强制重新编码")
    
    args = parser.parse_args()
    
    # 测试模式
    if args.test:
        console.print("🔍 测试 FFmpeg 可用性...", style="cyan")
        if ffmpeg_wrapper.check_ffmpeg_available():
            console.print("✅ FFmpeg 可用", style="green")
            return 0
        else:
            console.print("❌ FFmpeg 不可用", style="red")
            return 1
    
    # 检查 FFmpeg
    if not ffmpeg_wrapper.check_ffmpeg_available():
        console.print("❌ FFmpeg 不可用，请确保已安装并添加到 PATH", style="red")
        return 1
    
    # 处理输入
    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"❌ 输入路径不存在: {args.input}", style="red")
        return 1
    
    # 获取视频文件列表
    if input_path.is_file():
        if video_handler.is_video_file(str(input_path)):
            video_files = [str(input_path)]
        else:
            console.print("❌ 输入文件不是支持的视频格式", style="red")
            return 1
    elif input_path.is_dir():
        video_files = video_handler.scan_directory(str(input_path), args.recursive)
        if not video_files:
            console.print("❌ 目录中没有找到视频文件", style="red")
            return 1
    else:
        console.print("❌ 无效的输入路径", style="red")
        return 1
    
    # 设置输出目录
    output_dir = args.output or "extracted_audio"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 如果用户没有指定 --slow 且选择了 copy 以外的格式，提醒可以使用极速模式
    if not args.slow and args.format != "copy":
        console.print("💡 提示：使用 '-f copy' 可启用极速模式，速度更快且无质量损失", style="yellow")
    
    # 如果用户指定了 --slow，则强制使用指定格式重新编码
    if args.slow and args.format == "copy":
        console.print("⚠️  --slow 参数与 copy 格式冲突，改为使用 mp3 格式", style="yellow")
        args.format = "mp3"
    
    console.print(f"📹 找到 {len(video_files)} 个视频文件", style="green")
    
    if args.format == "copy":
        console.print("⚡ 极速模式：直接复制音频流", style="bold yellow")
    else:
        console.print(f"🎵 音频格式: {args.format.upper()}", style="cyan")
    
    console.print(f"📁 输出目录: {output_dir}", style="blue")
    
    # 处理文件
    success_count = 0
    for i, video_file in enumerate(video_files, 1):
        console.print(f"\n[{i}/{len(video_files)}] 处理: {Path(video_file).name}", style="yellow")
        
        # 生成输出路径
        from audiov.config import config_manager
        formats = config_manager.get_audio_formats()
        
        if args.format == "copy":
            # 极速模式：检测原始音频格式
            extension = ffmpeg_wrapper.get_audio_extension(video_file)
        else:
            extension = formats.get(args.format, {}).get('extension', '.mp3')
        
        output_file = Path(output_dir) / f"{Path(video_file).stem}{extension}"
        
        # 提取音频
        success, error = ffmpeg_wrapper.extract_audio(
            video_file,
            str(output_file),
            args.format,
            args.quality or ""
        )
        
        if success:
            success_count += 1
        else:
            console.print(f"❌ 失败: {error}", style="red")
    
    # 显示结果
    console.print(f"\n🎉 处理完成: {success_count}/{len(video_files)} 个文件成功", 
                 style="bold green" if success_count == len(video_files) else "bold yellow")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n👋 用户中断操作", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ 发生错误: {e}", style="red")
        sys.exit(1)
