"""
视频处理器模块

封装视频文件的分类、移动等核心操作功能
"""

import os
import json
import logging
import shutil
import send2trash
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime

# 导入Rich库
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
from rich.progress import TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

# 导入通用工具
from bitv.common_utils import (
    VideoInfo, ProcessResult, ProcessStats,
    get_bitrate_level, ensure_dir_exists, get_relative_path
)

# 导入分析器
from bitv.video_analyzer import VideoAnalyzer

console = Console()


class VideoProcessor:
    """视频处理器类，封装视频文件分类和处理功能"""
    
    def __init__(self, analyzer: Optional[VideoAnalyzer] = None):
        """
        初始化视频处理器
        
        Args:
            analyzer: 视频分析器，如果不提供则创建默认的
        """
        self.analyzer = analyzer if analyzer is not None else VideoAnalyzer()
        self.stats = ProcessStats()
    
    def classify_video(self, video_path: str, target_dir: str, is_move: bool = False) -> ProcessResult:
        """
        根据码率分类单个视频文件
        
        Args:
            video_path: 视频文件路径
            target_dir: 目标目录
            is_move: 是否移动文件（否则复制）
            
        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 分析视频
            video_info = self.analyzer.analyze_video(video_path)
            
            if not video_info:
                return ProcessResult(
                    success=False,
                    source_path=video_path,
                    error_message="无法分析视频信息"
                )
            
            # 获取码率等级
            bitrate_level = self.analyzer.get_video_bitrate_level(video_info)
            
            # 获取相对路径，用于保持目录结构
            source_dir = os.path.dirname(video_path)
            try:
                rel_path = get_relative_path(source_dir, os.path.dirname(target_dir))
            except ValueError:
                # 如果不是子目录关系，只取文件名
                rel_path = ""
            
            # 构建目标路径
            dest_dir = os.path.join(target_dir, bitrate_level, rel_path)
            ensure_dir_exists(dest_dir)
            
            dest_path = os.path.join(dest_dir, os.path.basename(video_path))
            
            # 确保目标路径不存在
            if os.path.exists(dest_path):
                # 添加时间戳来避免冲突
                filename, ext = os.path.splitext(os.path.basename(video_path))
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                dest_path = os.path.join(dest_dir, f"{filename}_{timestamp}{ext}")
            
            # 移动或复制文件
            if is_move:
                shutil.move(video_path, dest_path)
                operation = "移动"
            else:
                shutil.copy2(video_path, dest_path)
                operation = "复制"
            
            # 创建处理结果
            result = ProcessResult(
                success=True,
                source_path=video_path,
                target_path=dest_path,
                video_info=video_info,
                bitrate_level=bitrate_level
            )
            
            # 记录日志
            console.print(f"[green]✓ {operation}:[/green] {os.path.basename(video_path)} → "
                         f"[blue]{bitrate_level}[/blue] ({video_info.bitrate_mbps:.2f}Mbps)")
            
            return result
            
        except Exception as e:
            error_message = f"处理视频时出错: {str(e)}"
            logging.error(f"{error_message}: {video_path}")
            
            return ProcessResult(
                success=False,
                source_path=video_path,
                error_message=error_message
            )
    
    def classify_videos_by_bitrate(self, 
                                 source_dir: str, 
                                 target_dir: Optional[str] = None,
                                 is_move: bool = False,
                                 recursive: bool = True,
                                 json_report: bool = True) -> Dict[str, Any]:
        """
        根据码率对多个视频文件进行分类
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录，如果为None则使用源目录
            is_move: 是否移动文件（否则复制）
            recursive: 是否递归搜索子文件夹
            json_report: 是否生成JSON报告
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 如果未指定目标目录，使用源目录
        if target_dir is None:
            target_dir = source_dir
        
        # 确保目录存在
        ensure_dir_exists(target_dir)
        
        # 重置统计信息
        self.stats = ProcessStats()
        
        # 查找视频文件
        console.print(f"[blue]🔍 搜索视频文件中...[/blue]")
        video_files = self.analyzer.find_videos_in_folder(source_dir, recursive)
        
        if not video_files:
            console.print(f"[yellow]⚠️ 未找到视频文件[/yellow]")
            return {
                "success": False,
                "error": "未找到视频文件",
                "source_dir": source_dir,
                "target_dir": target_dir
            }
        
        # 显示找到的视频数量
        operation = "移动" if is_move else "复制"
        console.print(f"[green]✓ 找到 {len(video_files)} 个视频文件，准备{operation}...[/green]")
        
        # 创建日志目录
        logs_dir = os.path.join(target_dir, "logs")
        ensure_dir_exists(logs_dir)
        
        # 创建日志文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"classify_log_{timestamp}.txt")
        
        # 初始化结果字典
        result = {
            "success": True,
            "timestamp": timestamp,
            "source_dir": source_dir,
            "target_dir": target_dir,
            "is_move": is_move,
            "total_files": len(video_files),
            "results": []
        }
        
        # 处理视频文件
        with open(log_file, "w", encoding="utf-8") as f, Progress(
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
            task = progress.add_task(f"[cyan]🎬 {operation}视频文件...[/cyan]", total=len(video_files))
            
            for video_path in video_files:
                # 更新任务描述
                filename = os.path.basename(video_path)
                progress.update(task, description=f"[cyan]🎬 {operation}: {filename}[/cyan]")
                
                # 处理视频
                process_result = self.classify_video(video_path, target_dir, is_move)
                
                # 更新统计信息
                self.stats.add_result(process_result)
                
                # 添加到结果列表
                result["results"].append(process_result.to_dict())
                
                # 记录日志
                log_message = self._format_log_message(process_result)
                f.write(log_message + "-" * 50 + "\n")
                
                # 更新进度
                progress.update(task, advance=1)
        
        # 显示处理结果
        self.display_processing_results()
        
        # 更新结果统计
        result["stats"] = {
            "successful_operations": self.stats.successful_operations,
            "failed_operations": self.stats.failed_operations,
            "total_size_bytes": self.stats.total_size_bytes,
            "total_duration": self.stats.total_duration
        }
        
        # 生成JSON报告
        if json_report:
            report_path = os.path.join(logs_dir, f"classify_report_{timestamp}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            console.print(f"[green]✓ 详细报告已保存: {report_path}[/green]")
        
        # 返回结果
        console.print(f"[green]✓ {operation}完成！详细日志: {log_file}[/green]")
        return result
    
    def classify_from_json_report(self, report_path: str, is_move: bool = False) -> Dict[str, Any]:
        """
        根据JSON分析报告对视频进行分类
        
        Args:
            report_path: 分析报告路径
            is_move: 是否移动文件（否则复制）
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 读取JSON报告
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            source_dir = report.get("folder_path", "")
            if not source_dir or not os.path.exists(source_dir):
                console.print(f"[red]✗ 无法找到源目录: {source_dir}[/red]")
                return {"success": False, "error": "找不到源目录"}
            
            # 默认使用源目录作为目标目录
            target_dir = source_dir
            
            # 从报告中获取视频信息
            videos = report.get("videos", [])
            if not videos:
                console.print(f"[yellow]⚠️ 报告中没有视频信息[/yellow]")
                return {"success": False, "error": "报告中没有视频信息"}
            
            # 重置统计信息
            self.stats = ProcessStats()
            
            # 显示找到的视频数量
            operation = "移动" if is_move else "复制"
            console.print(f"[green]✓ 报告中包含 {len(videos)} 个视频文件，准备{operation}...[/green]")
            
            # 创建日志目录
            logs_dir = os.path.join(target_dir, "logs")
            ensure_dir_exists(logs_dir)
            
            # 创建日志文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(logs_dir, f"classify_from_report_{timestamp}.txt")
            
            # 初始化结果字典
            result = {
                "success": True,
                "timestamp": timestamp,
                "report_path": report_path,
                "source_dir": source_dir,
                "target_dir": target_dir,
                "is_move": is_move,
                "total_files": len(videos),
                "results": []
            }
            
            # 处理视频文件
            with open(log_file, "w", encoding='utf-8') as f, Progress(
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
                task = progress.add_task(f"[cyan]🎬 {operation}视频文件...[/cyan]", total=len(videos))
                
                for video in videos:
                    video_path = video.get("path", "")
                    if not video_path or not os.path.exists(video_path):
                        # 跳过不存在的文件
                        progress.update(task, advance=1)
                        continue
                    
                    # 更新任务描述
                    filename = os.path.basename(video_path)
                    progress.update(task, description=f"[cyan]🎬 {operation}: {filename}[/cyan]")
                    
                    # 获取码率等级
                    bitrate_level = video.get("bitrate_level", "")
                    
                    if not bitrate_level:
                        # 如果报告中没有码率等级，使用分析器获取
                        video_info = self.analyzer.analyze_video(video_path)
                        if video_info:
                            bitrate_level = self.analyzer.get_video_bitrate_level(video_info)
                    
                    # 获取相对路径，用于保持目录结构
                    source_dir = os.path.dirname(video_path)
                    try:
                        rel_path = get_relative_path(source_dir, os.path.dirname(target_dir))
                    except ValueError:
                        # 如果不是子目录关系，只取文件名
                        rel_path = ""
                    
                    # 构建目标路径
                    dest_dir = os.path.join(target_dir, bitrate_level, rel_path)
                    ensure_dir_exists(dest_dir)
                    
                    dest_path = os.path.join(dest_dir, os.path.basename(video_path))
                    
                    # 确保目标路径不存在
                    if os.path.exists(dest_path):
                        # 添加时间戳来避免冲突
                        filename, ext = os.path.splitext(os.path.basename(video_path))
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        dest_path = os.path.join(dest_dir, f"{filename}_{timestamp}{ext}")
                    
                    try:
                        # 移动或复制文件
                        if is_move:
                            shutil.move(video_path, dest_path)
                        else:
                            shutil.copy2(video_path, dest_path)
                        
                        # 从报告中获取视频信息
                        video_info_dict = video.get("info", {})
                        video_info = VideoInfo.from_dict(video_info_dict) if video_info_dict else None
                        
                        # 创建处理结果
                        process_result = ProcessResult(
                            success=True,
                            source_path=video_path,
                            target_path=dest_path,
                            video_info=video_info,
                            bitrate_level=bitrate_level
                        )
                    except Exception as e:
                        process_result = ProcessResult(
                            success=False,
                            source_path=video_path,
                            error_message=str(e)
                        )
                    
                    # 更新统计信息
                    self.stats.add_result(process_result)
                    
                    # 添加到结果列表
                    result["results"].append(process_result.to_dict())
                    
                    # 记录日志
                    log_message = self._format_log_message(process_result)
                    f.write(log_message + "-" * 50 + "\n")
                    
                    # 更新进度
                    progress.update(task, advance=1)
            
            # 显示处理结果
            self.display_processing_results()
            
            # 更新结果统计
            result["stats"] = {
                "successful_operations": self.stats.successful_operations,
                "failed_operations": self.stats.failed_operations,
                "total_size_bytes": self.stats.total_size_bytes,
                "total_duration": self.stats.total_duration
            }
            
            # 生成JSON报告
            report_path = os.path.join(logs_dir, f"classify_result_{timestamp}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 返回结果
            console.print(f"[green]✓ {operation}完成！详细日志: {log_file}[/green]")
            console.print(f"[green]✓ 结果报告: {report_path}[/green]")
            return result
            
        except Exception as e:
            error_message = f"从报告分类视频时出错: {str(e)}"
            logging.error(error_message)
            console.print(f"[red]✗ {error_message}[/red]")
            return {"success": False, "error": error_message}
    
    def _format_log_message(self, result: ProcessResult) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if result.success:
            message = (
                f"时间: {timestamp}\n"
                f"文件: {os.path.basename(result.source_path)}\n"
                f"源路径: {result.source_path}\n"
                f"目标路径: {result.target_path}\n"
                f"分组: {result.bitrate_level}\n"
            )
            
            if result.video_info:
                message += (
                    f"时长: {result.video_info.duration:.2f}秒\n"
                    f"码率: {result.video_info.bitrate_mbps:.2f}Mbps\n"
                    f"分辨率: {result.video_info.width}x{result.video_info.height}\n"
                    f"FPS: {result.video_info.fps:.2f}\n"
                    f"大小: {result.video_info.size_mb:.2f}MB\n"
                )
        else:
            message = (
                f"时间: {timestamp}\n"
                f"文件: {os.path.basename(result.source_path)}\n"
                f"源路径: {result.source_path}\n"
                f"错误: {result.error_message}\n"
            )
        
        return message + "\n"
    
    def display_processing_results(self) -> None:
        """显示处理结果统计"""
        console.print(Panel.fit("[bold cyan]处理结果统计[/bold cyan]"))
        
        # 获取统计摘要
        summary = self.stats.get_summary()
        console.print(summary)
        
        # 显示各等级的文件数
        if self.stats.results_by_level:
            level_table = Table(title="码率等级分布")
            level_table.add_column("码率等级", style="cyan")
            level_table.add_column("文件数量", style="green")
            level_table.add_column("总大小(MB)", style="yellow")
            
            for level, results in sorted(self.stats.results_by_level.items()):
                level_size_mb = sum(r.video_info.size_bytes for r in results if r.video_info) / (1024 * 1024)
                level_table.add_row(level, f"{len(results)}", f"{level_size_mb:.2f}")
            
            console.print(level_table)