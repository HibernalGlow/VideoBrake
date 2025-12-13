"""
识别脚本 - 新工作流程第二步
1. 读取扫描生成的 JSON 文件
2. 使用 Gemini API 识别每个文件夹的角色和原作
3. 更新 JSON 文件，填写 character_info 信息
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

from config import Config
from character_identifier import CharacterIdentifier

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


class BatchIdentifier:
    """批量识别器"""
    
    def __init__(self, scan_file: str, output_dir: str = None):
        """
        初始化识别器
        
        Args:
            scan_file: 扫描文件路径（可以是完整路径或文件名）
            output_dir: 输出目录（默认从 scan 文件推断）
        """
        # 尝试不同的路径
        scan_path = Path(scan_file)
        
        if scan_path.exists():
            # 如果是完整路径
            self.scan_file = scan_path.resolve()
            if output_dir is None:
                self.output_dir = self.scan_file.parent
            else:
                self.output_dir = Path(output_dir).resolve()
        else:
            # 如果只是文件名，尝试在多个位置查找
            found = False
            
            # 1. 当前目录
            if (Path.cwd() / scan_file).exists():
                self.scan_file = (Path.cwd() / scan_file).resolve()
                self.output_dir = Path.cwd() if output_dir is None else Path(output_dir).resolve()
                found = True
            # 2. output 目录
            elif (Path("output") / scan_file).exists():
                self.scan_file = (Path("output") / scan_file).resolve()
                self.output_dir = Path("output").resolve() if output_dir is None else Path(output_dir).resolve()
                found = True
            
            if not found:
                raise ValueError(f"扫描文件不存在: {scan_file}")
        
        # 加载扫描数据
        with open(self.scan_file, 'r', encoding='utf-8') as f:
            self.scan_data = json.load(f)
        
        # 如果还没确定输出目录，从 scan 数据推断
        if output_dir is None and not hasattr(self, 'output_dir'):
            target_dir = Path(self.scan_data.get("target_dir", "."))
            self.output_dir = target_dir / "coserv_output"
        
        # 初始化 Gemini 识别器
        try:
            self.identifier = CharacterIdentifier()
        except RuntimeError as e:
            raise RuntimeError(f"Gemini 初始化失败: {e}")
        
        # 统计
        self.stats = {
            "total": len(self.scan_data["folders"]),
            "identified": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def identify_all(self, skip_identified: bool = True, auto_save: bool = True):
        """
        识别所有文件夹
        
        Args:
            skip_identified: 是否跳过已识别的项
            auto_save: 是否自动保存（每识别一个就保存）
        """
        folders = self.scan_data["folders"]
        
        if skip_identified:
            # 过滤已识别的
            pending_folders = [f for f in folders if f["status"] == "pending"]
            print(f"\n找到 {len(pending_folders)} 个待识别文件夹（跳过 {len(folders) - len(pending_folders)} 个已处理）")
        else:
            pending_folders = folders
            print(f"\n将识别所有 {len(pending_folders)} 个文件夹")
        
        if not pending_folders:
            print("没有需要识别的文件夹")
            return
        
        print("开始批量识别...\n")
        
        # 处理每个文件夹
        with tqdm(pending_folders, desc="识别进度", unit="文件夹") as pbar:
            for folder_info in pbar:
                folder_name = folder_info["folder_name"]
                pbar.set_description(f"识别: {folder_name[:30]}")
                
                try:
                    result = self.identify_single_folder(folder_info)
                    
                    if result:
                        folder_info["character_info"] = result
                        folder_info["status"] = "identified"
                        self.stats["identified"] += 1
                        
                        if RICH_AVAILABLE:
                            console.print(f"  ✓ [green]{folder_name}[/green]: {result['character']} ({result['source']})")
                        else:
                            print(f"  ✓ {folder_name}: {result['character']} ({result['source']})")
                    else:
                        folder_info["status"] = "failed"
                        self.stats["failed"] += 1
                        
                        if RICH_AVAILABLE:
                            console.print(f"  ✗ [yellow]{folder_name}[/yellow]: 识别失败")
                        else:
                            print(f"  ✗ {folder_name}: 识别失败")
                    
                    # 自动保存
                    if auto_save:
                        self.save_scan_data()
                        
                except Exception as e:
                    print(f"\n❌ 识别异常 {folder_name}: {e}\n")
                    folder_info["status"] = "failed"
                    folder_info["notes"] = f"识别异常: {str(e)}"
                    self.stats["failed"] += 1
        
        # 最终保存
        if not auto_save:
            self.save_scan_data()
        
        # 打印摘要
        self.print_summary()
    
    def identify_single_folder(self, folder_info: Dict) -> Dict:
        """
        识别单个文件夹
        
        Args:
            folder_info: 文件夹信息
            
        Returns:
            识别结果字典
        """
        frames = folder_info.get("frames", [])
        
        if not frames:
            return None
        
        # 构造完整路径
        frame_paths = [str(self.output_dir / frame) for frame in frames]
        
        # 调用 Gemini 识别
        result = self.identifier.identify_test(frame_paths)
        
        return result
    
    def save_scan_data(self):
        """保存更新后的扫描数据"""
        with open(self.scan_file, 'w', encoding='utf-8') as f:
            json.dump(self.scan_data, f, ensure_ascii=False, indent=2)
    
    def print_summary(self):
        """打印识别摘要"""
        print("\n" + "="*60)
        print("📊 识别完成摘要")
        print("="*60)
        print(f"总文件夹数: {self.stats['total']}")
        print(f"✓ 识别成功: {self.stats['identified']}")
        print(f"✗ 识别失败: {self.stats['failed']}")
        print(f"⏭ 跳过: {self.stats['skipped']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['identified'] / self.stats['total']) * 100
            print(f"\n识别率: {success_rate:.1f}%")
        
        print(f"\n更新的扫描文件: {self.scan_file}")
        print("="*60)
        
        print("\n📝 下一步操作：")
        print("1. 检查识别结果（查看 JSON 文件）")
        print("2. 手动修正识别错误的项")
        print(f"3. 运行处理脚本: python process.py --scan-file {self.scan_file.name}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量识别脚本 - 新工作流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 识别扫描文件
  python identify.py --scan-file scan_20231214_120000.json
  
  # 重新识别所有（包括已识别的）
  python identify.py --scan-file scan_20231214_120000.json --no-skip
  
  # 指定输出目录
  python identify.py --scan-file scan_20231214_120000.json --output my_output
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
        "--no-skip",
        action="store_true",
        help="不跳过已识别的项，重新识别所有"
    )
    
    parser.add_argument(
        "--no-auto-save",
        action="store_true",
        help="不自动保存，全部识别完成后再保存"
    )
    
    args = parser.parse_args()
    
    # 打印配置
    Config.print_config()
    
    # 创建识别器
    try:
        identifier = BatchIdentifier(args.scan_file, args.output)
    except ValueError as e:
        print(f"❌ {e}")
        return
    except RuntimeError as e:
        print(f"❌ {e}")
        return
    
    # 执行识别
    identifier.identify_all(
        skip_identified=not args.no_skip,
        auto_save=not args.no_auto_save
    )


if __name__ == "__main__":
    main()
