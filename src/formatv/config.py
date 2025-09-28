"""
配置加载模块 - 负责从JSON文件加载配置
"""
import os
import json
from typing import Dict, Any, List
from pathlib import Path

# 初始默认配置
DEFAULT_CONFIG = {
    "video_extensions": [
        ".mp4", ".avi", ".mkv", ".wmv", ".mov", ".flv", ".webm", 
        ".m4v", ".ts", ".mts", ".mpeg", ".mpg", ".m2ts"
    ],
    "prefixes": [
        {
            "name": "hb",
            "prefix": "[#hb]",
            "description": "HandBrake转码文件"
        }
    ],
    "default_path": "E:\\1Hub\\EH\\1EHV",
    "output_filename": "duplicate_videos.txt"
}

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> Dict[str, Any]:
    """
    从配置文件加载配置，如果文件不存在则使用默认配置
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            # 如果配置文件不存在，创建一个默认配置文件
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"加载配置文件出错: {e}")
        return DEFAULT_CONFIG


def save_config(config: Dict[str, Any]) -> None:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
    """
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置文件出错: {e}")


def get_video_extensions() -> List[str]:
    """
    获取视频文件扩展名列表
    
    Returns:
        List[str]: 视频文件扩展名列表
    """
    config = load_config()
    return config.get("video_extensions", DEFAULT_CONFIG["video_extensions"])


def get_prefix_list() -> List[Dict[str, str]]:
    """
    获取前缀列表
    
    Returns:
        List[Dict[str, str]]: 前缀信息列表
    """
    config = load_config()
    return config.get("prefixes", DEFAULT_CONFIG["prefixes"])


def get_prefix_by_name(name: str) -> str:
    """
    根据名称获取前缀
    
    Args:
        name: 前缀名称
        
    Returns:
        str: 前缀字符串，如果未找到则返回空字符串
    """
    prefixes = get_prefix_list()
    for prefix_info in prefixes:
        if prefix_info.get("name") == name:
            return prefix_info.get("prefix", "")
    return ""


def get_default_path() -> str:
    """
    获取默认路径
    
    Returns:
        str: 默认路径
    """
    config = load_config()
    return config.get("default_path", DEFAULT_CONFIG["default_path"])


def get_output_filename() -> str:
    """
    获取输出文件名
    
    Returns:
        str: 输出文件名
    """
    config = load_config()
    return config.get("output_filename", DEFAULT_CONFIG["output_filename"])


def get_blacklist() -> List[str]:
    """
    获取黑名单关键词列表，用于在路径或文件名中匹配并跳过这些路径

    Returns:
        List[str]: 黑名单关键词列表
    """
    config = load_config()
    return config.get("blacklist", DEFAULT_CONFIG.get("blacklist", []))
