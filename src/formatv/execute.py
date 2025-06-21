"""
操作执行模块 - 负责执行具体的文件操作
"""
import os
import concurrent.futures
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Union
import pyperclip

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
from rich.progress import TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel

# 导入配置处理
from engingv.utils.config import get_video_extensions, get_prefix_list, get_prefix_by_name, get_output_filename

# 设置控制台对象
console = Console()


def process_single_file(file_path: str, add_nov: bool = True) -> Tuple[bool, str]:
    """
    处理单个文件，添加或移除.nov后缀
    
    Args:
        file_path: 文件路径
        add_nov: 是否添加.nov后缀（True为添加，False为移除）
        
    Returns:
        Tuple[bool, str]: (操作是否成功, 文件路径或错误消息)
    """
    try:
        # 获取原始文件的时间戳
        stat = os.stat(file_path)
        atime = stat.st_atime  # 访问时间
        mtime = stat.st_mtime  # 修改时间
        
        # 根据操作类型重命名文件
        new_path = file_path + '.nov' if add_nov else file_path[:-4]
        os.rename(file_path, new_path)
        
        # 恢复时间戳
        os.utime(new_path, (atime, mtime))
        return True, file_path
    except Exception as e:
        return False, f'错误 {file_path}: {e}'


def check_and_save_duplicates(output_dir: str, scan_results: Dict[str, Any], prefix_name: str = "hb") -> None:
    """
    检查带特定前缀的文件对应的无前缀文件，并保存无前缀文件路径
    
    Args:
        output_dir: 输出目录路径
        scan_results: 扫描结果数据
        prefix_name: 要检查的前缀名称，默认为"hb"
    """
    # 获取前缀信息 - 根据名称查找对应的前缀配置
    prefixes = get_prefix_list()
    prefix_info = None
    for p in prefixes:
        if p.get("name") == prefix_name:
            prefix_info = p
            break
    
    if not prefix_info:
        console.print(f"\n[yellow]⚠️ 未找到名为 '{prefix_name}' 的前缀配置[/yellow]")
        return
    
    # 获取前缀字符串和描述
    prefix = prefix_info.get("prefix")
    description = prefix_info.get("description", f"{prefix_name} 前缀文件")
    
    # 获取前缀文件 - 使用前缀名称(name)作为键
    prefixed_files = scan_results.get("prefixed_files", {}).get(prefix_name, [])
    if not prefixed_files:
        console.print(f"\n[yellow]没有找到带 '{prefix}' 前缀的视频文件，无需检查。[/yellow]")
        return
    
    nov_files = scan_results.get("nov_files", [])
    normal_files = scan_results.get("normal_files", [])
    
    # 匹配逻辑
    duplicate_non_prefixed_files = []
    non_prefixed_lookup = {}  # {(directory, base_name_without_ext): full_path}
    
    # 建立无前缀文件的查找字典
    for f in normal_files:
        p = Path(f)
        key = (str(p.parent), p.stem)
        non_prefixed_lookup[key] = f
    
    for f in nov_files:
        p = Path(f)
        original_name_path = Path(p.stem)  # 获取 .nov 前的文件名（含原始扩展名）
        key = (str(p.parent), original_name_path.stem)  # 获取不含扩展名的基础名
        # 存储的是添加 .nov 前的原始路径
        non_prefixed_lookup[key] = f[:-4]
    
    # 查找匹配项
    for prefixed_file in prefixed_files:
        prefixed_path = Path(prefixed_file)
        prefixed_dir = str(prefixed_path.parent)
        prefixed_name = prefixed_path.name
        
        # 去掉前缀，获取基础名（不含扩展名）
        base_name_with_ext = prefixed_name[len(prefix):]
        base_name_without_ext = Path(base_name_with_ext).stem
        lookup_key = (prefixed_dir, base_name_without_ext)
        
        if lookup_key in non_prefixed_lookup:
            duplicate_non_prefixed_files.append(non_prefixed_lookup[lookup_key])
    
    # 处理结果
    if duplicate_non_prefixed_files:
        output_filename = get_output_filename()
        output_path = os.path.join(output_dir, output_filename)
        try:
            # 去重并排序
            unique_duplicates = sorted(list(set(duplicate_non_prefixed_files)))
            
            # 将结果写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                for file_path in unique_duplicates:
                    f.write(file_path + '\n')
            
            # 将结果复制到剪贴板
            clipboard_content = '\n'.join(unique_duplicates)
            pyperclip.copy(clipboard_content)
            
            console.print(f"\n[green]✓ 发现 {len(unique_duplicates)} 个对应的无前缀文件[/green]")
            console.print(f"[green]✓ 列表已保存到:[/green] {output_path}")
            console.print(f"[green]✓ 重复文件路径已复制到剪贴板![/green]")
        except Exception as e:
            console.print(f"\n[red]✗ 错误：无法写入重复文件列表到 {output_path}: {e}[/red]")
    else:
        console.print(f"\n[green]✓ 未发现 '{prefix}' 文件对应的无前缀重复文件。[/green]")


def add_nov_extension_to_files(files: List[str]) -> Tuple[int, List[str]]:
    """
    为文件列表添加.nov后缀
    
    Args:
        files: 文件路径列表
        
    Returns:
        Tuple[int, List[str]]: (成功处理的文件数量, 错误消息列表)
    """
    success_count = 0
    error_files = []
    
    # 过滤掉已经有.nov后缀的文件
    files_to_process = [f for f in files if not f.lower().endswith('.nov')]
    
    if not files_to_process:
        return 0, []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"正在添加.nov扩展名...", total=len(files_to_process))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_single_file, file, True) for file in files_to_process]
            
            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                result, file_or_error = future.result()
                if result:
                    success_count += 1
                else:
                    error_files.append(file_or_error)
                progress.advance(task)
    
    return success_count, error_files


def remove_nov_extension_from_files(files: List[str]) -> Tuple[int, List[str]]:
    """
    移除文件列表中的.nov后缀
    
    Args:
        files: 文件路径列表
        
    Returns:
        Tuple[int, List[str]]: (成功处理的文件数量, 错误消息列表)
    """
    success_count = 0
    error_files = []
    
    # 只处理有.nov后缀的文件
    files_to_process = [f for f in files if f.lower().endswith('.nov')]
    
    if not files_to_process:
        return 0, []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"正在移除.nov扩展名...", total=len(files_to_process))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_single_file, file, False) for file in files_to_process]
            
            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                result, file_or_error = future.result()
                if result:
                    success_count += 1
                else:
                    error_files.append(file_or_error)
                progress.advance(task)
    
    return success_count, error_files


def execute_operation(scan_data: Dict[str, Any], operation: str, prefix_name: str = "hb", recursive: bool = False) -> Dict[str, Any]:
    """
    执行操作
    
    Args:
        scan_data: 包含扫描结果的数据字典
        operation: 操作类型，可选值为 'add_nov', 'remove_nov', 'check_duplicates'
        prefix_name: 用于检查重复项的前缀名称，默认为"hb"
        recursive: 是否递归处理子文件夹
        
    Returns:
        Dict[str, Any]: 执行结果字典
    """
    scan_results = scan_data.get("scan_results", {})
    result = {
        "operation": operation,
        "success_count": 0,
        "error_count": 0,
        "errors": [],
        "paths_processed": list(scan_results.keys()),
        "recursive": recursive,
    }
    
    if operation == 'check_duplicates':
        # 选择一个输出目录（使用第一个路径）
        if scan_results:
            output_dir = next(iter(scan_results.keys()))
            
            # 合并所有路径的文件列表
            merged_scan_results = {
                "nov_files": [],
                "normal_files": [],
                "prefixed_files": {}
            }
            
            # 初始化前缀文件容器
            prefixes = get_prefix_list()
            for prefix_info in prefixes:
                prefix_name = prefix_info.get("name")
                merged_scan_results["prefixed_files"][prefix_name] = []
              # 合并所有路径的扫描结果
            for path, data in scan_results.items():
                merged_scan_results["nov_files"].extend(data.get("nov_files", []))
                merged_scan_results["normal_files"].extend(data.get("normal_files", []))
                
                # 合并前缀文件
                for name, prefixed_files in data.get("prefixed_files", {}).items():
                    merged_scan_results["prefixed_files"][name].extend(prefixed_files)
            
            # 使用传入的前缀名称进行检查
            check_and_save_duplicates(output_dir, merged_scan_results, prefix_name)
            result["output_dir"] = output_dir
    
    elif operation == 'add_nov':
        start_time = time.time()
        all_normal_files = []
        
        for path, data in scan_results.items():
            all_normal_files.extend(data.get("normal_files", []))
        
        # 批量添加.nov后缀
        if all_normal_files:
            console.print(f"\n[blue]🔄 开始添加.nov后缀，处理 {len(all_normal_files)} 个文件...[/blue]")
            success_count, errors = add_nov_extension_to_files(all_normal_files)
            result["success_count"] = success_count
            result["error_count"] = len(errors)
            result["errors"] = errors
        else:
            console.print("\n[yellow]⚠️ 未找到需要添加.nov后缀的普通视频文件！[/yellow]")
        
        end_time = time.time()
        result["execution_time"] = end_time - start_time
    
    elif operation == 'remove_nov':
        start_time = time.time()
        all_nov_files = []
        
        for path, data in scan_results.items():
            all_nov_files.extend(data.get("nov_files", []))
        
        # 批量移除.nov后缀
        if all_nov_files:
            console.print(f"\n[blue]🔄 开始移除.nov后缀，处理 {len(all_nov_files)} 个文件...[/blue]")
            success_count, errors = remove_nov_extension_from_files(all_nov_files)
            result["success_count"] = success_count
            result["error_count"] = len(errors)
            result["errors"] = errors
        else:
            console.print("\n[yellow]⚠️ 未找到带.nov后缀的视频文件！[/yellow]")
        
        end_time = time.time()
        result["execution_time"] = end_time - start_time
    
    # 显示执行结果
    if operation in ('add_nov', 'remove_nov') and result.get("success_count", 0) > 0:
        console.print(Panel.fit(f"[bold green]处理完成！[/bold green]"))
        console.print(f"[green]✓ 成功处理:[/green] {result['success_count']} 个文件")
        
        if "execution_time" in result:
            console.print(f"[blue]📊 总耗时:[/blue] {result['execution_time']:.2f} 秒")
        
        if result.get("errors", []):
            console.print("[yellow]⚠️ 处理过程中出现以下错误:[/yellow]")
            for error in result["errors"]:
                console.print(f"  [red]• {error}[/red]")
    
    return result
