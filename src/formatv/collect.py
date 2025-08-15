"""
路径收集模块 - 负责从用户输入、剪贴板等获取路径
"""
import os
import pyperclip
from typing import List, Dict, Any, Union
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

# 导入配置处理
from .config import get_default_path

# 设置控制台对象
console = Console()


def normalize_path(path: str) -> str:
    """
    处理复制粘贴的路径，移除引号，处理转义字符
    
    Args:
        path: 原始路径
        
    Returns:
        str: 标准化后的路径
    """
    path = path.strip('" \'')  # 移除首尾的引号和空格
    return os.path.normpath(path)  # 标准化路径分隔符


def collect_from_clipboard() -> List[str]:
    """
    从剪贴板读取路径
    
    Returns:
        List[str]: 有效路径列表
    """
    # 从剪贴板读取路径
    clipboard_content = pyperclip.paste()
    
    # 分割多行路径并过滤空行
    paths = [p.strip() for p in clipboard_content.splitlines() if p.strip()]
    
    if not paths:
        console.print("[yellow]⚠️ 剪贴板中没有有效的路径！[/yellow]")
        return []
        
    return [normalize_path(p) for p in paths]


def collect_from_input(multi_path: bool = True, default_path: str = None) -> List[str]:
    """
    从用户输入获取路径，支持单路径和多路径模式
    
    Args:
        multi_path: 是否启用多路径输入模式，默认为True
        default_path: 默认路径，如果未指定则从配置文件获取
        
    Returns:
        List[str]: 有效路径列表
    """
    paths = []
    
    # 如果未指定默认路径，从配置获取
    if default_path is None:
        default_path = get_default_path()
    
    if multi_path:
        # 多路径输入模式
        console.print("[blue]请输入要处理的路径 (每行一个，输入空行结束)[/blue]")
        
        while True:
            # 第一次输入提供默认值，后续输入不提供默认值
            if not paths:
                input_path = Prompt.ask("路径", default=default_path)
            else:
                input_path = Prompt.ask("路径 (空行结束)")
            
            # 如果输入为空行，结束输入
            if not input_path.strip():
                break
                
            # 标准化路径
            paths.append(normalize_path(input_path))
    else:
        # 单路径输入模式
        input_path = Prompt.ask("请输入要处理的路径", default=default_path)
        
        if not input_path:
            console.print("[yellow]⚠️ 请输入一个有效的路径。[/yellow]")
            return []
            
        paths = [normalize_path(input_path)]
    
    # 检查是否有路径输入
    if not paths:
        console.print("[yellow]⚠️ 未输入有效的路径。[/yellow]")
        return []
    
    # 验证路径
    valid_paths = []
    for path in paths:
        if not os.path.exists(path):
            console.print(f"[red]✗ 路径不存在: {path}[/red]")
            continue
        valid_paths.append(path)
    
    # 检查有效路径
    if not valid_paths:
        console.print("[yellow]⚠️ 没有有效的路径可以处理。[/yellow]")
        return []
        
    # 显示收集到的路径数量
    console.print(f"[green]✓ 收集到 {len(valid_paths)} 个有效路径[/green]")
    return valid_paths


def collect_paths(use_clipboard: bool = False, multi_path: bool = True) -> Dict[str, Any]:
    """
    收集路径并组织成处理数据
    
    Args:
        use_clipboard: 是否从剪贴板读取路径
        multi_path: 是否启用多路径输入模式
        
    Returns:
        Dict[str, Any]: 包含路径信息的数据字典，格式如下：
        {
            "paths": [path1, path2, ...],
            "count": 路径数量,
            "source": "clipboard" 或 "input"
        }
    """
    paths = []
    source = "clipboard" if use_clipboard else "input"
    
    if use_clipboard:
        paths = collect_from_clipboard()
    else:
        paths = collect_from_input(multi_path=multi_path)
    
    # 过滤掉非目录路径
    directory_paths = []
    for path in paths:
        if os.path.isdir(path):
            directory_paths.append(path)
        else:
            console.print(f"[red]✗ 提供的路径不是一个目录: {path}[/red]")
    
    result = {
        "paths": directory_paths,
        "count": len(directory_paths),
        "source": source
    }
    
    return result
