#!/usr/bin/env python
"""
高性能文件扫描器

使用多种优化技术提升扫描速度:
1. scandir-rs (Rust 实现的高性能目录扫描，可选)
2. 并行处理优化
3. 扩展名缓存
4. Rich 进度条显示
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import logging

# 尝试导入高性能库
try:
    import scandir_rs
    HAS_SCANDIR_RS = True
except ImportError:
    HAS_SCANDIR_RS = False

try:
    from joblib import Parallel, delayed
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

# Rich 进度条
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeElapsedColumn, MofNCompleteColumn
)

from .config import get_video_extensions, get_prefix_list, get_blacklist

console = Console()


@dataclass
class VideoScanResult:
    """视频扫描结果"""
    path: str
    nov_files: List[str] = field(default_factory=list)
    normal_files: List[str] = field(default_factory=list)
    prefixed_files: Dict[str, List[str]] = field(default_factory=dict)
    skipped_paths: List[str] = field(default_factory=list)
    total_files: int = 0


class FastVideoScanner:
    """高性能视频文件扫描器"""
    
    def __init__(self, max_workers: int = None, use_rust: bool = True):
        """
        初始化扫描器
        
        Args:
            max_workers: 最大工作线程数
            use_rust: 是否使用 Rust 实现的 scandir
        """
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 2)
        self.use_rust = use_rust and HAS_SCANDIR_RS
        
        # 缓存配置
        self._video_extensions: Optional[Tuple[str, ...]] = None
        self._prefixes: Optional[List[Dict]] = None
        self._blacklist: Optional[List[str]] = None
    
    @property
    def video_extensions(self) -> Tuple[str, ...]:
        """获取视频扩展名 (缓存)"""
        if self._video_extensions is None:
            self._video_extensions = tuple(get_video_extensions())
        return self._video_extensions
    
    @property
    def prefixes(self) -> List[Dict]:
        """获取前缀列表 (缓存)"""
        if self._prefixes is None:
            self._prefixes = get_prefix_list()
        return self._prefixes
    
    @property
    def blacklist(self) -> List[str]:
        """获取黑名单 (缓存)"""
        if self._blacklist is None:
            self._blacklist = [s.lower() for s in (get_blacklist() or [])]
        return self._blacklist
    
    def _is_blacklisted(self, path: str) -> bool:
        """检查路径是否在黑名单中"""
        path_lower = path.lower()
        return any(kw in path_lower for kw in self.blacklist)
    
    def _classify_file(self, file_path: str, filename: str) -> Tuple[str, Optional[str]]:
        """
        分类文件
        
        Returns:
            (类型, 前缀名称或None)
            类型: 'nov', 'prefixed', 'normal', 'skip'
        """
        file_lower = filename.lower()
        
        # 检查 .nov 文件
        if file_lower.endswith('.nov'):
            base_name = filename[:-4]
            if any(base_name.lower().endswith(ext) for ext in self.video_extensions):
                return 'nov', None
            return 'skip', None
        
        # 检查带前缀的文件
        for prefix_info in self.prefixes:
            prefix = prefix_info.get("prefix")
            prefix_name = prefix_info.get("name")
            if filename.startswith(prefix):
                return 'prefixed', prefix_name
        
        # 检查普通视频文件
        if any(file_lower.endswith(ext) for ext in self.video_extensions):
            return 'normal', None
        
        return 'skip', None

    def scan_directory(self, directory: str, show_progress: bool = True) -> VideoScanResult:
        """
        扫描单个目录
        
        Args:
            directory: 目录路径
            show_progress: 是否显示进度
            
        Returns:
            VideoScanResult: 扫描结果
        """
        result = VideoScanResult(path=directory)
        
        # 初始化前缀文件字典
        for prefix_info in self.prefixes:
            result.prefixed_files[prefix_info.get("name")] = []
        
        if show_progress:
            # 显示扫描状态
            status_parts = ["[cyan]⚡ 快速扫描模式[/cyan]"]
            if self.use_rust:
                status_parts.append("[green]scandir-rs ✓[/green]")
            if HAS_JOBLIB:
                status_parts.append("[green]joblib ✓[/green]")
            status_parts.append(f"[dim]线程数: {self.max_workers}[/dim]")
            console.print(" | ".join(status_parts))
        
        # 收集所有目录
        all_dirs = self._collect_dirs(directory, show_progress)
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=30),
                MofNCompleteColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"扫描 {len(all_dirs)} 个目录", total=len(all_dirs))
                
                # 并行扫描
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(self._scan_single_dir, d): d
                        for d in all_dirs
                    }
                    for future in as_completed(futures):
                        try:
                            dir_result = future.result()
                            self._merge_results(result, dir_result)
                        except Exception as e:
                            logging.warning(f"扫描失败: {futures[future]}, {e}")
                        progress.advance(task)
        else:
            # 无进度条模式
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._scan_single_dir, d): d
                    for d in all_dirs
                }
                for future in as_completed(futures):
                    try:
                        dir_result = future.result()
                        self._merge_results(result, dir_result)
                    except Exception as e:
                        logging.warning(f"扫描失败: {futures[future]}, {e}")
        
        result.total_files = (
            len(result.nov_files) + 
            len(result.normal_files) + 
            sum(len(files) for files in result.prefixed_files.values())
        )
        
        if show_progress:
            console.print(f"[green]✓[/green] 扫描完成，共找到 {result.total_files} 个视频文件")
        
        return result
    
    def _collect_dirs(self, root: str, show_progress: bool = True) -> List[str]:
        """收集所有需要扫描的目录"""
        dirs = []
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]收集目录..."),
                console=console,
                transient=True
            ) as progress:
                progress.add_task("collecting", total=None)
                dirs = self._do_collect_dirs(root)
        else:
            dirs = self._do_collect_dirs(root)
        
        return dirs
    
    def _do_collect_dirs(self, root: str) -> List[str]:
        """实际收集目录"""
        dirs = []
        
        if self.use_rust:
            try:
                for dirpath, dirnames, _ in scandir_rs.walk(root):
                    if self._is_blacklisted(dirpath):
                        dirnames.clear()
                        continue
                    dirs.append(dirpath)
                return dirs
            except Exception:
                pass
        
        # 回退到 os.walk
        for dirpath, dirnames, _ in os.walk(root):
            if self._is_blacklisted(dirpath):
                dirnames.clear()
                continue
            dirs.append(dirpath)
        
        return dirs
    
    def _scan_single_dir(self, directory: str) -> Dict[str, Any]:
        """扫描单个目录 (不递归)"""
        result = {
            'nov_files': [],
            'normal_files': [],
            'prefixed_files': {p.get("name"): [] for p in self.prefixes},
            'skipped': False
        }
        
        if self._is_blacklisted(directory):
            result['skipped'] = True
            return result
        
        try:
            entries = os.scandir(directory)
        except (OSError, PermissionError):
            return result
        
        for entry in entries:
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                
                file_type, prefix_name = self._classify_file(entry.path, entry.name)
                
                if file_type == 'nov':
                    result['nov_files'].append(entry.path)
                elif file_type == 'prefixed':
                    result['prefixed_files'][prefix_name].append(entry.path)
                elif file_type == 'normal':
                    result['normal_files'].append(entry.path)
            except (OSError, PermissionError):
                continue
        
        return result
    
    def _merge_results(self, target: VideoScanResult, source: Dict[str, Any]):
        """合并扫描结果"""
        if source.get('skipped'):
            return
        
        target.nov_files.extend(source.get('nov_files', []))
        target.normal_files.extend(source.get('normal_files', []))
        
        for prefix_name, files in source.get('prefixed_files', {}).items():
            if prefix_name in target.prefixed_files:
                target.prefixed_files[prefix_name].extend(files)


def find_video_files_fast(directory: str, show_progress: bool = True) -> Dict[str, Any]:
    """
    快速查找视频文件的便捷函数
    
    Args:
        directory: 目录路径
        show_progress: 是否显示进度
        
    Returns:
        与原 find_video_files 兼容的字典格式
    """
    scanner = FastVideoScanner()
    result = scanner.scan_directory(directory, show_progress)
    
    return {
        "nov_files": result.nov_files,
        "normal_files": result.normal_files,
        "prefixed_files": result.prefixed_files,
        "skipped_paths": result.skipped_paths
    }
