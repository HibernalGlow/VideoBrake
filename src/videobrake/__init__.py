"""
VideoBrake - 视频处理工具集

提供统一接口调用各个子包功能
"""

__version__ = '0.1.0'

# 导入码率计算模块
from bitscaculate.video_analyzer import VideoAnalyzer
from bitscaculate.video_processor import VideoProcessor
from bitscaculate.common_utils import (
    VideoInfo, ProcessResult, ProcessStats,
    create_bitrate_levels, get_bitrate_level, ensure_dir_exists,
    get_relative_path, is_video_file, VIDEO_FILE_TYPES
)

# 导入格式过滤模块
from formatfliter.core import (
    FormatFilter, process_videos, process_single_file,
    check_and_save_duplicates, find_video_files, normalize_path
)

# 统一接口类
class VideoBrake:
    """VideoBrake统一接口，用于集中调用各子包功能"""
    
    def __init__(self, bitrate_step: float = 5, max_steps: int = 10):
        """
        初始化VideoBrake接口
        
        Args:
            bitrate_step: 码率等级步长（Mbps）
            max_steps: 最大等级数量
        """
        self.analyzer = VideoAnalyzer(bitrate_step, max_steps)
        self.processor = VideoProcessor(self.analyzer)
        self.format_filter = FormatFilter()
        
    # === 码率分析与分类功能 ===
    
    def analyze_video(self, video_path):
        """分析单个视频文件"""
        return self.analyzer.analyze_video(video_path)
        
    def analyze_folder(self, folder_path, recursive=True):
        """分析文件夹中的所有视频"""
        return self.analyzer.analyze_folder(folder_path, recursive)
        
    def generate_json_report(self, result, output_path=None):
        """生成JSON分析报告"""
        return self.analyzer.generate_json_report(result, output_path)
    
    def classify_videos(self, source_dir, target_dir=None, is_move=False, recursive=True):
        """根据码率对视频进行分类"""
        return self.processor.classify_videos_by_bitrate(
            source_dir, target_dir, is_move, recursive
        )
    
    def classify_from_report(self, report_path, is_move=False):
        """根据JSON报告对视频进行分类"""
        return self.processor.classify_from_json_report(report_path, is_move)
        
    # === 格式过滤功能 ===
    
    def process_videos_in_dir(self, directory):
        """处理目录中的视频文件(添加/移除.nov后缀和检查重复项)"""
        return process_videos(directory)
    
    def add_nov_extension(self, file_path):
        """添加.nov后缀到视频文件"""
        return process_single_file(file_path, add_nov=True)
    
    def remove_nov_extension(self, file_path):
        """移除视频文件的.nov后缀"""
        return process_single_file(file_path, add_nov=False)
    
    def check_duplicates(self, directory):
        """检查目录中的重复视频文件"""
        nov_files, normal_files, hb_files = find_video_files(directory)
        return check_and_save_duplicates(directory, nov_files, normal_files, hb_files)

