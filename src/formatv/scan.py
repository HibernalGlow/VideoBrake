"""
文件扫描模块 - 负责搜索和分类视频文件
"""
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
from rich.console import Console

# 导入配置处理
from .config import get_video_extensions, get_prefix_list, get_prefix_by_name, get_blacklist
# 设置控制台对象
console = Console()
def find_video_files(directory: str) -> Dict[str, Any]:
    """
    在指定目录查找视频文件，区分普通视频文件、.nov文件和带各类前缀的文件
    
    Args:
        directory: 目录路径
        
    Returns:
        Dict[str, Any]: 包含分类后文件列表的字典，格式如下：
        {
            "nov_files": [...],  # .nov文件列表
            "normal_files": [...],  # 普通视频文件列表
            "prefixed_files": {
                "prefix1": [...],  # 带前缀1的文件列表
                "prefix2": [...],  # 带前缀2的文件列表
                ...
            }
        }
    """
    # 从配置加载视频格式和前缀
    video_extensions = tuple(get_video_extensions())
    prefixes = get_prefix_list()
    
    # 准备结果容器
    result = {
        "nov_files": [],
        "normal_files": [],
    "prefixed_files": {},
    "skipped_paths": []
    }
    
    # 初始化每个前缀的文件列表
    for prefix_info in prefixes:
        prefix_name = prefix_info.get("name")
        result["prefixed_files"][prefix_name] = []
    
    console.print(f"[blue]正在扫描文件: {directory}...[/blue]")
    
    # 使用os.walk快速遍历目录，支持基于黑名单关键词跳过目录
    blacklist = [s.lower() for s in get_blacklist() or []]

    for root, dirs, files in os.walk(directory):
        # 如果当前路径包含任一黑名单关键词，则跳过该目录及其子目录
        root_lower = root.lower()
        if any(kw in root_lower for kw in blacklist):
            # 清空dirs以防os.walk继续遍历子目录，并记录/打印被跳过路径，避免误以为是扫描错误
            dirs.clear()
            console.print(f"[yellow]跳过黑名单路径（已记录）：{root}[/yellow]")
            result["skipped_paths"].append(root)
            continue
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()
            
            # 检查是否为.nov文件
            if file_lower.endswith('.nov'):
                base_name = file[:-4]
                if any(base_name.lower().endswith(ext) for ext in video_extensions):
                    result["nov_files"].append(file_path)
                continue
            
            # 检查是否为带前缀的文件（忽略视频格式差异，只要前缀匹配就记录）
            is_prefixed = False
            for prefix_info in prefixes:
                prefix = prefix_info.get("prefix")
                prefix_name = prefix_info.get("name")

                if file.startswith(prefix):
                    result["prefixed_files"][prefix_name].append(file_path)
                    is_prefixed = True
                    break
            
            # 如果不是带前缀的文件，检查是否为普通视频文件
            if not is_prefixed and any(file_lower.endswith(ext) for ext in video_extensions):
                result["normal_files"].append(file_path)
    
    return result


def find_video_files_recursive(directory: str, recursive: bool = False) -> List[str]:
    """
    查找目录中的视频文件，支持递归搜索
    
    Args:
        directory: 目录路径
        recursive: 是否递归搜索
        
    Returns:
        List[str]: 视频文件路径列表
    """
    video_extensions = get_video_extensions()
    nov_extensions = [ext + '.nov' for ext in video_extensions]
    all_extensions = tuple(video_extensions + nov_extensions)
    
    video_files = []
    
    blacklist = [s.lower() for s in get_blacklist() or []]

    if recursive:
        for root, dirs, files in os.walk(directory):
            root_lower = root.lower()
            if any(kw in root_lower for kw in blacklist):
                dirs.clear()
                console.print(f"[yellow]跳过黑名单路径（递归）：{root}[/yellow]")
                continue
            for file in files:
                if file.lower().endswith(all_extensions):
                    video_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            # 当非递归时，仅检查当前目录下的文件名，不检查子目录，但仍应跳过黑名单相关的目录名
            if any(kw in directory.lower() for kw in blacklist):
                console.print(f"[yellow]跳过黑名单路径（非递归）：{directory}[/yellow]")
                break
            if file.lower().endswith(all_extensions):
                video_files.append(os.path.join(directory, file))
                
    return video_files


def scan_directories(path_data: Dict[str, Any], recursive: bool = False) -> Dict[str, Any]:
    """
    扫描多个目录中的视频文件
    
    Args:
        path_data: 包含路径信息的数据字典
        recursive: 是否递归搜索子文件夹
        
    Returns:
        Dict[str, Any]: 扩展后的数据字典，包含扫描结果，格式如下：
        {
            "paths": [path1, path2, ...],
            "count": 路径数量,
            "source": "clipboard" 或 "input",
            "scan_results": {
                path1: {
                    "nov_files": [...],
                    "normal_files": [...],
                    "prefixed_files": {
                        "prefix1": [...],
                        ...
                    }
                },
                ...
            }
        }
    """
    paths = path_data.get("paths", [])
    result = path_data.copy()
    
    # 添加扫描结果字段
    result["scan_results"] = {}
    
    for path in paths:
        scan_result = find_video_files(path)
        result["scan_results"][path] = scan_result
    
    return result
