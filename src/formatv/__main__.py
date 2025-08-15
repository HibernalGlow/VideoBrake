"""
主模块 - 整合路径收集、文件扫描和操作执行，提供命令行入口点
"""
import os
import argparse
from typing import Dict, Any, List, Union
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

# 导入其他模块
from .collect import collect_paths
from .scan import scan_directories
from .execute import execute_operation
from .config import get_prefix_list, load_config

# 设置控制台对象
console = Console()


def show_scan_summary(scan_data: Dict[str, Any]) -> None:
    """
    显示扫描结果摘要
    
    Args:
        scan_data: 扫描结果数据
    """
    scan_results = scan_data.get("scan_results", {})
    
    # 计算各类文件总数
    total_normal = 0
    total_nov = 0
    total_prefixed = {}
    
    # 初始化前缀文件计数
    prefixes = get_prefix_list()
    for prefix_info in prefixes:
        prefix_name = prefix_info.get("name")
        total_prefixed[prefix_name] = 0
    
    # 汇总文件数量
    for path, data in scan_results.items():
        total_normal += len(data.get("normal_files", []))
        total_nov += len(data.get("nov_files", []))
        
        # 统计前缀文件
        for prefix_name, files in data.get("prefixed_files", {}).items():
            total_prefixed[prefix_name] += len(files)
    
    # 显示总结
    console.print(Panel.fit(f"[bold cyan]文件扫描结果[/bold cyan]"))
    console.print(f"[green]• 找到 {total_normal} 个普通视频文件[/green]")
    console.print(f"[yellow]• 找到 {total_nov} 个.nov视频文件[/yellow]")    # 显示带前缀的文件统计
    for prefix_info in prefixes:
        prefix_name = prefix_info.get("name")
        prefix = prefix_info.get("prefix")
        description = prefix_info.get("description", "")
        count = total_prefixed.get(prefix_name, 0)
        console.print(f"[blue]• 找到 {count} 个 {prefix} 前缀视频文件 ({description})[/blue]")


def select_prefix_for_check() -> str:
    """
    选择要检查重复项的前缀
    
    Returns:
        str: 选择的前缀名称
    """
    prefixes = get_prefix_list()
    console.print("[cyan]选择要检查的前缀类型：[/cyan]")
    for i, prefix_info in enumerate(prefixes, 1):
        prefix = prefix_info.get("prefix", "")
        name = prefix_info.get("name")
        description = prefix_info.get("description", "")
        console.print(f"{i}. {prefix} ({description})")
    
    # 默认选项为第一个前缀
    default_choice = "1"
    
    # 生成有效选择范围和显示选项
    valid_choices = [str(i) for i in range(1, len(prefixes) + 1)]
    choice_display = "/".join(valid_choices)
    
    # 使用显式的提示格式
    prompt_text = f"请选择 [{choice_display}] ({default_choice}): "
    choice = Prompt.ask(prompt_text, choices=valid_choices, default=default_choice)
    
    # 返回选择的前缀名称
    selected_index = int(choice) - 1
    selected_prefix = prefixes[selected_index].get("name")
    
    # 确认选择
    selected_prefix_info = prefixes[selected_index]
    console.print(f"[green]✓ 已选择: {selected_prefix_info.get('prefix')} ({selected_prefix_info.get('description')})[/green]")
    
    return selected_prefix


def interactive_mode() -> None:
    """交互式界面入口"""
    console.print(Panel.fit("视频格式处理工具", border_style="cyan"))
    console.print()
    
    # 显示功能菜单
    console.print("[cyan]可用功能：[/cyan]")
    console.print("1. 添加.nov后缀")
    console.print("2. 恢复原始文件名")
    console.print("3. 检查重复项")
    console.print("q. 退出程序")
    console.print()
    
    choice = Prompt.ask("请选择功能", choices=["1", "2", "3", "q"], default="3")
    
    if choice == "q":
        return
    
    # 收集路径
    use_clipboard = Confirm.ask("是否从剪贴板读取路径？", default=False)
    path_data = collect_paths(use_clipboard=use_clipboard, multi_path=True)
    
    if not path_data.get("paths", []):
        return  # 无有效路径，直接返回
    
    # 询问是否递归处理
    recursive = Confirm.ask("是否递归处理子文件夹？", default=False)
    
    # 扫描文件
    scan_data = scan_directories(path_data, recursive=recursive)
    
    # 显示扫描结果摘要
    show_scan_summary(scan_data)
    
    # 根据选择执行操作
    operation_map = {
        "1": "add_nov",
        "2": "remove_nov",
        "3": "check_duplicates",
    }
    
    operation = operation_map.get(choice)
    if operation:
        if operation == "check_duplicates":
            # 选择要检查的前缀
            prefix_name = select_prefix_for_check()
            result = execute_operation(scan_data, operation, prefix_name=prefix_name, recursive=recursive)
        else:
            result = execute_operation(scan_data, operation, recursive=recursive)
    
    console.print()
    Prompt.ask("[green]按回车继续[/green]")


def command_line_mode(args: argparse.Namespace) -> None:
    """命令行模式入口"""
    # 显示标题
    console.print(Panel.fit("[bold cyan]视频文件格式批量处理工具[/bold cyan]"))
    
    # 收集路径
    use_clipboard = args.clipboard
    multi_path = not args.single
    
    path_data = collect_paths(use_clipboard=use_clipboard, multi_path=multi_path)
    if not path_data.get("paths", []):
        return  # 无有效路径，直接返回
    
    # 扫描文件
    scan_data = scan_directories(path_data, recursive=args.recursive)
    
    # 显示扫描结果摘要
    show_scan_summary(scan_data)
    
    # 根据命令行参数执行操作
    if args.check:
        # 检查重复项
        prefix_name = args.prefix if args.prefix else "hb"  # 默认为 hb 前缀
        result = execute_operation(scan_data, "check_duplicates", prefix_name=prefix_name, recursive=args.recursive)
    elif args.restore:
        # 恢复原始文件名
        result = execute_operation(scan_data, "remove_nov", recursive=args.recursive)
    elif args.add_nov:
        # 添加.nov后缀
        result = execute_operation(scan_data, "add_nov", recursive=args.recursive)
    else:
        # 如果没有指定操作，提示用户选择
        console.print("\n[cyan]未指定操作，请选择要执行的操作：[/cyan]")
        console.print("1. 添加.nov后缀")
        console.print("2. 恢复原始文件名")
        console.print("3. 检查重复项")
        
        choice = Prompt.ask("请选择", choices=["1", "2", "3"], default="3")
        
        operation_map = {
            "1": "add_nov",
            "2": "remove_nov", 
            "3": "check_duplicates"
        }
        
        operation = operation_map.get(choice)
        
        if operation == "check_duplicates":
            # 选择要检查的前缀
            prefix_name = select_prefix_for_check()
            result = execute_operation(scan_data, operation, prefix_name=prefix_name, recursive=args.recursive)
        else:
            result = execute_operation(scan_data, operation, recursive=args.recursive)


def main() -> None:
    """主函数"""
    # 处理命令行参数
    parser = argparse.ArgumentParser(description="视频文件格式批量处理工具")
    parser.add_argument('-c', '--clipboard', action='store_true', 
                       help='从剪贴板读取路径')
    parser.add_argument('-s', '--single', action='store_true', 
                       help='禁用多路径输入模式，仅输入单个路径')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='启用交互式模式')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归处理子文件夹')
    
    # 添加操作组，互斥选项
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--add-nov', action='store_true',
                       help='添加.nov后缀（默认操作）')
    group.add_argument('--restore', action='store_true',
                       help='恢复原始文件名（移除.nov后缀）')
    group.add_argument('--check', action='store_true',
                       help='检查重复项')
    
    # 添加前缀选项
    parser.add_argument('-p', '--prefix', type=str,
                       help='指定用于检查重复的前缀名称，默认为"hb"')
    
    args = parser.parse_args()
    
    # 显示多路径提示
    if not args.single and not args.clipboard:
        console.print("[blue]多路径输入模式已启用，每行输入一个路径，输入空行结束[/blue]")
    
    # 选择运行模式
    if args.interactive:
        interactive_mode()
    else:
        command_line_mode(args)


if __name__ == '__main__':
    main()