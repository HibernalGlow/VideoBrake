"""
VideoBrake - 视频处理工具集

提供统一接口调用各个子包功能
"""

__version__ = '0.2.0'

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

# 导入子包，提供直接访问入口
import bitscaculate
import formatfliter

# 导入主要类和函数
from bitscaculate.video_analyzer import VideoAnalyzer
from bitscaculate.video_processor import VideoProcessor
from formatfliter.__main__ import FormatFilter, process_videos, find_video_files

# 从内部模块导入需要的功能
from bitscaculate.common_utils import VideoInfo, VIDEO_FILE_TYPES, get_bitrate_level
from formatfliter.__main__ import add_nov_extension, remove_nov_extension, process_video_files

# 确保日志目录存在
log_dir = Path(__file__).parent.parent.parent / "logs" / "videobrake"
log_dir.mkdir(parents=True, exist_ok=True)

# 统一接口类
class VideoBrake:
    """VideoBrake统一接口，用于集中调用各子包功能"""
    
    def __init__(self, bitrate_step: float = 1.0, max_steps: int = 10):
        """初始化VideoBrake接口
        
        参数:
            bitrate_step: 码率分级步长（Mbps）
            max_steps: 最大码率分级数
        """
        self.bitscaculate = bitscaculate  # 码率计算模块
        self.formatfliter = formatfliter  # 格式过滤模块
        self.bitrate_step = bitrate_step
        self.max_steps = max_steps
    
    def analyze_video(self, file_path: str) -> Optional[VideoInfo]:
        """分析单个视频文件
        
        参数:
            file_path: 视频文件路径
            
        返回:
            VideoInfo 对象或 None（如果分析失败）
        """
        # 使用VideoAnalyzer对象分析视频
        analyzer = VideoAnalyzer(bitrate_step=self.bitrate_step, max_steps=self.max_steps)
        return analyzer.analyze_video(file_path)
    
    def analyze_folder(self, folder_path: str, recursive: bool = True) -> Dict[str, List[VideoInfo]]:
        """分析文件夹中的视频文件
        
        参数:
            folder_path: 文件夹路径
            recursive: 是否递归搜索子文件夹
            
        返回:
            按码率分组的视频信息字典 {档位: [视频信息列表]}
        """
        # 创建分析器对象并调用其analyze_folder方法
        analyzer = VideoAnalyzer(bitrate_step=self.bitrate_step, max_steps=self.max_steps)
        return analyzer.analyze_folder(folder_path, recursive=recursive)
        
    def generate_json_report(self, analysis_result: Dict[str, List[VideoInfo]]) -> str:
        """从分析结果生成 JSON 报告
        
        参数:
            analysis_result: 分析结果字典
            
        返回:
            JSON 报告文件路径
        """
        # 转换为可序列化的字典
        report_data = {
            "metadata": {
                "bitrate_step": self.bitrate_step,
                "max_steps": self.max_steps,
                "total_videos": sum(len(videos) for videos in analysis_result.values())
            },
            "groups": {}
        }
        
        for step, videos in analysis_result.items():
            report_data["groups"][step] = [
                {
                    "filename": video.filename,
                    "path": video.path,
                    "bitrate_mbps": video.bitrate_mbps,
                    "size_mb": video.size_mb,
                    "duration": video.duration,
                    "width": video.width,
                    "height": video.height,
                    "fps": video.fps
                }
                for video in videos
            ]
            
        # 保存到文件
        report_path = log_dir / f"video_analysis_{Path.cwd().name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        return str(report_path)
        
    def classify_videos(self, source_dir: str, target_dir: str = None, is_move: bool = False, recursive: bool = True) -> None:
        """按码率分类视频文件
        
        参数:
            source_dir: 源文件夹路径
            target_dir: 目标文件夹路径
            is_move: 是否移动文件（True）或复制（False）
            recursive: 是否递归搜索子文件夹
        """
        # 如果未指定目标目录，使用源目录
        if target_dir is None:
            target_dir = source_dir
            
        # 分析文件夹
        analysis_result = self.analyze_folder(source_dir, recursive=recursive)
        
        # 创建目标目录（如果不存在）
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # 按码率分组移动/复制文件
        for step, videos in analysis_result.items():
            group_dir = Path(target_dir) / step
            group_dir.mkdir(exist_ok=True)
            
            for video in videos:
                source_file = Path(video.path)
                target_file = group_dir / source_file.name
                
                if is_move:
                    shutil.move(str(source_file), str(target_file))
                else:
                    shutil.copy2(str(source_file), str(target_file))
                    
    def classify_from_report(self, report_path: str, is_move: bool = False) -> None:
        """根据报告文件对视频进行分类
        
        参数:
            report_path: JSON报告文件路径
            is_move: 是否移动文件（True）或复制（False）
        """
        # 加载报告文件
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
            
        # 获取报告所在目录作为基准目录
        base_dir = Path(report_path).parent
        
        # 根据报告进行分类
        for step, videos in report_data["groups"].items():
            group_dir = base_dir / step
            group_dir.mkdir(exist_ok=True)
            
            for video in videos:
                source_file = Path(video["path"])
                if not source_file.exists():
                    print(f"文件不存在: {source_file}")
                    continue
                    
                target_file = group_dir / source_file.name
                
                if is_move:
                    shutil.move(str(source_file), str(target_file))
                else:
                    shutil.copy2(str(source_file), str(target_file))
                    
    def process_videos_in_dir(self, directory: str) -> None:
        """处理目录中的视频文件（添加/移除.nov后缀和检查重复项）
        
        参数:
            directory: 目录路径
        """
        process_video_files(directory)
        
    def add_nov_extension(self, file_path: str) -> Tuple[bool, str]:
        """添加.nov后缀到文件
        
        参数:
            file_path: 文件路径
            
        返回:
            (成功标志, 结果消息)
        """
        return add_nov_extension(file_path)
        
    def remove_nov_extension(self, file_path: str) -> Tuple[bool, str]:
        """移除文件的.nov后缀
        
        参数:
            file_path: 文件路径
            
        返回:
            (成功标志, 结果消息)
        """
        return remove_nov_extension(file_path)
        
    def check_duplicates(self, folder_path: str, nov_files: List[str], 
                        normal_files: List[str], hb_files: List[str]) -> None:
        """检查重复的视频文件（带#hb标记的文件）
        
        参数:
            folder_path: 文件夹路径
            nov_files: .nov文件列表
            normal_files: 普通视频文件列表
            hb_files: 带#hb标记的文件列表
        """
        # 创建集合以便快速查找
        nov_names = {Path(f).stem for f in nov_files}
        normal_names = {Path(f).stem for f in normal_files}
        
        # 检查每个hb文件是否有对应的普通文件
        for hb_file in hb_files:
            hb_path = Path(hb_file)
            base_name = hb_path.stem
            
            # 移除#hb部分
            if "#hb" in base_name:
                clean_name = base_name.split("#hb")[0]
                
                # 检查是否有对应的普通文件或.nov文件
                if clean_name in normal_names or clean_name in nov_names:
                    print(f"发现重复: {hb_file}")
                    print(f"  对应的原始文件存在")
