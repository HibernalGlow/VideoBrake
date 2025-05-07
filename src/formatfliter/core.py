import os
import concurrent.futures
import time
from pathlib import Path
import sys
import pyperclip
from typing import List, Tuple, Dict, Any, Optional

# 导入Rich库用于美化输出，替换prompt_toolkit
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
from rich.progress import TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

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


def find_video_files(directory: str) -> Tuple[List[str], List[str], List[str]]:
    """
    在指定目录查找视频文件，区分普通视频文件、.nov文件和带[#hb]前缀的文件
    
    Args:
        directory: 目录路径
        
    Returns:
        Tuple[List[str], List[str], List[str]]: (.nov文件列表, 普通视频文件列表, [#hb]前缀文件列表)
    """
    # 支持的视频格式
    video_extensions = ('.mp4', '.avi', '.mkv', '.wmv', '.mov', '.flv', '.webm', '.m4v','.ts','.mts')
    hb_prefix = '[#hb]'

    console.print("[blue]正在扫描文件...[/blue]")
    nov_files = []
    normal_files = []
    hb_files = []

    # 使用os.walk快速遍历目录
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()

            if file_lower.endswith('.nov'):
                # 检查.nov文件的原始扩展名是否为视频格式
                base_name = file[:-4]
                if any(base_name.lower().endswith(ext) for ext in video_extensions):
                    nov_files.append(file_path)
            elif file.startswith(hb_prefix):
                 # 检查带 [#hb] 前缀的文件是否为视频格式 (检查去除前缀后的部分)
                base_name_with_ext = file[len(hb_prefix):]
                if any(base_name_with_ext.lower().endswith(ext) for ext in video_extensions):
                    hb_files.append(file_path)
            else:
                # 检查普通文件是否为视频格式
                if any(file_lower.endswith(ext) for ext in video_extensions):
                    normal_files.append(file_path)

    return nov_files, normal_files, hb_files


def check_and_save_duplicates(directory: str, nov_files: List[str], normal_files: List[str], hb_files: List[str]) -> None:
    """
    检查[#hb]文件对应的无前缀文件，并保存无前缀文件路径
    
    Args:
        directory: 目录路径
        nov_files: .nov文件列表
        normal_files: 普通视频文件列表
        hb_files: [#hb]前缀文件列表
    """
    if not hb_files:
        console.print("\n[yellow]没有找到带 [#hb] 前缀的视频文件，无需检查。[/yellow]")
        return # 没有带[#hb]前缀的文件，无需检查

    hb_prefix = '[#hb]'
    duplicate_non_hb_files = []
    non_hb_lookup = {} # {(directory, base_name_without_ext): full_path}

    # 建立无前缀文件的查找字典
    for f in normal_files:
        p = Path(f)
        key = (str(p.parent), p.stem)
        non_hb_lookup[key] = f
    for f in nov_files:
        p = Path(f)
        original_name_path = Path(p.stem) # 获取 .nov 前的文件名（含原始扩展名）
        key = (str(p.parent), original_name_path.stem) # 获取不含扩展名的基础名
        # 存储的是添加 .nov 前的原始路径
        non_hb_lookup[key] = f[:-4]

    # 查找匹配项
    for hb_file in hb_files:
        hb_path = Path(hb_file)
        hb_dir = str(hb_path.parent)
        hb_name = hb_path.name
        # 去掉[#hb]前缀，获取基础名（不含扩展名）
        base_name_with_ext = hb_name[len(hb_prefix):]
        base_name_without_ext = Path(base_name_with_ext).stem
        lookup_key = (hb_dir, base_name_without_ext)

        if lookup_key in non_hb_lookup:
            duplicate_non_hb_files.append(non_hb_lookup[lookup_key])

    # 保存结果
    if duplicate_non_hb_files:
        output_filename = 'duplicate_videos.txt'
        output_path = os.path.join(directory, output_filename) # 保存在处理目录的根目录
        try:
            # 去重并排序
            unique_duplicates = sorted(list(set(duplicate_non_hb_files)))
            with open(output_path, 'w', encoding='utf-8') as f:
                for file_path in unique_duplicates:
                    f.write(file_path + '\n')
            console.print(f"\n[green]✓ 发现 {len(unique_duplicates)} 个对应的无前缀文件，列表已保存到:[/green] {output_path}")
        except Exception as e:
            console.print(f"\n[red]✗ 错误：无法写入重复文件列表到 {output_path}: {e}[/red]")
    else:
        console.print("\n[green]✓ 未发现 [#hb] 文件对应的无前缀重复文件。[/green]")


def process_videos(directory: str) -> None:
    """
    处理指定目录下的视频文件，提供添加/移除.nov后缀和检查重复项的功能
    
    Args:
        directory: 目录路径
    """
    # 快速搜索文件
    nov_files, normal_files, hb_files = find_video_files(directory)

    console.print(Panel.fit(f"[bold cyan]文件扫描结果[/bold cyan]"))
    console.print(f"[green]• 找到 {len(normal_files)} 个普通视频文件[/green]")
    console.print(f"[yellow]• 找到 {len(nov_files)} 个.nov视频文件[/yellow]")
    console.print(f"[blue]• 找到 {len(hb_files)} 个 [#hb] 前缀视频文件[/blue]")

    # 创建选择菜单
    console.print(Panel.fit("[bold cyan]请选择要执行的操作[/bold cyan]"))
    console.print("1. 添加.nov后缀")
    console.print("2. 恢复原始文件名")
    console.print("3. 检查[#hb]重复项")
    console.print("0. 退出程序")
    
    choice = Prompt.ask("请选择", choices=["0", "1", "2", "3"], default="2")

    if choice == '0':
        console.print("[yellow]操作已取消。[/yellow]")
        return

    # 根据选择执行操作
    if choice == '1':
        files_to_process = normal_files
        add_nov = True
        action_desc = "添加.nov后缀"
    elif choice == '2':
        files_to_process = nov_files
        add_nov = False
        action_desc = "恢复原始文件名"
    elif choice == '3':
        # 只执行检查重复项的操作
        console.print("\n[blue]开始检查 [#hb] 重复项...[/blue]")
        check_and_save_duplicates(directory, nov_files, normal_files, hb_files)
        console.print("[green]✓ 检查完成。[/green]")
        return # 检查完成后直接返回
    else:
        console.print("[red]无效的选择。[/red]")
        return

    # --- 文件处理逻辑 (仅用于选项 1 和 2) ---
    total_files = len(files_to_process)
    if total_files == 0:
        console.print(f"\n[yellow]⚠️ 没有找到需要执行 '{action_desc}' 操作的文件！[/yellow]")
        return

    # 使用线程池处理文件
    start_time = time.time()
    console.print(f"\n[blue]🔄 开始 {action_desc}，处理 {total_files} 个文件...[/blue]")
    
    success_count = 0
    error_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]处理文件...[/cyan]", total=total_files)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
            futures = [executor.submit(process_single_file, file, add_nov) for file in files_to_process]
            
            # 收集处理结果并显示进度
            for future in concurrent.futures.as_completed(futures):
                success, result = future.result()
                
                if success:
                    success_count += 1
                else:
                    error_files.append(result)
                    
                # 更新进度
                progress.update(task, advance=1)
    
    end_time = time.time()
    console.print(Panel.fit(f"[bold green]处理完成！[/bold green]"))
    console.print(f"[green]✓ 成功处理:[/green] {success_count}/{total_files} 个文件")
    console.print(f"[blue]📊 总耗时:[/blue] {end_time - start_time:.2f} 秒")
    
    # 显示错误信息（如果有）
    if error_files:
        console.print("[yellow]⚠️ 处理过程中出现以下错误:[/yellow]")
        for error in error_files:
            console.print(f"  [red]• {error}[/red]")


class FormatFilter:
    """视频格式过滤器类，用于批量处理视频文件格式"""
    
    def process_from_clipboard(self) -> None:
        """从剪贴板读取路径并处理"""
        # 从剪贴板读取路径
        clipboard_content = pyperclip.paste()
        # 分割多行路径
        paths = [p.strip() for p in clipboard_content.splitlines() if p.strip()]
        if not paths:
            console.print("[yellow]⚠️ 剪贴板中没有有效的路径！[/yellow]")
            return
            
        self.process_paths(paths)
    
    def process_from_input(self) -> None:
        """从用户输入获取路径并处理"""
        default_path = r'E:\1EHV'  # 可以修改为更常用的默认路径或留空
        input_path = Prompt.ask("请输入要处理的路径", default=default_path)
        
        if not input_path:
            console.print("[yellow]⚠️ 请输入一个有效的路径。[/yellow]")
            return
            
        self.process_paths([input_path])
    
    def process_paths(self, paths: List[str]) -> None:
        """
        处理多个路径
        
        Args:
            paths: 路径列表
        """
        for path in paths:
            path = normalize_path(path)
            if not os.path.exists(path):
                console.print(f"[red]✗ 路径不存在: {path}[/red]")
                continue
            if not os.path.isdir(path):
                console.print(f"[red]✗ 提供的路径不是一个目录: {path}[/red]")
                continue

            console.print(Panel.fit(f"[bold cyan]处理目录: {path}[/bold cyan]"))
            process_videos(path)


def main(use_clipboard: bool = False) -> None:
    """
    主函数，提供命令行入口点
    
    Args:
        use_clipboard: 是否从剪贴板读取路径
    """
    console.print(Panel.fit("[bold cyan]视频文件格式批量处理工具[/bold cyan]"))
    
    filter_tool = FormatFilter()
    if use_clipboard:
        filter_tool.process_from_clipboard()
    else:
        filter_tool.process_from_input()


if __name__ == '__main__':
    # 处理命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="视频文件格式批量处理工具")
    parser.add_argument('-c', '--clipboard', action='store_true', help='从剪贴板读取路径')
    args = parser.parse_args()
    
    main(use_clipboard=args.clipboard)