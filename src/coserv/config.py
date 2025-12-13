"""
配置文件
存储所有可调参数和系统设置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """系统配置类"""
    
    # ==================== API 配置 ====================
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-1.5-flash"
    
    # ==================== 视频处理配置 ====================
    # 场景检测阈值（越低越敏感，检测到更多场景切换）
    SCENE_THRESHOLD = 27.0
    
    # 每个视频最多提取的帧数
    MAX_FRAMES_PER_VIDEO = 10
    
    # 最小场景长度（秒）- 避免太短的场景
    MIN_SCENE_LENGTH = 2.0
    
    # ==================== 人脸检测配置 ====================
    # 人脸检测置信度阈值
    FACE_DETECTION_CONFIDENCE = 0.5
    
    # 最小人脸大小（相对于图像宽度的比例）
    MIN_FACE_SIZE_RATIO = 0.1
    
    # ==================== 图像去重配置 ====================
    # 感知哈希差异阈值（越小越严格）
    HASH_DIFF_THRESHOLD = 10
    
    # ==================== 文件组织配置 ====================
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}
    
    # 未识别视频的默认文件夹名
    UNKNOWN_FOLDER_NAME = "未识别角色"
    
    # 是否移动文件（False 则复制）
    MOVE_FILES = True
    
    # ==================== AI 提示词配置 ====================
    AI_PROMPT_TEMPLATE = """
请分析这些图片中 Coser 扮演的角色。

要求：
1. 识别出角色的名字和所属作品
2. 如果无法识别具体角色，返回 "未知"
3. 只返回最主要的角色（如果有多个）

请以 JSON 格式返回结果：
{
    "character": "角色名",
    "source": "作品名"
}

如果无法识别，返回：
{
    "character": "未知",
    "source": "未知"
}
"""
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = "INFO"
    
    # ==================== 性能配置 ====================
    # 图像缩放大小（用于加速处理，设为 None 则不缩放）
    PROCESS_IMAGE_WIDTH = 1280
    
    # 上传到 API 的图片质量
    UPLOAD_IMAGE_QUALITY = 85
    
    @classmethod
    def validate(cls):
        """验证配置是否正确"""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("❌ 未设置 GEMINI_API_KEY，请在 .env 文件中配置")
        
        if errors:
            print("\n配置错误：")
            for error in errors:
                print(f"  {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("\n" + "="*60)
        print("📋 当前配置")
        print("="*60)
        print(f"AI 模型: {cls.GEMINI_MODEL}")
        print(f"场景检测阈值: {cls.SCENE_THRESHOLD}")
        print(f"每视频最大帧数: {cls.MAX_FRAMES_PER_VIDEO}")
        print(f"人脸检测置信度: {cls.FACE_DETECTION_CONFIDENCE}")
        print(f"哈希差异阈值: {cls.HASH_DIFF_THRESHOLD}")
        print(f"文件操作模式: {'移动' if cls.MOVE_FILES else '复制'}")
        print(f"API Key: {'已设置 ✓' if cls.GEMINI_API_KEY else '未设置 ✗'}")
        print("="*60 + "\n")


if __name__ == "__main__":
    Config.print_config()
    Config.validate()
