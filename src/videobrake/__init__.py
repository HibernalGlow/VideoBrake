"""
VideoBrake - 视频处理工具集

提供统一接口调用各个子包功能
"""

__version__ = '0.1.0'

# 导入子包，提供直接访问入口
import bitscaculate
import formatfliter

# 提供子包的主要类/函数的直接访问
from bitscaculate.video_analyzer import VideoAnalyzer
from bitscaculate.video_processor import VideoProcessor
from formatfliter.core import FormatFilter, process_videos

# 简化的统一接口类
class VideoBrake:
    """VideoBrake统一接口，用于集中调用各子包功能"""
    
    def __init__(self):
        """初始化VideoBrake接口"""
        self.bitscaculate = bitscaculate  # 码率计算模块
        self.formatfliter = formatfliter  # 格式过滤模块

