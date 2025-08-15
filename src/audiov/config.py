"""
配置管理模块
负责加载和管理音频提取的配置选项
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为空则使用默认路径
        """
        if config_path is None:
            # 使用默认配置文件路径
            self.config_path = Path(__file__).parent / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                console.print(f"✅ 配置文件加载成功: {self.config_path}", style="green")
                return config
            else:
                console.print(f"⚠️  配置文件不存在: {self.config_path}", style="yellow")
                return self._get_default_config()
        except Exception as e:
            console.print(f"❌ 配置文件加载失败: {e}", style="red")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "ffmpeg": {
                "executable_path": "ffmpeg",
                "timeout": 300
            },
            "audio_formats": {
                "mp3": {
                    "codec": "libmp3lame",
                    "extension": ".mp3",
                    "quality": "-q:a 2",
                    "description": "MP3 (高质量)"
                }
            },
            "output": {
                "default_directory": "extracted_audio",
                "preserve_structure": True,
                "overwrite_existing": False,
                "create_subdirs": True
            },
            "processing": {
                "batch_size": 5,
                "parallel_processing": False,
                "log_level": "INFO"
            },
            "ui": {
                "show_progress": True,
                "confirm_before_start": True,
                "show_file_details": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键 (例如: 'ffmpeg.executable_path')
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            console.print(f"✅ 配置已保存到: {self.config_path}", style="green")
            return True
        except Exception as e:
            console.print(f"❌ 配置保存失败: {e}", style="red")
            return False
    
    def get_audio_formats(self) -> Dict[str, Dict[str, str]]:
        """
        获取支持的音频格式
        
        Returns:
            音频格式字典
        """
        return self.get('audio_formats', {})
    
    def get_ffmpeg_path(self) -> str:
        """
        获取 FFmpeg 可执行文件路径
        
        Returns:
            FFmpeg 路径
        """
        return self.get('ffmpeg.executable_path', 'ffmpeg')
    
    def get_output_directory(self) -> str:
        """
        获取默认输出目录
        
        Returns:
            输出目录路径
        """
        return self.get('output.default_directory', 'extracted_audio')


# 全局配置实例
config_manager = ConfigManager()
