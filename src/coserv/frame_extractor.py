"""
智能截图模块
实现三重过滤机制：
1. 场景检测 - 提取不同机位的画面
2. 人脸检测 - 过滤无人脸的画面
3. 视觉去重 - 剔除相似画面
"""

import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import imagehash
from pathlib import Path
from typing import List, Tuple, Optional
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from config import Config


class FrameExtractor:
    """智能帧提取器"""
    
    def __init__(self):
        """初始化检测器"""
        # 初始化 MediaPipe 人脸检测
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0=近距离模型, 1=远距离模型
            min_detection_confidence=Config.FACE_DETECTION_CONFIDENCE
        )
        
        print("✓ 人脸检测器初始化完成")
    
    def extract_best_frames(
        self, 
        video_path: str, 
        max_frames: int = None
    ) -> List[np.ndarray]:
        """
        提取视频中最佳的帧
        
        Args:
            video_path: 视频文件路径
            max_frames: 最多提取的帧数
            
        Returns:
            帧数组列表 (BGR 格式)
        """
        if max_frames is None:
            max_frames = Config.MAX_FRAMES_PER_VIDEO
        
        print(f"\n🎬 开始处理视频: {Path(video_path).name}")
        
        # 第一步：场景检测
        scene_frames = self._detect_scenes(video_path)
        if not scene_frames:
            print("  ⚠ 未检测到场景，使用均匀采样")
            scene_frames = self._uniform_sample(video_path, max_frames * 2)
        
        print(f"  ✓ 场景检测完成，获得 {len(scene_frames)} 个候选帧")
        
        # 第二步：人脸过滤
        face_frames = self._filter_by_face(scene_frames)
        print(f"  ✓ 人脸过滤完成，保留 {len(face_frames)} 个有人脸的帧")
        
        if not face_frames:
            print("  ⚠ 未检测到人脸，返回空列表")
            return []
        
        # 第三步：视觉去重
        unique_frames = self._deduplicate_frames(face_frames, max_frames)
        print(f"  ✓ 去重完成，最终保留 {len(unique_frames)} 个帧")
        
        return unique_frames
    
    def _detect_scenes(self, video_path: str) -> List[np.ndarray]:
        """
        使用 PySceneDetect 检测场景切换点
        
        Returns:
            场景关键帧列表
        """
        try:
            # 初始化视频管理器
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()
            
            # 添加内容检测器
            scene_manager.add_detector(
                ContentDetector(threshold=Config.SCENE_THRESHOLD)
            )
            
            # 开始检测
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            
            # 获取场景列表
            scene_list = scene_manager.get_scene_list()
            
            # 打开视频以读取帧
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            frames = []
            for i, (start_time, end_time) in enumerate(scene_list):
                # 计算场景长度
                scene_duration = (end_time - start_time).get_seconds()
                
                # 跳过太短的场景
                if scene_duration < Config.MIN_SCENE_LENGTH:
                    continue
                
                # 从场景中间提取帧
                mid_time = start_time + (end_time - start_time) / 2
                frame_num = int(mid_time.get_frames())
                
                # 读取帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    # 可选：缩放以加速处理
                    if Config.PROCESS_IMAGE_WIDTH:
                        frame = self._resize_frame(frame, Config.PROCESS_IMAGE_WIDTH)
                    frames.append(frame)
            
            cap.release()
            video_manager.release()
            
            return frames
            
        except Exception as e:
            print(f"  ⚠ 场景检测失败: {e}")
            return []
    
    def _uniform_sample(self, video_path: str, num_frames: int) -> List[np.ndarray]:
        """
        均匀采样视频帧（备用方案）
        
        Args:
            video_path: 视频路径
            num_frames: 采样数量
            
        Returns:
            帧列表
        """
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算采样间隔
        interval = max(1, total_frames // num_frames)
        
        frames = []
        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                if Config.PROCESS_IMAGE_WIDTH:
                    frame = self._resize_frame(frame, Config.PROCESS_IMAGE_WIDTH)
                frames.append(frame)
                
            if len(frames) >= num_frames:
                break
        
        cap.release()
        return frames
    
    def _filter_by_face(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """
        过滤出包含人脸的帧
        
        Args:
            frames: 输入帧列表
            
        Returns:
            包含人脸的帧列表
        """
        face_frames = []
        
        for frame in frames:
            # 转换为 RGB（MediaPipe 需要）
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 检测人脸
            results = self.face_detection.process(rgb_frame)
            
            if results.detections:
                # 检查人脸大小
                has_valid_face = False
                h, w = frame.shape[:2]
                
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    face_width = bbox.width
                    
                    # 人脸宽度占图像的比例
                    if face_width >= Config.MIN_FACE_SIZE_RATIO:
                        has_valid_face = True
                        break
                
                if has_valid_face:
                    face_frames.append(frame)
        
        return face_frames
    
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
    
    @staticmethod
    def frame_to_bytes(frame: np.ndarray, quality: int = None) -> bytes:
        """
        将帧转换为 JPEG 字节
        
        Args:
            frame: BGR 格式的帧
            quality: JPEG 质量 (1-100)
            
        Returns:
            JPEG 字节数据
        """
        if quality is None:
            quality = Config.UPLOAD_IMAGE_QUALITY
        
        # 编码为 JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()


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
