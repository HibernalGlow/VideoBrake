"""
VideoBrake - 交互式用户界面模块

提供菜单驱动的交互式界面，统一访问所有功能
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 导入Rich库用于美化输出
from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt, FloatPrompt
from rich.panel import Panel
from rich.table import Table

# 导入统一接口
from videobrake import VideoBrake
# 导入formatfliter模块所需函数
from formatfliter.__main__ import find_video_files

console = Console()


def get_path_from_input(message: str = "请输入文件夹路径") -> str:
    """从用户输入获取路径"""
    while True:
        path = Prompt.ask(message)
        
        # 处理带引号的路径
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]  # 去除首尾的引号
            
        if not path:
            console.print("[yellow]路径不能为空[/yellow]")
            continue
            
        if not os.path.exists(path):
            console.print(f"[red]路径不存在: {path}[/red]")
            continue
            
        return path


class InteractiveUI:
    """交互式用户界面类"""
    
    def __init__(self):
        """初始化交互式界面"""
        self.vb = VideoBrake()
        
    def show_main_menu(self) -> None:
        """显示主菜单"""
        while True:
            console.print(Panel.fit(f"[bold cyan]VideoBrake - 视频处理工具集 [/bold cyan]"))
            
            console.print("1. 视频分析功能")
            console.print("2. 视频分类功能")
            console.print("3. 视频格式处理功能")
            console.print("0. 退出程序")
            
            choice = Prompt.ask("请选择功能", choices=["0", "1", "2", "3"], default="1")
            
            if choice == "0":
                console.print("[yellow]程序已退出[/yellow]")
                break
            elif choice == "1":
                self.show_analysis_menu()
            elif choice == "2":
                self.show_classification_menu()
            elif choice == "3":
                self.show_format_menu()
            
            # 询问是否继续
            if not Confirm.ask("是否返回主菜单?", default=True):
                console.print("[yellow]程序已退出[/yellow]")
                break
    
    def show_analysis_menu(self) -> None:
        """视频分析菜单"""
        console.print(Panel.fit("[bold cyan]视频分析功能[/bold cyan]"))
        
        console.print("1. 分析单个视频文件")
        console.print("2. 分析整个文件夹")
        console.print("0. 返回上级菜单")
        
        choice = Prompt.ask("请选择功能", choices=["0", "1", "2"], default="1")
        
        if choice == "0":
            return
        elif choice == "1":
            self.analyze_single_file()
        elif choice == "2":
            self.analyze_folder()
    
    def show_classification_menu(self) -> None:
        """视频分类菜单"""
        console.print(Panel.fit("[bold cyan]视频分类功能[/bold cyan]"))
        
        console.print("1. 按码率分类视频文件")
        console.print("2. 根据JSON报告分类视频")
        console.print("0. 返回上级菜单")
        
        choice = Prompt.ask("请选择功能", choices=["0", "1", "2"], default="1")
        
        if choice == "0":
            return
        elif choice == "1":
            self.classify_videos()
        elif choice == "2":
            self.classify_from_report()
    
    def show_format_menu(self) -> None:
        """视频格式处理菜单"""
        console.print(Panel.fit("[bold cyan]视频格式处理功能[/bold cyan]"))
        
        console.print("1. 处理目录(添加/移除.nov后缀和检查重复项)")
        console.print("2. 添加.nov后缀到单个文件")
        console.print("3. 移除单个文件的.nov后缀")
        console.print("4. 检查[#hb]重复项")
        console.print("0. 返回上级菜单")
        
        choice = Prompt.ask("请选择功能", choices=["0", "1", "2", "3", "4"], default="1")
        
        if choice == "0":
            return
        elif choice == "1":
            folder_path = get_path_from_input("请输入要处理的文件夹路径")
            self.vb.process_videos_in_dir(folder_path)
        elif choice == "2":
            file_path = get_path_from_input("请输入要添加.nov后缀的视频文件路径")
            success, result = self.vb.add_nov_extension(file_path)
            if success:
                console.print(f"[green]成功添加.nov后缀: {file_path}.nov[/green]")
            else:
                console.print(f"[red]添加.nov后缀失败: {result}[/red]")
        elif choice == "3":
            file_path = get_path_from_input("请输入要移除.nov后缀的文件路径")
            success, result = self.vb.remove_nov_extension(file_path)
            if success:
                console.print(f"[green]成功移除.nov后缀: {os.path.splitext(file_path)[0]}[/green]")
            else:
                console.print(f"[red]移除.nov后缀失败: {result}[/red]")
        elif choice == "4":
            folder_path = get_path_from_input("请输入要检查重复项的文件夹路径")
            nov_files, normal_files, hb_files = find_video_files(folder_path)
            self.vb.check_duplicates(folder_path, nov_files, normal_files, hb_files)
    
    def analyze_single_file(self) -> None:
        """分析单个视频文件"""
        file_path = get_path_from_input("请输入视频文件路径")
        
        console.print(f"[blue]正在分析视频: {file_path}[/blue]")
        video_info = self.vb.analyze_video(file_path)
        
        if video_info:
            console.print(f"[green]文件名:[/green] {video_info.filename}")
            console.print(f"[green]码率:[/green] {video_info.bitrate_mbps:.2f} Mbps")
            console.print(f"[green]时长:[/green] {video_info.duration:.2f} 秒 ({video_info.duration / 60:.2f} 分钟)")
            console.print(f"[green]分辨率:[/green] {video_info.width}x{video_info.height}")
            console.print(f"[green]帧率:[/green] {video_info.fps:.2f} fps")
            console.print(f"[green]文件大小:[/green] {video_info.size_mb:.2f} MB")
        else:
            console.print(f"[red]无法分析视频文件: {file_path}[/red]")
    
    def analyze_folder(self) -> None:
        """分析视频文件夹"""
        folder_path = get_path_from_input("请输入视频文件夹路径")
        
        # 询问是否递归搜索
        recursive = Confirm.ask("是否递归搜索子文件夹?", default=True)
        
        # 询问码率等级设置
        console.print("[cyan]设置码率等级参数[/cyan]")
        step_mb = FloatPrompt.ask("每档码率大小(Mbps)", default=1.0)
        max_levels = IntPrompt.ask("最大档位数量", default=10)
        
        # 创建分析器并分析文件夹
        try:
            # 重新创建带有自定义参数的实例
            self.vb = VideoBrake(bitrate_step=step_mb, max_steps=max_levels)
            console.print(f"[cyan]开始分析文件夹: {folder_path}[/cyan]")
            
            # 分析文件夹
            result = self.vb.analyze_folder(folder_path, recursive=recursive)
            
            # 生成JSON报告
            if Confirm.ask("是否生成JSON报告?", default=True):
                report_path = self.vb.generate_json_report(result)
                console.print(f"[green]分析报告已保存: {report_path}[/green]")
                
                # 询问是否根据分析结果进行分类
                if Confirm.ask("是否根据分析结果对视频进行分类?", default=False):
                    is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
                    self.vb.classify_from_report(report_path, is_move=is_move)
        except Exception as e:
            console.print(f"[red]分析过程中出错: {str(e)}[/red]")
    
    def classify_videos(self) -> None:
        """分类视频文件"""
        # 获取源文件夹路径
        source_dir = get_path_from_input("请输入源文件夹路径")
        
        # 询问目标目录
        use_same_dir = Confirm.ask("是否使用源文件夹作为目标文件夹?", default=True)
        target_dir = source_dir if use_same_dir else get_path_from_input("请输入目标文件夹路径")
        
        # 询问是否递归搜索
        recursive = Confirm.ask("是否递归搜索子文件夹?", default=True)
        
        # 询问是否移动文件
        is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
        
        # 询问码率等级设置
        console.print("[cyan]设置码率等级参数[/cyan]")
        step_mb = FloatPrompt.ask("每档码率大小(Mbps)", default=1.0)
        max_levels = IntPrompt.ask("最大档位数量", default=10)
        
        # 重新创建带有自定义参数的实例
        self.vb = VideoBrake(bitrate_step=step_mb, max_steps=max_levels)
        
        # 执行分类
        self.vb.classify_videos(
            source_dir=source_dir,
            target_dir=target_dir,
            is_move=is_move,
            recursive=recursive
        )
    
    def classify_from_report(self) -> None:
        """根据报告分类视频"""
        # 获取报告路径
        report_path = get_path_from_input("请输入JSON分析报告路径")
        
        # 询问是否移动文件
        is_move = Confirm.ask("是否移动文件（否则复制）?", default=False)
        
        # 执行分类
        self.vb.classify_from_report(report_path, is_move=is_move)


def run_interactive():
    """运行交互式界面"""
    try:
        ui = InteractiveUI()
        ui.show_main_menu()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]程序被用户中断[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]程序出错: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(run_interactive())