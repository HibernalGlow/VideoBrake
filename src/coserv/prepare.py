"""
前期准备脚本
1. 扫描视频文件
2. 智能提取关键帧（场景检测+人脸过滤+去重）
3. 保存帧到输出目录
4. 生成待识别清单
"""

import json
import argparse
import io
from pathlib import Path
from tqdm import tqdm
import shutil

from config import Config
from frame_extractor import FrameExtractor
from file_organizer import FileOrganizer


class VideoPreparer:
    """视频准备器"""
    
    def __init__(self, video_dir: str, output_dir: str = "output"):
        """
        初始化准备器
        
        Args:
            video_dir: 视频目录
            output_dir: 输出目录
        """
        self.video_dir = Path(video_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        
        if not self.video_dir.exists():
            raise ValueError(f"视频目录不存在: {video_dir}")
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化模块
        self.frame_extractor = FrameExtractor()
        self.file_organizer = FileOrganizer(str(self.video_dir))
        
        # 待识别清单
        self.pending_list = []
    
    def prepare_all(self, limit: int = None):
        """
        准备所有视频
        
        Args:
            limit: 限制处理数量
        """
        # 获取所有视频
        videos = self.file_organizer.get_video_files(recursive=False)
        
        if not videos:
            print("❌ 未找到任何视频文件")
            return
        
        if limit:
            videos = videos[:limit]
            print(f"\n⚠ 限制模式：只处理前 {limit} 个视频\n")
        
        print(f"\n找到 {len(videos)} 个视频文件")
        print("开始提取关键帧...\n")
        
        # 处理每个视频
        with tqdm(videos, desc="总进度", unit="视频") as pbar:
            for video_path in pbar:
                pbar.set_description(f"处理: {video_path.name[:30]}")
                
                try:
                    self.prepare_single_video(video_path)
                except Exception as e:
                    print(f"\n❌ 处理失败 {video_path.name}: {e}\n")
        
        # 保存待识别清单
        self.save_pending_list()
        
        # 打印摘要
        self.print_summary()
    
    def prepare_single_video(self, video_path: Path):
        """
        准备单个视频
        
        Args:
            video_path: 视频文件路径
        """
        # 创建视频专属目录
        video_name = video_path.stem
        video_output_dir = self.output_dir / video_name
        frames_dir = video_output_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取关键帧
        frames = self.frame_extractor.extract_best_frames(str(video_path))
        
        if not frames:
            print(f"  ⚠ {video_path.name}: 未提取到有效帧")
            return
        
        # 保存所有帧
        saved_frames = []
        for i, frame in enumerate(frames):
            frame_path = frames_dir / f"frame_{i+1:02d}.webp"
            
            # 转换为RGB（webp需要）
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            from PIL import Image
            pil_image = Image.fromarray(rgb_frame)
            
            # 压缩到目标大小（25KB）
            quality = 80
            while quality > 10:
                buffer = io.BytesIO()
                pil_image.save(buffer, format='WEBP', quality=quality)
                size_kb = buffer.tell() / 1024
                
                if size_kb <= 25 or quality <= 20:
                    # 保存到文件
                    with open(frame_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    break
                
                quality -= 10
            
            saved_frames.append(str(frame_path.relative_to(self.output_dir)))
        
        # 添加到待识别清单
        self.pending_list.append({
            "video_name": video_name,
            "video_path": str(video_path),
            "frames_dir": str(frames_dir.relative_to(self.output_dir)),
            "frames": saved_frames,
            "frame_count": len(saved_frames),
            "status": "pending"  # pending, identified, skipped
        })
        
        print(f"  ✓ {video_path.name}: 提取了 {len(frames)} 个关键帧")
    
    def save_pending_list(self):
        """保存待识别清单"""
        pending_file = self.output_dir / "pending.json"
        
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump(self.pending_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 待识别清单已保存: {pending_file}")
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "="*60)
        print("📊 准备完成摘要")
        print("="*60)
        print(f"总视频数: {len(self.pending_list)}")
        
        total_frames = sum(item['frame_count'] for item in self.pending_list)
        print(f"总关键帧数: {total_frames}")
        
        if self.pending_list:
            avg_frames = total_frames / len(self.pending_list)
            print(f"平均每视频: {avg_frames:.1f} 帧")
        
        print(f"\n输出目录: {self.output_dir}")
        print("="*60)
        
        print("\n📝 下一步操作：")
        print("1. 打开 Gemini CLI 交互式界面")
        print("2. 查看提取的关键帧（在 output/视频名/frames/ 目录）")
        print("3. 识别角色后，创建 output/results.json 文件")
        print("4. 运行 organize.py 完成文件整理")
        print("\n💡 提示：可以使用以下命令启动 Gemini CLI：")
        print(f"   cd {self.output_dir}")
        print("   gemini")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频关键帧提取脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 处理视频目录
  python prepare.py D:\\Videos\\Cosplay
  
  # 限制处理数量
  python prepare.py D:\\Videos\\Cosplay --limit 5
  
  # 指定输出目录
  python prepare.py D:\\Videos\\Cosplay --output my_output
        """
    )
    
    parser.add_argument(
        "video_dir",
        type=str,
        help="视频目录路径"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="输出目录（默认: output）"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的视频数量"
    )
    
    args = parser.parse_args()
    
    # 打印配置
    Config.print_config()
    
    # 创建准备器
    try:
        preparer = VideoPreparer(args.video_dir, args.output)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 执行准备
    preparer.prepare_all(limit=args.limit)


if __name__ == "__main__":
    main()
