"""
用户界面模块
提供 Rich 终端交互界面
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.live import Live

from .config import config_manager
from .file_handler import video_handler
from .ffmpeg_wrapper import ffmpeg_wrapper

console = Console()

class InteractiveUI:
    """交互式用户界面"""
    
    def __init__(self):
        """初始化界面"""
        self.video_files = []
        self.output_directory = ""
        self.audio_format = "mp3"
        self.quality_options = ""
    
    def show_welcome(self) -> None:
        """显示欢迎信息"""
        welcome_text = Text()
        welcome_text.append("🎵 AudioV - 视频音频提取工具\n", style="bold cyan")
        welcome_text.append("使用 FFmpeg 从视频文件中提取音频\n", style="dim")
        welcome_text.append("支持多种格式: MP3, AAC, WAV, FLAC, M4A", style="green")
        
        panel = Panel(
            welcome_text,
            title="欢迎使用",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
    
    def check_ffmpeg(self) -> bool:
        """检查 FFmpeg 是否可用"""
        console.print("🔍 检查 FFmpeg...", style="cyan")
        
        if ffmpeg_wrapper.check_ffmpeg_available():
            console.print("✅ FFmpeg 已就绪", style="green")
            return True
        else:
            console.print("❌ FFmpeg 不可用或未安装", style="red")
            console.print("请确保 FFmpeg 已安装并添加到系统 PATH 中", style="yellow")
            return False
    
    def select_input_method(self) -> str:
        """选择输入方式"""
        console.print("\n📂 选择视频文件输入方式:", style="bold")
        
        choices = [
            "1. 扫描目录",
            "2. 手动输入文件路径",
            "3. 从剪贴板粘贴路径"
        ]
        
        for choice in choices:
            console.print(f"   {choice}")
        
        while True:
            selection = Prompt.ask(
                "请选择",
                choices=["1", "2", "3"],
                default="1"
            )
            
            if selection in ["1", "2", "3"]:
                return selection
    
    def scan_directory_input(self) -> List[str]:
        """目录扫描输入"""
        while True:
            directory = Prompt.ask("📁 请输入要扫描的目录路径")
            
            if not directory:
                continue
            
            directory_path = Path(directory)
            if not directory_path.exists():
                console.print("❌ 目录不存在，请重新输入", style="red")
                continue
            
            if not directory_path.is_dir():
                console.print("❌ 输入的路径不是目录，请重新输入", style="red")
                continue
            
            recursive = Confirm.ask("🔄 是否递归扫描子目录?", default=True)
            
            console.print("🔍 正在扫描...", style="cyan")
            video_files = video_handler.scan_directory(directory, recursive)
            
            if not video_files:
                console.print("❌ 未找到视频文件", style="red")
                if not Confirm.ask("是否重新选择目录?", default=True):
                    return []
                continue
            
            return video_files
    
    def manual_input(self) -> List[str]:
        """手动输入文件路径"""
        console.print("📝 请输入视频文件路径 (每行一个，输入空行结束):")
        
        file_paths = []
        while True:
            path = Prompt.ask("文件路径", default="")
            if not path:
                break
            file_paths.append(path)
        
        return video_handler.validate_files(file_paths)
    
    def clipboard_input(self) -> List[str]:
        """从剪贴板输入"""
        try:
            import pyperclip
            clipboard_content = pyperclip.paste()
            
            if not clipboard_content:
                console.print("❌ 剪贴板为空", style="red")
                return []
            
            console.print(f"📋 剪贴板内容: {clipboard_content[:100]}...", style="dim")
            
            # 按行分割
            lines = clipboard_content.strip().split('\n')
            file_paths = [line.strip() for line in lines if line.strip()]
            
            return video_handler.validate_files(file_paths)
            
        except ImportError:
            console.print("❌ pyperclip 库未安装，无法使用剪贴板功能", style="red")
            return []
        except Exception as e:
            console.print(f"❌ 读取剪贴板失败: {e}", style="red")
            return []
    
    def get_video_files(self) -> List[str]:
        """获取视频文件列表"""
        input_method = self.select_input_method()
        
        if input_method == "1":
            return self.scan_directory_input()
        elif input_method == "2":
            return self.manual_input()
        elif input_method == "3":
            return self.clipboard_input()
        else:
            return []
    
    def select_audio_format(self) -> Tuple[str, str]:
        """选择音频格式"""
        console.print("\n🎵 选择音频格式:", style="bold")
        
        formats = config_manager.get_audio_formats()
        format_list = list(formats.keys())
        
        # 检查是否启用极速模式默认
        fast_mode_default = config_manager.get('processing.fast_mode_default', True)
        
        table = Table(title="支持的音频格式")
        table.add_column("序号", style="cyan", no_wrap=True)
        table.add_column("格式", style="magenta")
        table.add_column("描述", style="green")
        table.add_column("编码器", style="blue")
        
        # 如果启用极速模式默认，将极速模式放在第一位
        if fast_mode_default and 'copy' in formats:
            # 重新排序，把 copy 放在最前面
            format_list = ['copy'] + [f for f in format_list if f != 'copy']
        
        for i, format_name in enumerate(format_list, 1):
            format_info = formats[format_name]
            style = "bold yellow" if format_name == 'copy' else ""
            table.add_row(
                str(i),
                format_name.upper() + (" 🚀" if format_name == 'copy' else ""),
                format_info.get('description', ''),
                format_info.get('codec', ''),
                style=style
            )
        
        console.print(table)
        console.print("💡 推荐使用极速模式 (COPY)，速度最快，无质量损失", style="yellow")
        
        while True:
            try:
                default_choice = 1 if fast_mode_default and format_list[0] == 'copy' else 1
                selection = IntPrompt.ask(
                    "请选择格式序号",
                    default=default_choice,
                    show_default=True
                )
                
                if 1 <= selection <= len(format_list):
                    selected_format = format_list[selection - 1]
                    quality = formats[selected_format].get('quality', '')
                    
                    # 极速模式不需要质量参数
                    if selected_format == 'copy':
                        console.print("⚡ 极速模式：直接复制音频流，无需设置质量参数", style="bold green")
                        return selected_format, ""
                    
                    # 询问是否自定义质量参数
                    if Confirm.ask(f"是否自定义质量参数? (当前: {quality or '默认'})", default=False):
                        custom_quality = Prompt.ask("请输入质量参数", default=quality)
                        return selected_format, custom_quality
                    else:
                        return selected_format, quality
                else:
                    console.print("❌ 无效的选择，请重新输入", style="red")
            except KeyboardInterrupt:
                console.print("\n👋 用户取消操作", style="yellow")
                return "", ""
    
    def select_output_directory(self) -> str:
        """选择输出目录"""
        console.print("\n📁 设置输出目录:", style="bold")
        
        default_dir = config_manager.get_output_directory()
        
        choices = [
            f"1. 使用默认目录 ({default_dir})",
            "2. 自定义目录",
            "3. 与源文件相同目录"
        ]
        
        for choice in choices:
            console.print(f"   {choice}")
        
        while True:
            selection = Prompt.ask(
                "请选择",
                choices=["1", "2", "3"],
                default="3"
            )
            
            if selection == "1":
                return default_dir
            elif selection == "2":
                while True:
                    custom_dir = Prompt.ask("请输入输出目录路径")
                    if custom_dir:
                        return custom_dir
            elif selection == "3":
                return "same_as_source"
    
    def show_processing_summary(self) -> bool:
        """显示处理摘要并确认"""
        console.print("\n📋 处理摘要:", style="bold")
        
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("项目", style="cyan")
        summary_table.add_column("值", style="white")
        
        summary_table.add_row("视频文件数量", str(len(self.video_files)))
        summary_table.add_row("音频格式", self.audio_format.upper())
        summary_table.add_row("输出目录", self.output_directory)
        if self.quality_options:
            summary_table.add_row("质量参数", self.quality_options)
        
        console.print(summary_table)
        
        # 显示文件列表（如果配置允许）
        if config_manager.get('ui.show_file_details', True):
            video_handler.show_files_table(self.video_files)
        
        return Confirm.ask("\n🚀 开始处理?", default=True)
    
    def process_files(self) -> None:
        """处理文件"""
        console.print("\n🎵 开始提取音频...", style="bold green")
        
        # 创建进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "提取音频中...",
                total=len(self.video_files)
            )
            
            # 批量处理
            if self.output_directory == "same_as_source":
                # 逐个处理，输出到源文件目录
                results = {}
                for video_file in self.video_files:
                    source_dir = Path(video_file).parent
                    output_filename = Path(video_file).stem + config_manager.get_audio_formats()[self.audio_format]['extension']
                    output_path = source_dir / output_filename
                    
                    success, error = ffmpeg_wrapper.extract_audio(
                        video_file,
                        str(output_path),
                        self.audio_format,
                        self.quality_options
                    )
                    
                    results[video_file] = (success, error)
                    progress.advance(task)
            else:
                # 批量处理到指定目录
                results = ffmpeg_wrapper.batch_extract_audio(
                    self.video_files,
                    self.output_directory,
                    self.audio_format,
                    self.quality_options,
                    progress,
                    task
                )
        
        # 显示处理结果
        self.show_results(results)
    
    def show_results(self, results: Dict[str, Tuple[bool, str]]) -> None:
        """显示处理结果"""
        console.print("\n📊 处理结果:", style="bold")
        
        success_count = sum(1 for success, _ in results.values() if success)
        total_count = len(results)
        
        # 结果摘要
        if success_count == total_count:
            console.print(f"✅ 全部成功! 共处理 {total_count} 个文件", style="bold green")
        else:
            console.print(f"⚠️  部分成功: {success_count}/{total_count} 个文件处理成功", style="yellow")
        
        # 详细结果表格
        if total_count <= 20 or not config_manager.get('ui.show_file_details', True):
            # 显示详细结果
            results_table = Table(title="详细结果")
            results_table.add_column("文件名", style="cyan")
            results_table.add_column("状态", style="white")
            results_table.add_column("说明", style="dim")
            
            for file_path, (success, error) in results.items():
                filename = Path(file_path).name
                if success:
                    results_table.add_row(filename, "✅ 成功", "")
                else:
                    results_table.add_row(filename, "❌ 失败", error[:50] + "..." if len(error) > 50 else error)
            
            console.print(results_table)
        
        # 失败文件列表
        failed_files = [(file_path, error) for file_path, (success, error) in results.items() if not success]
        if failed_files:
            console.print("\n❌ 失败的文件:", style="red")
            for file_path, error in failed_files:
                console.print(f"   • {Path(file_path).name}: {error}", style="dim red")
    
    def run(self) -> None:
        """运行交互式界面"""
        try:
            # 显示欢迎信息
            self.show_welcome()
            
            # 检查 FFmpeg
            if not self.check_ffmpeg():
                return
            
            # 获取视频文件
            self.video_files = self.get_video_files()
            if not self.video_files:
                console.print("❌ 没有可处理的视频文件", style="red")
                return
            
            # 选择音频格式
            self.audio_format, self.quality_options = self.select_audio_format()
            if not self.audio_format:
                return
            
            # 选择输出目录
            self.output_directory = self.select_output_directory()
            
            # 显示摘要并确认
            if config_manager.get('ui.confirm_before_start', True):
                if not self.show_processing_summary():
                    console.print("👋 用户取消操作", style="yellow")
                    return
            
            # 处理文件
            self.process_files()
            
            console.print("\n🎉 处理完成!", style="bold green")
            
        except KeyboardInterrupt:
            console.print("\n👋 用户中断操作", style="yellow")
        except Exception as e:
            console.print(f"\n❌ 发生错误: {e}", style="red")


def main():
    """主函数"""
    ui = InteractiveUI()
    ui.run()


if __name__ == "__main__":
    main()
