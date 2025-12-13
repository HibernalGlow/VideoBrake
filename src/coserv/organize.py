"""
后期整理脚本
1. 读取识别结果 (results.json)
2. 根据角色信息创建文件夹
3. 移动/复制视频文件
4. 生成整理报告
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List

from .config import Config
from .file_organizer import FileOrganizer


class VideoOrganizer:
    """视频整理器"""
    
    def __init__(self, video_dir: str, results_file: str = "output/results.json"):
        """
        初始化整理器
        
        Args:
            video_dir: 视频目录
            results_file: 识别结果文件
        """
        self.video_dir = Path(video_dir).resolve()
        self.results_file = Path(results_file).resolve()
        
        if not self.video_dir.exists():
            raise ValueError(f"视频目录不存在: {video_dir}")
        
        if not self.results_file.exists():
            raise ValueError(f"结果文件不存在: {results_file}")
        
        # 初始化文件组织器
        self.file_organizer = FileOrganizer(str(self.video_dir))
        
        # 加载识别结果
        self.results = self.load_results()
        
        # 统计
        self.stats = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "error": 0
        }
    
    def load_results(self) -> List[Dict]:
        """加载识别结果"""
        with open(self.results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"✓ 已加载 {len(results)} 条识别结果")
        return results
    
    def organize_all(self, dry_run: bool = False):
        """
        整理所有视频
        
        Args:
            dry_run: 是否为测试模式
        """
        if dry_run:
            print("\n⚠ 测试模式：不会实际移动文件\n")
        
        self.stats["total"] = len(self.results)
        
        print(f"\n开始整理 {len(self.results)} 个视频...\n")
        
        for result in self.results:
            try:
                self.organize_single_video(result, dry_run)
            except Exception as e:
                print(f"❌ 整理失败 {result.get('video_name', 'Unknown')}: {e}")
                self.stats["error"] += 1
        
        # 打印摘要
        self.print_summary()
        
        # 打印文件组织摘要
        if not dry_run:
            self.file_organizer.print_summary()
    
    def organize_single_video(self, result: Dict, dry_run: bool = False):
        """
        整理单个视频
        
        Args:
            result: 识别结果
            dry_run: 是否为测试模式
        """
        video_name = result['video_name']
        video_path = result['video_path']
        status = result.get('status', 'pending')
        
        print(f"\n📹 {video_name}")
        
        # 跳过未识别的视频
        if status == 'skipped':
            print(f"  ⏭ 跳过（用户标记）")
            self.stats["skipped"] += 1
            return
        
        # 获取角色信息
        character_info = result.get('character_info')
        
        if not character_info or status != 'identified':
            print(f"  ⚠ 未识别，移动到'未识别角色'文件夹")
            character_info = None
        else:
            print(f"  ✓ 识别为: {character_info['character']} ({character_info['source']})")
        
        # 整理文件
        if not dry_run:
            success = self.file_organizer.organize_video(video_path, character_info)
            if success:
                self.stats["success"] += 1
            else:
                self.stats["error"] += 1
        else:
            folder_name = self._get_folder_name(character_info)
            print(f"  [测试模式] 将移动到: {folder_name}")
            self.stats["success"] += 1
    
    def _get_folder_name(self, character_info: Dict = None) -> str:
        """获取目标文件夹名"""
        if character_info and character_info.get('character'):
            return self.file_organizer._sanitize_folder_name(
                character_info['character'],
                character_info.get('source', '')
            )
        else:
            return Config.UNKNOWN_FOLDER_NAME
    
    def print_summary(self):
        """打印整理摘要"""
        print("\n" + "="*60)
        print("📊 整理统计")
        print("="*60)
        print(f"总视频数: {self.stats['total']}")
        print(f"✓ 成功整理: {self.stats['success']}")
        print(f"⏭ 跳过: {self.stats['skipped']}")
        print(f"❌ 错误: {self.stats['error']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"\n整理率: {success_rate:.1f}%")
        
        print("="*60 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频文件整理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 整理视频（测试模式）
  python organize.py D:\\Videos\\Cosplay --dry-run
  
  # 正式整理
  python organize.py D:\\Videos\\Cosplay
  
  # 指定结果文件
  python organize.py D:\\Videos\\Cosplay --results my_results.json
        """
    )
    
    parser.add_argument(
        "video_dir",
        type=str,
        help="视频目录路径"
    )
    
    parser.add_argument(
        "--results",
        type=str,
        default="output/results.json",
        help="识别结果文件路径（默认: output/results.json）"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="测试模式：只显示，不移动文件"
    )
    
    args = parser.parse_args()
    
    # 打印配置
    Config.print_config()
    
    # 创建整理器
    try:
        organizer = VideoOrganizer(args.video_dir, args.results)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 执行整理
    organizer.organize_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
