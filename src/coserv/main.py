"""
主程序
整合所有模块，实现完整的视频自动分类流程
"""

import sys
import argparse
from pathlib import Path
from tqdm import tqdm
import time

from .config import Config
from .frame_extractor import FrameExtractor
from .character_identifier import CharacterIdentifier
from .file_organizer import FileOrganizer


class VideoClassifier:
    """视频分类器主控制器"""
    
    def __init__(self, base_dir: str, dry_run: bool = False):
        """
        初始化分类器
        
        Args:
            base_dir: 视频所在目录
            dry_run: 是否为测试模式（不实际移动文件）
        """
        self.base_dir = Path(base_dir).resolve()
        self.dry_run = dry_run
        
        if not self.base_dir.exists():
            raise ValueError(f"目录不存在: {base_dir}")
        
        # 初始化各模块
        print("\n" + "="*60)
        print("🚀 初始化视频分类系统")
        print("="*60)
        
        self.frame_extractor = FrameExtractor()
        self.character_identifier = CharacterIdentifier()
        self.file_organizer = FileOrganizer(str(self.base_dir))
        
        if dry_run:
            print("\n⚠ 测试模式：不会实际移动文件")
        
        print("="*60 + "\n")
        
        # 统计数据
        self.stats = {
            "total": 0,
            "success": 0,
            "no_face": 0,
            "unknown": 0,
            "error": 0,
        }
    
    def process_single_video(self, video_path: str) -> bool:
        """
        处理单个视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            是否成功
        """
        video_path = Path(video_path).resolve()
        
        print(f"\n{'='*60}")
        print(f"📹 处理: {video_path.name}")
        print(f"{'='*60}")
        
        # 第一步：提取帧
        frames = self.frame_extractor.extract_best_frames(str(video_path))
        
        if not frames:
            print("  ⚠ 未提取到有效的人脸帧")
            self.stats["no_face"] += 1
            return False
        
        # 第二步：识别角色
        character_info = self.character_identifier.identify_from_frames(frames)
        
        if not character_info:
            print("  ⚠ 未能识别角色")
            self.stats["unknown"] += 1
            
            # 如果启用了未知分类，仍然组织文件
            if not self.dry_run:
                self.file_organizer.organize_video(str(video_path), None)
            
            return False
        
        # 第三步：组织文件
        if not self.dry_run:
            success = self.file_organizer.organize_video(str(video_path), character_info)
            if success:
                self.stats["success"] += 1
                return True
            else:
                self.stats["error"] += 1
                return False
        else:
            print(f"  [测试模式] 将移动到: {character_info['character']}({character_info['source']})")
            self.stats["success"] += 1
            return True
    
    def process_directory(self, recursive: bool = False, limit: int = None):
        """
        处理整个目录
        
        Args:
            recursive: 是否递归处理子目录
            limit: 限制处理的视频数量（用于测试）
        """
        # 获取所有视频文件
        videos = self.file_organizer.get_video_files(recursive=recursive)
        
        if not videos:
            print("❌ 未找到任何视频文件")
            return
        
        # 应用限制
        if limit:
            videos = videos[:limit]
            print(f"\n⚠ 限制模式：只处理前 {limit} 个视频\n")
        
        self.stats["total"] = len(videos)
        
        print(f"\n找到 {len(videos)} 个视频文件")
        print(f"开始处理...\n")
        
        # 使用进度条
        with tqdm(videos, desc="总进度", unit="视频") as pbar:
            for video in pbar:
                pbar.set_description(f"处理: {video.name[:30]}")
                
                try:
                    self.process_single_video(str(video))
                except Exception as e:
                    print(f"\n❌ 处理失败 {video.name}: {e}\n")
                    self.stats["error"] += 1
                
                # 更新进度条后缀
                pbar.set_postfix({
                    "成功": self.stats["success"],
                    "无人脸": self.stats["no_face"],
                    "未识别": self.stats["unknown"],
                    "错误": self.stats["error"]
                })
                
                # 短暂延迟，避免 API 请求过快
                time.sleep(0.5)
        
        # 打印最终统计
        self.print_statistics()
        
        # 打印文件组织摘要
        if not self.dry_run:
            self.file_organizer.print_summary()
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("📊 处理统计")
        print("="*60)
        print(f"总视频数: {self.stats['total']}")
        print(f"✓ 成功识别并分类: {self.stats['success']}")
        print(f"⚠ 未检测到人脸: {self.stats['no_face']}")
        print(f"⚠ 无法识别角色: {self.stats['unknown']}")
        print(f"❌ 处理错误: {self.stats['error']}")
        
        if self.stats["total"] > 0:
            success_rate = (self.stats["success"] / self.stats["total"]) * 100
            print(f"\n成功率: {success_rate:.1f}%")
        
        print("="*60 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频自动分类系统 - 让机器帮你整理 Coser 视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 处理指定目录（测试模式，不移动文件）
  python main.py /path/to/videos --dry-run
  
  # 实际运行，只处理前 5 个视频
  python main.py /path/to/videos --limit 5
  
  # 完整运行
  python main.py /path/to/videos
  
  # 递归处理所有子目录
  python main.py /path/to/videos --recursive
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="要处理的视频目录"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="测试模式：只识别，不移动文件"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="递归处理子目录"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的视频数量（用于测试）"
    )
    
    parser.add_argument(
        "--single",
        type=str,
        default=None,
        help="只处理单个视频文件"
    )
    
    args = parser.parse_args()
    
    # 验证配置
    Config.print_config()
    if not Config.validate():
        sys.exit(1)
    
    # 创建分类器
    try:
        classifier = VideoClassifier(args.directory, dry_run=args.dry_run)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 处理单个文件或整个目录
    if args.single:
        if not Path(args.single).exists():
            print(f"❌ 文件不存在: {args.single}")
            sys.exit(1)
        
        classifier.stats["total"] = 1
        classifier.process_single_video(args.single)
        classifier.print_statistics()
    else:
        classifier.process_directory(
            recursive=args.recursive,
            limit=args.limit
        )


if __name__ == "__main__":
    main()
