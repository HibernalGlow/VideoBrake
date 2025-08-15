"""
视频分析器模块

封装视频信息提取、码率分析等功能
"""

import os
import json
import cv2
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Set
from datetime import datetime
from collections import Counter

# 导入Rich库
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
from rich.progress import TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

# 导入通用工具
from bitv.common_utils import (
    VideoInfo, ProcessResult, create_bitrate_levels, 
    get_bitrate_level, is_video_file, VIDEO_FILE_TYPES
)

console = Console()


class VideoAnalyzer:
    """视频分析器类，封装视频信息提取、码率分析等功能"""
    
    def __init__(self, bitrate_step: float = 5, max_steps: int = 10):
        """
        初始化视频分析器
        
        Args:
            bitrate_step: 码率等级步长（Mbps）
            max_steps: 最大等级数量
        """
        self.bitrate_step = bitrate_step
        self.max_steps = max_steps
        self.bitrate_levels = create_bitrate_levels(bitrate_step, max_steps)
    
    def analyze_video(self, video_path: str) -> Optional[VideoInfo]:
        """
        分析单个视频文件，提取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Optional[VideoInfo]: 视频信息，如果分析失败则返回None
        """
        try:
            if not os.path.exists(video_path):
                logging.error(f"视频文件不存在: {video_path}")
                return None
            
            if not is_video_file(video_path):
                logging.error(f"不是有效的视频文件: {video_path}")
                return None
            
            # 获取文件大小
            file_size = os.path.getsize(video_path)
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logging.error(f"无法打开视频文件: {video_path}")
                return None
                
            # 获取视频基本信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算时长（秒）
            duration = total_frames / fps if fps > 0 else 0
            
            # 计算码率 (bits/s)
            bitrate = (file_size * 8) / duration if duration > 0 else 0
            
            # 释放视频对象
            cap.release()
            
            # 创建VideoInfo对象
            video_info = VideoInfo(
                path=video_path,
                duration=duration,
                bitrate=bitrate,
                width=width,
                height=height,
                fps=fps,
                size_bytes=file_size
            )
            
            return video_info
            
        except Exception as e:
            logging.error(f"分析视频时出错: {video_path}, 错误: {str(e)}")
            return None
    
    def estimate_video_bitrate(self, video_path: str) -> float:
        """
        估算视频码率（bits/s），使用文件大小作为参考
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 估算的码率
        """
        try:
            # 获取文件大小（字节）
            file_size = os.path.getsize(video_path)
            # 假设平均1分钟视频，转换为比特率（bits/s）
            # 文件大小(bytes) * 8(bits/byte) / 60(s) 
            return (file_size * 8) / 60
        except Exception as e:
            logging.error(f"估算视频码率时出错: {video_path}, 错误: {str(e)}")
            return 0
    
    def get_video_bitrate_level(self, video_info: VideoInfo) -> str:
        """
        根据视频信息获取码率等级
        
        Args:
            video_info: 视频信息对象
            
        Returns:
            str: 码率等级名称
        """
        return get_bitrate_level(video_info.bitrate, self.bitrate_levels)
    
    def find_videos_in_folder(self, folder_path: str, recursive: bool = True) -> List[str]:
        """
        在指定文件夹中查找视频文件
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归搜索子文件夹
            
        Returns:
            List[str]: 视频文件路径列表
        """
        result = []
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            logging.error(f"文件夹不存在或不是目录: {folder_path}")
            return result
        
        try:
            if recursive:
                # 递归搜索
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if is_video_file(file_path):
                            result.append(file_path)
            else:
                # 只搜索当前文件夹
                for item in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, item)
                    if os.path.isfile(file_path) and is_video_file(file_path):
                        result.append(file_path)
                        
            return result
        
        except Exception as e:
            logging.error(f"搜索视频文件时出错: {folder_path}, 错误: {str(e)}")
            return result
    
    def analyze_folder(self, folder_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        分析文件夹中的视频文件，生成分析报告
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归搜索子文件夹
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        result = {
            "folder_path": folder_path,
            "timestamp": datetime.now().isoformat(),
            "videos": [],
            "stats": {
                "total_videos": 0,
                "total_size_bytes": 0,
                "total_duration": 0,
                "bitrate_distribution": {}
            }
        }
        
        # 查找视频文件
        console.print(f"[blue]正在搜索视频文件...[/blue]")
        video_files = self.find_videos_in_folder(folder_path, recursive)
        
        if not video_files:
            console.print(f"[yellow]未找到视频文件[/yellow]")
            return result
        
        console.print(f"[green]找到 {len(video_files)} 个视频文件[/green]")
        
        # 分析视频文件
        bitrate_counter = Counter()
        total_size = 0
        total_duration = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]分析视频文件...[/cyan]", total=len(video_files))
            
            for video_path in video_files:
                # 更新任务描述
                progress.update(task, description=f"[cyan]分析视频: {os.path.basename(video_path)}[/cyan]")
                
                # 分析视频
                video_info = self.analyze_video(video_path)
                
                if video_info:
                    # 获取码率等级
                    bitrate_level = self.get_video_bitrate_level(video_info)
                    
                    # 更新统计信息
                    bitrate_counter[bitrate_level] += 1
                    total_size += video_info.size_bytes
                    total_duration += video_info.duration
                    
                    # 添加到结果
                    result["videos"].append({
                        "path": video_path,
                        "info": video_info.to_dict(),
                        "bitrate_level": bitrate_level
                    })
                
                # 更新进度
                progress.update(task, advance=1)
        
        # 更新统计信息
        result["stats"]["total_videos"] = len(result["videos"])
        result["stats"]["total_size_bytes"] = total_size
        result["stats"]["total_duration"] = total_duration
        result["stats"]["bitrate_distribution"] = {
            level: count for level, count in sorted(bitrate_counter.items())
        }
        
        # 显示分析结果
        self.display_analysis_results(result)
        
        return result
    
    def display_analysis_results(self, result: Dict[str, Any]) -> None:
        """
        显示分析结果
        
        Args:
            result: 分析结果
        """
        console.print(Panel.fit(
            f"[bold cyan]视频分析结果[/bold cyan]", 
            subtitle=f"文件夹: {result['folder_path']}"
        ))
        
        # 创建统计表格
        stats = result["stats"]
        table = Table(title="总体统计")
        table.add_column("项目", style="cyan")
        table.add_column("数值", style="green")
        
        table.add_row("视频文件数量", f"{stats['total_videos']}")
        table.add_row("总大小", f"{stats['total_size_bytes'] / (1024 * 1024):.2f} MB")
        table.add_row("总时长", f"{stats['total_duration'] / 60:.2f} 分钟")
        
        console.print(table)
        
        # 显示码率分布
        if stats["bitrate_distribution"]:
            bitrate_table = Table(title="码率分布")
            bitrate_table.add_column("码率等级", style="cyan")
            bitrate_table.add_column("文件数量", style="green")
            bitrate_table.add_column("百分比", style="yellow")
            
            total_videos = stats["total_videos"]
            for level, count in stats["bitrate_distribution"].items():
                percentage = (count / total_videos) * 100 if total_videos > 0 else 0
                bitrate_table.add_row(level, f"{count}", f"{percentage:.1f}%")
            
            console.print(bitrate_table)
    
    def generate_json_report(self, result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        生成JSON分析报告
        
        Args:
            result: 分析结果
            output_path: 输出文件路径，如果为None则使用默认路径
            
        Returns:
            str: 生成的报告文件路径
        """
        if output_path is None:
            folder_path = result["folder_path"]
            folder_name = os.path.basename(folder_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(folder_path, f"{folder_name}_analysis_{timestamp}.json")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]分析报告已保存: {output_path}[/green]")
        return output_path