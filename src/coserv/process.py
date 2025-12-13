"""
处理脚本 - 新工作流程第三步
1. 读取已识别的 JSON 文件
2. 根据角色信息移动/复制视频文件
3. 生成处理报告
"""

import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

from config import Config
from file_organizer import FileOrganizer

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, scan_file: str, output_dir: str = "output", mode: str = "move"):
        """
        初始化处理器
        
        Args:
            scan_file: 扫描文件路径
            output_dir: 输出目录
            mode: 处理模式 (move/copy)
        """
        self.output_dir = Path(output_dir).resolve()
        self.scan_file = self.output_dir / scan_file
        self.mode = mode
        
        if not self.scan_file.exists():
            raise ValueError(f"扫描文件不存在: {self.scan_file}")
        
        # 加载扫描数据
        with open(self.scan_file, 'r', encoding='utf-8') as f:
            self.scan_data = json.load(f)
        
        # 目标目录
        self.target_dir = Path(self.scan_data["target_dir"])
        
        # 文件组织器
        self.file_organizer = FileOrganizer(str(self.target_dir))
        
        # 统计
        self.stats = {
            "total": len(self.scan_data["folders"]),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "unknown": 0
        }
    
    def process_all(self, dry_run: bool = False):
        """
        处理所有文件夹
        
        Args:
            dry_run: 是否为测试模式
        """
        if dry_run:
            print("\n⚠ 测试模式：不会实际移动/复制文件\n")
        
        folders = self.scan_data["folders"]
        
        print(f"\n开始处理 {len(folders)} 个文件夹...")
        print(f"处理模式: {'移动' if self.mode == 'move' else '复制'}")
        print()
        
        # 处理每个文件夹
        with tqdm(folders, desc="处理进度", unit="文件夹") as pbar:
            for folder_info in pbar:
                folder_name = folder_info["folder_name"]
                pbar.set_description(f"处理: {folder_name[:30]}")
                
                try:
                    self.process_single_folder(folder_info, dry_run)
                except Exception as e:
                    print(f"\n❌ 处理失败 {folder_name}: {e}\n")
                    self.stats["failed"] += 1
        
        # 打印摘要
        self.print_summary()
        
        # 打印文件组织摘要
        if not dry_run:
            self.file_organizer.print_summary()
    
    def process_single_folder(self, folder_info: Dict, dry_run: bool = False):
        """
        处理单个文件夹
        
        Args:
            folder_info: 文件夹信息
            dry_run: 是否为测试模式
        """
        folder_name = folder_info["folder_name"]
        folder_path = Path(folder_info["folder_path"])
        status = folder_info.get("status", "pending")
        
        # 跳过未识别的
        if status == "skipped":
            if RICH_AVAILABLE:
                console.print(f"  ⏭ [dim]{folder_name}[/dim]: 跳过（用户标记）")
            else:
                print(f"  ⏭ {folder_name}: 跳过（用户标记）")
            self.stats["skipped"] += 1
            return
        
        # 获取角色信息
        character_info = folder_info.get("character_info")
        
        # 处理所有视频文件
        video_files = folder_info.get("video_files", [])
        
        if not video_files:
            return
        
        # 确定目标文件夹
        if character_info and status == "identified":
            target_folder_name = self._get_target_folder_name(character_info)
            
            if RICH_AVAILABLE:
                console.print(f"  ✓ [green]{folder_name}[/green] → {target_folder_name}")
            else:
                print(f"  ✓ {folder_name} → {target_folder_name}")
        else:
            target_folder_name = Config.UNKNOWN_FOLDER_NAME
            self.stats["unknown"] += 1
            
            if RICH_AVAILABLE:
                console.print(f"  ? [yellow]{folder_name}[/yellow] → {target_folder_name} (未识别)")
            else:
                print(f"  ? {folder_name} → {target_folder_name} (未识别)")
        
        # 创建目标文件夹
        target_folder_path = self.target_dir / target_folder_name
        
        if not dry_run:
            target_folder_path.mkdir(exist_ok=True)
            
            # 处理每个视频文件
            for video_file_rel in video_files:
                video_file = self.target_dir / video_file_rel
                
                if not video_file.exists():
                    print(f"    ⚠ 文件不存在: {video_file}")
                    continue
                
                target_file = target_folder_path / video_file.name
                
                # 处理重名
                counter = 1
                while target_file.exists():
                    stem = video_file.stem
                    suffix = video_file.suffix
                    target_file = target_folder_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # 移动或复制
                if self.mode == "move":
                    shutil.move(str(video_file), str(target_file))
                else:  # copy
                    shutil.copy2(str(video_file), str(target_file))
        
        self.stats["processed"] += 1
    
    def _get_target_folder_name(self, character_info: Dict) -> str:
        """获取目标文件夹名"""
        character = character_info.get("character", "")
        source = character_info.get("source", "")
        
        if character and source:
            # 使用 file_organizer 的方法来清理文件夹名
            return self.file_organizer._sanitize_folder_name(character, source)
        else:
            return Config.UNKNOWN_FOLDER_NAME
    
    def print_summary(self):
        """打印处理摘要"""
        print("\n" + "="*60)
        print("📊 处理统计")
        print("="*60)
        print(f"总文件夹数: {self.stats['total']}")
        print(f"✓ 处理成功: {self.stats['processed']}")
        print(f"? 移至未识别: {self.stats['unknown']}")
        print(f"⏭ 跳过: {self.stats['skipped']}")
        print(f"❌ 失败: {self.stats['failed']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['processed'] / self.stats['total']) * 100
            print(f"\n处理率: {success_rate:.1f}%")
        
        print("="*60 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量处理脚本 - 新工作流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 测试模式（不实际移动）
  python process.py --scan-file scan_20231214_120000.json --dry-run
  
  # 移动文件
  python process.py --scan-file scan_20231214_120000.json --mode move
  
  # 复制文件
  python process.py --scan-file scan_20231214_120000.json --mode copy
  
  # 指定输出目录
  python process.py --scan-file scan_20231214_120000.json --output my_output
        """
    )
    
    parser.add_argument(
        "--scan-file",
        type=str,
        required=True,
        help="扫描文件名（在 output 目录中）"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="输出目录（默认: output）"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["move", "copy"],
        default="move",
        help="处理模式：move=移动文件，copy=复制文件（默认: move）"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="测试模式：只显示，不实际移动/复制文件"
    )
    
    args = parser.parse_args()
    
    # 打印配置
    Config.print_config()
    
    # 创建处理器
    try:
        processor = BatchProcessor(args.scan_file, args.output, args.mode)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 执行处理
    processor.process_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
