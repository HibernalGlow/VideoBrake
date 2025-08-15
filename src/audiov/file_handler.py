"""
文件处理模块
处理视频文件的扫描、验证和组织
"""

import os
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()

class VideoFileHandler:
    """视频文件处理器"""
    
    # 支持的视频文件扩展名
    SUPPORTED_VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', 
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts'
    }
    
    def __init__(self):
        """初始化视频文件处理器"""
        pass
    
    def is_video_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的视频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为支持的视频文件
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_VIDEO_EXTENSIONS
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """
        扫描目录中的视频文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归扫描子目录
            
        Returns:
            视频文件路径列表
        """
        video_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            console.print(f"❌ 目录不存在: {directory}", style="red")
            return video_files
        
        if not directory_path.is_dir():
            console.print(f"❌ 路径不是目录: {directory}", style="red")
            return video_files
        
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory_path.glob(pattern):
                if file_path.is_file() and self.is_video_file(str(file_path)):
                    video_files.append(str(file_path))
            
            video_files.sort()  # 按文件名排序
            
            console.print(f"📁 扫描完成，找到 {len(video_files)} 个视频文件", style="green")
            
        except Exception as e:
            console.print(f"❌ 扫描目录时发生错误: {e}", style="red")
        
        return video_files
    
    def validate_files(self, file_paths: List[str]) -> List[str]:
        """
        验证文件列表，移除不存在或不支持的文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            验证后的文件路径列表
        """
        valid_files = []
        invalid_files = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                invalid_files.append(f"{file_path} (文件不存在)")
                continue
            
            if not path.is_file():
                invalid_files.append(f"{file_path} (不是文件)")
                continue
            
            if not self.is_video_file(file_path):
                invalid_files.append(f"{file_path} (不支持的格式)")
                continue
            
            valid_files.append(file_path)
        
        # 报告验证结果
        if invalid_files:
            console.print(f"⚠️  发现 {len(invalid_files)} 个无效文件:", style="yellow")
            for invalid_file in invalid_files:
                console.print(f"   - {invalid_file}", style="dim yellow")
        
        if valid_files:
            console.print(f"✅ {len(valid_files)} 个文件验证通过", style="green")
        else:
            console.print("❌ 没有有效的视频文件", style="red")
        
        return valid_files
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件基本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            
            return {
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'directory': str(path.parent)
            }
        except Exception as e:
            console.print(f"❌ 获取文件信息失败 ({file_path}): {e}", style="red")
            return None
    
    def show_files_table(self, file_paths: List[str]) -> None:
        """
        以表格形式显示文件列表
        
        Args:
            file_paths: 文件路径列表
        """
        if not file_paths:
            console.print("📋 没有文件可显示", style="yellow")
            return
        
        table = Table(title="📹 待处理的视频文件")
        table.add_column("序号", style="cyan", no_wrap=True)
        table.add_column("文件名", style="magenta")
        table.add_column("大小", style="green", justify="right")
        table.add_column("目录", style="blue")
        
        for i, file_path in enumerate(file_paths, 1):
            info = self.get_file_info(file_path)
            if info:
                table.add_row(
                    str(i),
                    info['name'],
                    f"{info['size_mb']} MB",
                    info['directory']
                )
            else:
                table.add_row(
                    str(i),
                    Path(file_path).name,
                    "未知",
                    str(Path(file_path).parent)
                )
        
        console.print(table)
    
    def get_supported_extensions(self) -> Set[str]:
        """
        获取支持的视频文件扩展名
        
        Returns:
            支持的扩展名集合
        """
        return self.SUPPORTED_VIDEO_EXTENSIONS.copy()
    
    def filter_by_extension(self, file_paths: List[str], extensions: Set[str]) -> List[str]:
        """
        根据扩展名过滤文件
        
        Args:
            file_paths: 文件路径列表
            extensions: 允许的扩展名集合
            
        Returns:
            过滤后的文件路径列表
        """
        filtered_files = []
        
        for file_path in file_paths:
            if Path(file_path).suffix.lower() in extensions:
                filtered_files.append(file_path)
        
        return filtered_files


# 全局视频文件处理器实例
video_handler = VideoFileHandler()
