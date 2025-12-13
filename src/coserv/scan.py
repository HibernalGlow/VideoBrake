"""
扫描脚本 - 新工作流程第一步
1. 扫描指定目录下的所有文件夹
2. 为每个文件夹提取关键帧/图片
3. 生成一个带时间戳的 JSON 文件记录所有信息
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from tqdm import tqdm

from config import Config
from frame_extractor import FrameExtractor
from file_organizer import FileOrganizer

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


class FolderScanner:
    """文件夹扫描器"""
    
    def __init__(self, target_dir: str, output_dir: str = None, 
                 max_frames: int = 5, image_size_kb: int = 25, 
                 save_json: bool = True):
        """
        初始化扫描器
        
        Args:
            target_dir: 目标文件夹目录
            output_dir: 输出目录（默认为视频目录下的 coserv_output）
            max_frames: 每个文件夹提取的最大图片数量（默认 5）
            image_size_kb: 图片压缩目标大小（KB，默认 25）
            save_json: 是否保存 JSON 文件（默认 True）
        """
        self.target_dir = Path(target_dir).resolve()
        
        # 如果未指定输出目录，默认使用视频目录下的 coserv_output
        if output_dir is None:
            self.output_dir = self.target_dir / "coserv_output"
        else:
            self.output_dir = Path(output_dir).resolve()
        
        if not self.target_dir.exists():
            raise ValueError(f"目标目录不存在: {target_dir}")
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化模块
        self.frame_extractor = FrameExtractor()
        
        # 配置参数
        self.max_frames = max_frames
        self.image_size_kb = image_size_kb
        self.save_json = save_json
        
        # 生成时间戳
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 扫描结果
        self.scan_data = {
            "timestamp": self.timestamp,
            "target_dir": str(self.target_dir),
            "config": {
                "max_frames": max_frames,
                "image_size_kb": image_size_kb
            },
            "folders": []
        }
    
    def scan_all_folders(self, limit: int = None):
        """
        扫描所有文件夹
        
        Args:
            limit: 限制处理数量
        """
        # 获取所有子文件夹（只扫描一级子目录）
        folders = [f for f in self.target_dir.iterdir() if f.is_dir()]
        
        if not folders:
            print("❌ 未找到任何子文件夹")
            return
        
        if limit:
            folders = folders[:limit]
            print(f"\n⚠ 限制模式：只处理前 {limit} 个文件夹\n")
        
        print(f"\n找到 {len(folders)} 个文件夹")
        print(f"配置：每个文件夹最多提取 {self.max_frames} 张图片，目标大小 {self.image_size_kb}KB")
        print("开始扫描...")
        
        # 处理每个文件夹
        with tqdm(folders, desc="扫描进度", unit="文件夹") as pbar:
            for folder_path in pbar:
                pbar.set_description(f"扫描: {folder_path.name[:30]}")
                
                try:
                    self.scan_single_folder(folder_path)
                except Exception as e:
                    print(f"\n❌ 扫描失败 {folder_path.name}: {e}\n")
        
        # 保存扫描结果
        if self.save_json:
            self.save_scan_data()
        
        # 打印摘要
        self.print_summary()
    
    def scan_single_folder(self, folder_path: Path):
        """
        扫描单个文件夹
        
        Args:
            folder_path: 文件夹路径
        """
        folder_name = folder_path.name
        
        # 查找视频文件
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(list(folder_path.glob(f'*{ext}')))
            video_files.extend(list(folder_path.glob(f'*{ext.upper()}')))
        
        if not video_files:
            # 没有视频文件，跳过
            return
        
        # 创建帧输出目录
        frames_output_dir = self.output_dir / f"frames_{self.timestamp}" / folder_name
        frames_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取第一个视频的关键帧（作为文件夹代表）
        video_file = video_files[0]
        frames = self.frame_extractor.extract_best_frames(str(video_file))
        
        if not frames:
            return
        
        # 限制帧数量
        frames = frames[:self.max_frames]
        
        # 保存关键帧
        saved_frames = []
        for i, frame in enumerate(frames):
            frame_filename = f"frame_{i+1:02d}.webp"
            frame_path = frames_output_dir / frame_filename
            
            # 保存为 WebP 格式
            import cv2
            from PIL import Image
            import io
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # 压缩到目标大小
            quality = 80
            while quality > 10:
                buffer = io.BytesIO()
                pil_image.save(buffer, format='WEBP', quality=quality)
                size_kb = buffer.tell() / 1024
                
                if size_kb <= self.image_size_kb or quality <= 20:
                    with open(frame_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    break
                
                quality -= 10
            
            saved_frames.append(str(frame_path.relative_to(self.output_dir)))
        
        # 记录文件夹信息
        folder_info = {
            "folder_name": folder_name,
            "folder_path": str(folder_path),
            "video_count": len(video_files),
            "video_files": [str(vf.relative_to(self.target_dir)) for vf in video_files],
            "representative_video": str(video_file.relative_to(self.target_dir)),
            "frames": saved_frames,
            "frame_count": len(saved_frames),
            "status": "pending",  # pending, identified, skipped
            "character_info": None,  # 待 Gemini 填写
            "notes": ""
        }
        
        self.scan_data["folders"].append(folder_info)
    
    def save_scan_data(self):
        """保存扫描数据"""
        scan_file = self.output_dir / f"scan_{self.timestamp}.json"
        
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(self.scan_data, f, ensure_ascii=False, indent=2)
        
        if RICH_AVAILABLE:
            console.print(f"\n✓ 扫描数据已保存: [cyan]{scan_file}[/cyan]")
        else:
            print(f"\n✓ 扫描数据已保存: {scan_file}")
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "="*60)
        print("📊 扫描完成摘要")
        print("="*60)
        print(f"扫描文件夹数: {len(self.scan_data['folders'])}")
        
        total_videos = sum(f['video_count'] for f in self.scan_data['folders'])
        print(f"总视频文件数: {total_videos}")
        
        total_frames = sum(f['frame_count'] for f in self.scan_data['folders'])
        print(f"提取关键帧数: {total_frames}")
        
        if self.scan_data['folders']:
            avg_frames = total_frames / len(self.scan_data['folders'])
            print(f"平均每文件夹: {avg_frames:.1f} 帧")
        
        print(f"\n输出目录: {self.output_dir}")
        print(f"时间戳: {self.timestamp}")
        print("="*60)
        
        print("\n📝 下一步操作：")
        print(f"1. 运行识别脚本: python identify.py --scan-file scan_{self.timestamp}.json")
        print("2. 或手动编辑 JSON 文件填写角色信息")
        print(f"3. 运行处理脚本: python process.py --scan-file scan_{self.timestamp}.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文件夹扫描脚本 - 新工作流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 扫描目录
  python scan.py D:\\Videos\\Cosplay
  
  # 限制扫描数量
  python scan.py D:\\Videos\\Cosplay --limit 10
  
  # 指定输出目录
  python scan.py D:\\Videos\\Cosplay --output my_output
        """
    )
    
    parser.add_argument(
        "target_dir",
        type=str,
        help="目标文件夹目录路径"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出目录（默认: 视频目录/coserv_output）"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的文件夹数量"
    )
    
    parser.add_argument(
        "--max-frames",
        type=int,
        default=5,
        help="每个文件夹提取的最大图片数量（默认: 5）"
    )
    
    parser.add_argument(
        "--image-size",
        type=int,
        default=25,
        help="图片压缩目标大小（KB，默认: 25）"
    )
    
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="不保存 JSON 文件，只生成图片"
    )
    
    args = parser.parse_args()
    
    # 打印配置
    Config.print_config()
    
    # 创建扫描器
    try:
        scanner = FolderScanner(
            args.target_dir, 
            args.output,
            max_frames=args.max_frames,
            image_size_kb=args.image_size,
            save_json=not args.no_json
        )
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 执行扫描
    scanner.scan_all_folders(limit=args.limit)


if __name__ == "__main__":
    main()
