"""
文件组织模块
负责创建文件夹和移动/复制视频文件
"""

import shutil
from pathlib import Path
from typing import Dict, Optional
import re

from config import Config


class FileOrganizer:
    """文件组织器"""
    
    def __init__(self, base_dir: str):
        """
        初始化组织器
        
        Args:
            base_dir: 基础目录（扫描视频的目录）
        """
        self.base_dir = Path(base_dir).resolve()
        
        if not self.base_dir.exists():
            raise ValueError(f"目录不存在: {base_dir}")
        
        print(f"✓ 文件组织器初始化完成")
        print(f"  基础目录: {self.base_dir}")
        print(f"  操作模式: {'移动' if Config.MOVE_FILES else '复制'}")
    
    def organize_video(
        self, 
        video_path: str, 
        character_info: Optional[Dict[str, str]]
    ) -> bool:
        """
        组织视频文件
        
        Args:
            video_path: 视频文件路径
            character_info: 角色信息字典，格式：{"character": "...", "source": "..."}
            
        Returns:
            是否成功
        """
        video_path = Path(video_path).resolve()
        
        # 确定目标文件夹名
        if character_info and character_info.get("character"):
            folder_name = self._sanitize_folder_name(
                character_info["character"],
                character_info.get("source", "")
            )
        else:
            folder_name = Config.UNKNOWN_FOLDER_NAME
        
        # 创建目标文件夹
        target_dir = self.base_dir / folder_name
        target_dir.mkdir(exist_ok=True)
        
        # 目标文件路径
        target_path = target_dir / video_path.name
        
        # 处理文件名冲突
        if target_path.exists():
            target_path = self._get_unique_path(target_path)
        
        # 移动或复制文件
        try:
            if Config.MOVE_FILES:
                shutil.move(str(video_path), str(target_path))
                action = "移动"
            else:
                shutil.copy2(str(video_path), str(target_path))
                action = "复制"
            
            print(f"  ✓ 已{action}到: {folder_name}/{target_path.name}")
            return True
            
        except Exception as e:
            print(f"  ❌ 文件操作失败: {e}")
            return False
    
    @staticmethod
    def _sanitize_folder_name(character: str, source: str = "") -> str:
        """
        清理文件夹名，移除非法字符
        
        Args:
            character: 角色名
            source: 作品名
            
        Returns:
            清理后的文件夹名
        """
        # 组合角色名和作品名
        if source and source != "未知":
            folder_name = f"{character}({source})"
        else:
            folder_name = character
        
        # 移除 Windows 文件夹名非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        folder_name = re.sub(illegal_chars, '_', folder_name)
        
        # 移除首尾空格和点
        folder_name = folder_name.strip(' .')
        
        # 限制长度
        max_length = 100
        if len(folder_name) > max_length:
            folder_name = folder_name[:max_length]
        
        return folder_name
    
    @staticmethod
    def _get_unique_path(path: Path) -> Path:
        """
        生成唯一的文件路径（处理重名）
        
        Args:
            path: 原始路径
            
        Returns:
            唯一路径
        """
        if not path.exists():
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def get_video_files(self, recursive: bool = False) -> list:
        """
        获取基础目录下所有视频文件
        
        Args:
            recursive: 是否递归搜索子目录
            
        Returns:
            视频文件路径列表
        """
        video_files = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in self.base_dir.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in Config.SUPPORTED_VIDEO_FORMATS:
                video_files.append(file_path)
        
        return video_files
    
    def create_backup(self, video_path: str) -> Optional[Path]:
        """
        创建视频文件的备份
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            备份文件路径，失败返回 None
        """
        video_path = Path(video_path)
        backup_dir = self.base_dir / ".backup"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / video_path.name
        backup_path = self._get_unique_path(backup_path)
        
        try:
            shutil.copy2(str(video_path), str(backup_path))
            return backup_path
        except Exception as e:
            print(f"  ⚠ 备份失败: {e}")
            return None
    
    def print_summary(self):
        """打印组织结果摘要"""
        print("\n" + "="*60)
        print("📊 文件组织摘要")
        print("="*60)
        
        # 统计各文件夹中的视频数量
        folders = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name != ".backup"]
        
        for folder in sorted(folders):
            video_count = sum(
                1 for f in folder.iterdir() 
                if f.is_file() and f.suffix.lower() in Config.SUPPORTED_VIDEO_FORMATS
            )
            print(f"  📁 {folder.name}: {video_count} 个视频")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python file_organizer.py <目录路径>")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    
    organizer = FileOrganizer(base_dir)
    
    # 列出所有视频
    videos = organizer.get_video_files(recursive=False)
    print(f"\n找到 {len(videos)} 个视频文件:")
    for video in videos[:10]:  # 只显示前10个
        print(f"  - {video.name}")
    
    if len(videos) > 10:
        print(f"  ... 还有 {len(videos) - 10} 个视频")
    
    # 测试文件夹名清理
    test_names = [
        ("优菈", "原神"),
        ("2B小姐姐", "尼尔:自动人形"),
        ("Test/Name:Invalid", ""),
    ]
    
    print("\n文件夹名清理测试:")
    for char, source in test_names:
        cleaned = organizer._sanitize_folder_name(char, source)
        print(f"  {char} ({source}) -> {cleaned}")
