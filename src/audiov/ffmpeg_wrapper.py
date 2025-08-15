"""
FFmpeg 封装模块
提供 FFmpeg 音频提取功能的封装
"""

import subprocess
import os
import shlex
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from rich.console import Console
from rich.progress import Progress, TaskID

from .config import config_manager

console = Console()

class FFmpegWrapper:
    """FFmpeg 包装器类"""
    
    def __init__(self):
        """初始化 FFmpeg 包装器"""
        self.ffmpeg_path = config_manager.get_ffmpeg_path()
        self.timeout = config_manager.get('ffmpeg.timeout', 300)
    
    def check_ffmpeg_available(self) -> bool:
        """
        检查 FFmpeg 是否可用
        
        Returns:
            FFmpeg 是否可用
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典，包含时长、音频轨道等信息
        """
        try:
            cmd = [
                self.ffmpeg_path, '-i', video_path,
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            # FFmpeg 的信息输出在 stderr 中
            output = result.stderr
            
            info = {
                'has_audio': 'Audio:' in output,
                'duration': self._parse_duration(output),
                'audio_streams': self._parse_audio_streams(output)
            }
            
            return info
        except Exception as e:
            console.print(f"❌ 获取视频信息失败 ({video_path}): {e}", style="red")
            return None
    
    def _parse_duration(self, ffmpeg_output: str) -> Optional[str]:
        """
        从 FFmpeg 输出中解析视频时长
        
        Args:
            ffmpeg_output: FFmpeg 输出内容
            
        Returns:
            时长字符串 (HH:MM:SS.ms 格式)
        """
        import re
        duration_pattern = r'Duration: (\d{2}:\d{2}:\d{2}\.\d{2})'
        match = re.search(duration_pattern, ffmpeg_output)
        return match.group(1) if match else None
    
    def _parse_audio_streams(self, ffmpeg_output: str) -> List[Dict[str, str]]:
        """
        从 FFmpeg 输出中解析音频流信息
        
        Args:
            ffmpeg_output: FFmpeg 输出内容
            
        Returns:
            音频流信息列表
        """
        import re
        audio_streams = []
        
        # 查找音频流信息
        audio_pattern = r'Stream #(\d+:\d+).*?: Audio: (\w+).*?, (\d+) Hz.*?, (\w+)'
        matches = re.findall(audio_pattern, ffmpeg_output)
        
        for match in matches:
            stream_id, codec, sample_rate, channels = match
            audio_streams.append({
                'stream_id': stream_id,
                'codec': codec,
                'sample_rate': sample_rate,
                'channels': channels
            })
        
        return audio_streams
    
    def extract_audio(
        self,
        video_path: str,
        output_path: str,
        audio_format: str = 'mp3',
        quality_options: str = '',
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        从视频文件提取音频
        
        Args:
            video_path: 输入视频文件路径
            output_path: 输出音频文件路径
            audio_format: 音频格式 (mp3, aac, wav, flac, m4a)
            quality_options: 质量选项字符串
            progress_callback: 进度回调函数
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 获取格式配置
            formats = config_manager.get_audio_formats()
            if audio_format not in formats:
                return False, f"不支持的音频格式: {audio_format}"
            
            format_config = formats[audio_format]
            codec = format_config['codec']
            quality = quality_options or format_config.get('quality', '')
            
            # 检查是否为极速模式（直接复制音频流）
            is_fast_mode = (audio_format == 'copy' or codec == 'copy')
            
            if is_fast_mode:
                # 极速模式：直接复制音频流
                console.print("⚡ 极速模式：直接复制音频流", style="bold yellow")
                
                # 如果是自动扩展名，检测原始音频格式
                if format_config.get('extension') == 'auto':
                    detected_ext = self.get_audio_extension(video_path)
                    # 更新输出路径的扩展名
                    output_path = str(Path(output_path).with_suffix(detected_ext))
                    console.print(f"🔍 检测到音频格式: {detected_ext}", style="dim")
                
                cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-vn',  # 不包含视频
                    '-acodec', 'copy',  # 直接复制音频流
                    '-hide_banner',
                    '-loglevel', 'error'
                ]
            else:
                # 普通模式：重新编码
                cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-vn',  # 不包含视频
                    '-acodec', codec,
                    '-hide_banner',
                    '-loglevel', 'error'
                ]
                
                # 添加质量参数
                if quality:
                    cmd.extend(shlex.split(quality))
            
            # 添加输出文件
            if config_manager.get('output.overwrite_existing', False):
                cmd.append('-y')  # 覆盖现有文件
            else:
                cmd.append('-n')  # 不覆盖现有文件
            
            cmd.append(output_path)
            
            console.print(f"🎵 开始提取音频: {Path(video_path).name}", style="cyan")
            if is_fast_mode:
                console.print("⚡ 极速模式 - 无需转码", style="bold green")
            console.print(f"📁 输出路径: {output_path}", style="dim")
            
            # 使用更安全的方式执行命令
            try:
                # 在 Windows 上设置正确的编码
                if os.name == 'nt':  # Windows
                    # 使用 subprocess.STARTUPINFO 来处理 Windows 编码问题
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        encoding='utf-8',
                        errors='ignore'
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',
                        errors='ignore'
                    )
                
                # 等待完成
                stdout, stderr = process.communicate(timeout=self.timeout)
                
                if process.returncode == 0:
                    console.print(f"✅ 音频提取成功: {Path(output_path).name}", style="green")
                    return True, ""
                else:
                    # 清理错误信息
                    error_msg = self._clean_error_message(stderr or stdout or "未知错误")
                    console.print(f"❌ 音频提取失败: {error_msg}", style="red")
                    return False, error_msg
                    
            except subprocess.TimeoutExpired:
                process.kill()
                error_msg = f"提取超时 (>{self.timeout}秒)"
                console.print(f"⏰ {error_msg}", style="yellow")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"提取过程中发生错误: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            return False, error_msg
    
    def _clean_error_message(self, error_text: str) -> str:
        """
        清理错误信息，提取有用的部分
        
        Args:
            error_text: 原始错误文本
            
        Returns:
            清理后的错误信息
        """
        if not error_text:
            return "未知错误"
        
        # 常见错误信息的简化
        error_patterns = [
            (r"No such file or directory", "文件不存在"),
            (r"Permission denied", "权限不足"),
            (r"Invalid data", "无效的文件数据"),
            (r"Could not find codec", "不支持的编码格式"),
            (r"File exists", "文件已存在"),
            (r"No space left", "磁盘空间不足"),
        ]
        
        # 检查常见错误模式
        import re
        for pattern, message in error_patterns:
            if re.search(pattern, error_text, re.IGNORECASE):
                return message
        
        # 提取最后一行作为错误信息
        lines = error_text.strip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            if last_line and len(last_line) < 200:
                return last_line
        
        return "处理过程中发生错误"
    
    def batch_extract_audio(
        self,
        video_files: List[str],
        output_directory: str,
        audio_format: str = 'mp3',
        quality_options: str = '',
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> Dict[str, Tuple[bool, str]]:
        """
        批量提取音频
        
        Args:
            video_files: 视频文件路径列表
            output_directory: 输出目录
            audio_format: 音频格式
            quality_options: 质量选项
            progress: Rich 进度条对象
            task_id: 进度条任务 ID
            
        Returns:
            处理结果字典 {文件路径: (是否成功, 错误信息)}
        """
        results = {}
        
        # 确保输出目录存在
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        # 获取音频格式扩展名
        formats = config_manager.get_audio_formats()
        extension = formats.get(audio_format, {}).get('extension', '.mp3')
        is_fast_mode = (audio_format == 'copy' or formats.get(audio_format, {}).get('codec') == 'copy')
        
        total_files = len(video_files)
        
        for i, video_path in enumerate(video_files):
            video_file = Path(video_path)
            
            # 生成输出文件路径
            if is_fast_mode and extension == 'auto':
                # 极速模式且自动扩展名，检测原始音频格式
                detected_ext = self.get_audio_extension(video_path)
                output_filename = video_file.stem + detected_ext
            else:
                output_filename = video_file.stem + extension
            
            output_path = Path(output_directory) / output_filename
            
            # 提取音频
            success, error = self.extract_audio(
                video_path,
                str(output_path),
                audio_format,
                quality_options
            )
            
            results[video_path] = (success, error)
            
            # 更新进度
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
        
        return results
    
    def get_audio_extension(self, video_path: str) -> str:
        """
        获取视频文件中音频流的格式扩展名
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            音频扩展名 (如 .aac, .mp3 等)
        """
        try:
            cmd = [
                self.ffmpeg_path, '-i', video_path,
                '-f', 'null', '-',
                '-hide_banner', '-loglevel', 'error'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 从 stderr 中解析音频编码格式
            output = result.stderr
            
            # 常见音频格式映射
            codec_extensions = {
                'aac': '.aac',
                'mp3': '.mp3',
                'vorbis': '.ogg',
                'opus': '.opus',
                'flac': '.flac',
                'ac-3': '.ac3',
                'dts': '.dts',
                'pcm': '.wav'
            }
            
            # 搜索音频编码格式
            import re
            audio_pattern = r'Audio: (\w+)'
            match = re.search(audio_pattern, output)
            
            if match:
                codec = match.group(1).lower()
                return codec_extensions.get(codec, '.aac')  # 默认返回 .aac
            
            return '.aac'  # 如果无法检测，默认返回 .aac
            
        except Exception as e:
            console.print(f"⚠️ 无法检测音频格式，使用默认: {e}", style="yellow")
            return '.aac'


# 全局 FFmpeg 包装器实例
ffmpeg_wrapper = FFmpegWrapper()
