"""
快速截图模块
使用随机采样 + 去重，速度最快
"""

import cv2
import numpy as np
import random
from PIL import Image
import imagehash
from pathlib import Path
from typing import List

from config import Config


class FrameExtractor:
    """快速帧提取器"""
    
    def __init__(self):
        """初始化提取器"""
        print("✓ 快速帧提取器初始化完成")
    
    def extract_best_frames(
        self, 
        video_path: str, 
        max_frames: int = None
    ) -> List[np.ndarray]:
        """
        快速提取视频帧（随机采样）
        
        Args:
            video_path: 视频文件路径
            max_frames: 最多提取的帧数
            
        Returns:
            帧数组列表 (BGR 格式)
        """
        if max_frames is None:
            max_frames = Config.MAX_FRAMES_PER_VIDEO
        
        print(f"🎬 处理: {Path(video_path).name}")
        
        # 随机采样
        sampled_frames = self._random_sample(video_path, max_frames * 3)
        
        if not sampled_frames:
            print("  ❌ 未能提取帧")
            return []
        
        print(f"  ✓ 采样: {len(sampled_frames)} 帧")
        
        # 去重
        unique_frames = self._deduplicate_frames(sampled_frames, max_frames)
        print(f"  ✓ 去重后: {len(unique_frames)} 帧")
        
        return unique_frames
    
    def _random_sample(self, video_path: str, num_frames: int) -> List[np.ndarray]:
        """
        随机采样视频帧
        
        Args:
            video_path: 视频路径
            num_frames: 采样数量
            
        Returns:
            帧列表
        """
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            cap.release()
            return []
        
        # 生成随机帧位置（跳过前10%和后10%，避免片头片尾）
        start_frame = int(total_frames * 0.1)
        end_frame = int(total_frames * 0.9)
        
        if end_frame <= start_frame:
            start_frame = 0
            end_frame = total_frames
        
        # 随机选择帧位置
        frame_positions = random.sample(
            range(start_frame, end_frame),
            min(num_frames, end_frame - start_frame)
        )
        frame_positions.sort()  # 排序以顺序读取，提高效率
        
        frames = []
        for frame_num in frame_positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # 可选：缩放以节省内存
                if Config.PROCESS_IMAGE_WIDTH:
                    frame = self._resize_frame(frame, Config.PROCESS_IMAGE_WIDTH)
                frames.append(frame)
        
        cap.release()
        return frames
    
    def _deduplicate_frames(
        self, 
        frames: List[np.ndarray], 
        max_frames: int
    ) -> List[np.ndarray]:
        """
        使用感知哈希去除相似帧
        
        Args:
            frames: 输入帧列表
            max_frames: 最大保留数量
            
        Returns:
            去重后的帧列表
        """
        if not frames:
            return []
        
        # 计算所有帧的感知哈希
        hashes = []
        for frame in frames:
            # 转换为 PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            # 计算感知哈希
            img_hash = imagehash.phash(pil_image)
            hashes.append((img_hash, frame))
        
        # 去重逻辑
        unique_frames = []
        unique_hashes = []
        
        for img_hash, frame in hashes:
            # 检查是否与已有哈希过于相似
            is_unique = True
            for existing_hash in unique_hashes:
                if img_hash - existing_hash < Config.HASH_DIFF_THRESHOLD:
                    is_unique = False
                    break
            
            if is_unique:
                unique_frames.append(frame)
                unique_hashes.append(img_hash)
                
                # 达到最大数量
                if len(unique_frames) >= max_frames:
                    break
        
        return unique_frames
    
    @staticmethod
    def _resize_frame(frame: np.ndarray, target_width: int) -> np.ndarray:
        """
        等比例缩放帧
        
        Args:
            frame: 输入帧
            target_width: 目标宽度
            
        Returns:
            缩放后的帧
        """
        h, w = frame.shape[:2]
        if w <= target_width:
            return frame
        
        aspect_ratio = h / w
        new_height = int(target_width * aspect_ratio)
        return cv2.resize(frame, (target_width, new_height), interpolation=cv2.INTER_AREA)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python frame_extractor.py <视频路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    extractor = FrameExtractor()
    frames = extractor.extract_best_frames(video_path, max_frames=5)
    
    # 保存测试帧
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    for i, frame in enumerate(frames):
        output_path = output_dir / f"frame_{i+1}.jpg"
        cv2.imwrite(str(output_path), frame)
        print(f"已保存: {output_path}")
    
    print(f"\n✓ 测试完成，共提取 {len(frames)} 帧")

