"""
通用工具模块

包含视频文件类型定义、结果格式化和其他共享功能
"""

import os
import json
import cv2
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from datetime import datetime, timedelta

# 视频文件类型
VIDEO_FILE_TYPES = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", 
    ".webm", ".m4v", ".mpg", ".mpeg", ".nov"
}

# 码率等级常量 - 基础单位为 Mbps (百万比特/秒)
DEFAULT_BITRATE_STEP = 5  # 默认每档5MB
DEFAULT_BITRATE_LEVELS = 10  # 默认10个等级

class VideoInfo:
    """视频信息类，存储视频的基本信息"""
    
    def __init__(self, 
                 path: str, 
                 duration: float = 0.0, 
                 bitrate: float = 0.0, 
                 width: int = 0, 
                 height: int = 0,
                 fps: float = 0.0,
                 size_bytes: int = 0):
        self.path = path
        self.filename = os.path.basename(path)
        self.duration = duration  # 秒
        self.bitrate = bitrate  # bits/s
        self.width = width
        self.height = height
        self.fps = fps
        self.size_bytes = size_bytes
    
    @property
    def bitrate_mbps(self) -> float:
        """返回以Mbps为单位的码率"""
        return self.bitrate / 1_000_000 if self.bitrate > 0 else 0
    
    @property
    def size_mb(self) -> float:
        """返回以MB为单位的文件大小"""
        return self.size_bytes / (1024 * 1024) if self.size_bytes > 0 else 0
    
    @property
    def duration_formatted(self) -> str:
        """以时:分:秒格式返回视频时长"""
        if self.duration <= 0:
            return "00:00:00"
        
        td = timedelta(seconds=self.duration)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 如果时长超过1天，添加天数
        if td.days > 0:
            return f"{td.days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def size_formatted(self) -> str:
        """以人类可读格式返回文件大小"""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.2f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{self.size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    @property
    def bitrate_formatted(self) -> str:
        """以人类可读格式返回码率"""
        if self.bitrate < 1000:
            return f"{self.bitrate:.2f} bps"
        elif self.bitrate < 1000000:
            return f"{self.bitrate / 1000:.2f} Kbps"
        else:
            return f"{self.bitrate / 1000000:.2f} Mbps"
    
    @property
    def resolution(self) -> str:
        """返回分辨率描述"""
        if self.width == 3840 and self.height == 2160:
            return f"{self.width}x{self.height} (4K UHD)"
        elif self.width == 1920 and self.height == 1080:
            return f"{self.width}x{self.height} (1080p Full HD)"
        elif self.width == 1280 and self.height == 720:
            return f"{self.width}x{self.height} (720p HD)"
        else:
            return f"{self.width}x{self.height}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示，便于JSON序列化"""
        return {
            # "path": self.path,
            "filename": self.filename,
            # "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            # "bitrate": self.bitrate,
            "bitrate_mbps": round(self.bitrate_mbps, 0),
            "bitrate_formatted": self.bitrate_formatted,
            "width": self.width,
            "height": self.height,
            "resolution": self.resolution,
            "fps": round(self.fps, 1),
            # "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 1),
            # "size_formatted": self.size_formatted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoInfo':
        """从字典创建VideoInfo实例"""
        return cls(
            path=data.get("path", ""),
            duration=data.get("duration", 0.0),
            bitrate=data.get("bitrate", 0.0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            fps=data.get("fps", 0.0),
            size_bytes=data.get("size_bytes", 0)
        )


class ProcessResult:
    """处理结果类，记录处理操作的结果"""
    
    def __init__(self, 
                 success: bool, 
                 source_path: str = "", 
                 target_path: str = "",
                 video_info: Optional[VideoInfo] = None,
                 bitrate_level: str = "",
                 error_message: str = ""):
        self.success = success
        self.source_path = source_path
        self.target_path = target_path
        self.video_info = video_info
        self.bitrate_level = bitrate_level
        self.error_message = error_message
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示，便于JSON序列化"""
        result = {
            "success": self.success,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "bitrate_level": self.bitrate_level,
            "timestamp": self.timestamp
        }
        
        if self.video_info:
            result["video_info"] = self.video_info.to_dict()
        
        if self.error_message:
            result["error_message"] = self.error_message
            
        return result


class ProcessStats:
    """处理统计信息类"""
    
    def __init__(self):
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_size_bytes = 0
        self.total_duration = 0.0
        self.results_by_level: Dict[str, List[ProcessResult]] = {}
    
    def add_result(self, result: ProcessResult):
        """添加一个处理结果到统计信息中"""
        if result.success:
            self.successful_operations += 1
            if result.video_info:
                self.total_size_bytes += result.video_info.size_bytes
                self.total_duration += result.video_info.duration
                
            # 按码率等级分组
            if result.bitrate_level:
                if result.bitrate_level not in self.results_by_level:
                    self.results_by_level[result.bitrate_level] = []
                self.results_by_level[result.bitrate_level].append(result)
        else:
            self.failed_operations += 1
    
    def get_summary(self) -> str:
        """获取统计摘要"""
        total_operations = self.successful_operations + self.failed_operations
        if total_operations == 0:
            return "没有进行任何操作"
        
        success_rate = (self.successful_operations / total_operations) * 100
        total_size_mb = self.total_size_bytes / (1024 * 1024)
        total_hours = self.total_duration / 3600
        
        summary = (
            f"总计: {total_operations}个文件, 成功: {self.successful_operations}, "
            f"失败: {self.failed_operations}, 成功率: {success_rate:.1f}%\n"
            f"总大小: {total_size_mb:.2f}MB, 总时长: {total_hours:.2f}小时"
        )
        
        # 添加码率等级统计
        if self.results_by_level:
            summary += "\n\n码率等级分布:\n"
            for level, results in sorted(self.results_by_level.items()):
                level_size_mb = sum(r.video_info.size_bytes for r in results if r.video_info) / (1024 * 1024)
                summary += f"- {level}: {len(results)}个文件, {level_size_mb:.2f}MB\n"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示，便于JSON序列化"""
        return {
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "total_size_bytes": self.total_size_bytes,
            "total_duration": self.total_duration,
            "results_by_level": {
                level: [r.to_dict() for r in results]
                for level, results in self.results_by_level.items()
            }
        }


def create_bitrate_levels(step_mb: float = DEFAULT_BITRATE_STEP, 
                         max_steps: int = DEFAULT_BITRATE_LEVELS) -> Dict[str, float]:
    """
    创建码率等级字典
    
    Args:
        step_mb: 每档位的大小（MB）
        max_steps: 最大档位数量
        
    Returns:
        Dict[str, float]: 码率等级字典，键为等级名称，值为码率阈值（bits/s）
    """
    levels = {}
    # 计算需要的位数
    digits = len(str(max_steps * step_mb))
    
    for i in range(1, max_steps + 1):
        threshold = i * step_mb * 1000000  # 转换为 bits/s
        # 使用 str(i*step_mb).zfill() 补零
        level_name = str(int(i*step_mb)).zfill(digits) + "MB"
        levels[level_name] = threshold
    
    # 添加最后一个无限大的档位
    levels["超大文件"] = float('inf')
    return levels


def get_bitrate_level(bitrate: float, levels: Dict[str, float]) -> str:
    """
    根据码率判断所属等级
    
    Args:
        bitrate: 码率（bits/s）
        levels: 码率等级字典
    
    Returns:
        str: 码率等级名称
    """
    for level_name, threshold in sorted(levels.items(), key=lambda x: x[1]):
        if bitrate <= threshold:
            return level_name
    return list(levels.keys())[-1]  # 返回最后一个等级


def is_video_file(file_path: str) -> bool:
    """
    检查文件是否为视频文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 是否为视频文件
    """
    ext = os.path.splitext(file_path.lower())[1]
    return ext in VIDEO_FILE_TYPES


def ensure_dir_exists(path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


def get_relative_path(path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        path: 完整路径
        base_path: 基准路径
    
    Returns:
        str: 相对路径
    """
    return os.path.relpath(path, base_path)