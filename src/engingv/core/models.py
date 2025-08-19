"""
Wallpaper Engine 工坊壁纸数据模型
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

from loguru import logger



@dataclass
class WallpaperFolder:
    """壁纸文件夹对象"""
    path: Path
    folder_name: str
    workshop_id: str
    project_data: Dict[str, Any]
    created_time: datetime
    modified_time: datetime
    size: int
    
    # Project.json 中的常用字段
    title: str = ""
    description: str = ""
    content_rating: str = ""
    rating_sex: str = ""
    rating_violence: str = ""
    tags: List[str] = None
    file_name: str = ""
    preview: str = ""
    wallpaper_type: str = ""
    
    def __post_init__(self):
        """初始化后处理，从 project_data 中提取字段"""
        if self.tags is None:
            self.tags = []
            
        # 从 project.json 中提取数据
        self.title = self.project_data.get("title", "")
        self.description = self.project_data.get("description", "")
        self.content_rating = self.project_data.get("contentrating", "")
        self.rating_sex = self.project_data.get("ratingsex", "")
        self.rating_violence = self.project_data.get("ratingviolence", "")
        self.tags = self.project_data.get("tags", [])
        self.file_name = self.project_data.get("file", "")
        self.preview = self.project_data.get("preview", "")
        self.wallpaper_type = self.project_data.get("type", "")
    
    @property
    def preview_path(self) -> Optional[Path]:
        """获取预览文件的完整路径"""
        if self.preview:
            preview_path = self.path / self.preview
            if preview_path.exists():
                return preview_path
        return None
    
    @property
    def main_file_path(self) -> Optional[Path]:
        """获取主文件的完整路径"""
        if self.file_name:
            main_file_path = self.path / self.file_name
            if main_file_path.exists():
                return main_file_path
        
            return None
    
    def matches_filter(self, filters: Dict[str, Any]) -> bool:
        """检查是否匹配过滤条件"""
        for key, value in filters.items():
            if not value:  # 空值跳过
                continue
                
            if key == "title" and value.lower() not in self.title.lower():
                return False
            elif key == "contentrating" and self.content_rating != value:
                return False
            elif key == "tags" and not any(tag in self.tags for tag in value):
                return False
            elif key == "type" and self.wallpaper_type != value:
                return False
            elif key == "ratingsex" and self.rating_sex != value:
                return False
            elif key == "ratingviolence" and self.rating_violence != value:
                return False
                
        return True
    
    def generate_new_name(self, template: str, description_max_length: int = 18, name_max_length: int = 120) -> str:
        """根据模板生成新的文件夹名称

        Args:
            template: 模板字符串
            description_max_length: 描述截断长度
            name_max_length: 最终名称最大长度（超出将截断保留后缀）
        """
        # 处理描述截断
        desc_clean = (self.description or '').strip().replace('\n', ' ').replace('\r', ' ')
        if description_max_length > 0 and len(desc_clean) > description_max_length:
            desc_clean = desc_clean[:description_max_length] + '…'

        replacements = {
            "{id}": self.workshop_id,
            "{title}": self.title,
            "{original_name}": self.folder_name,
            "{type}": self.wallpaper_type,
            "{rating}": self.content_rating,
            "{desc}": desc_clean,
        }

        new_name = template
        for placeholder, value in replacements.items():
            new_name = new_name.replace(placeholder, str(value))

        # 清理文件名中的非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            new_name = new_name.replace(char, "_")

        # 去掉首尾空格与重复空格
        new_name = ' '.join(new_name.split())

        # 限制总长度，保留结尾的id信息（如果包含 #id 或 原始id）
        if name_max_length > 0 and len(new_name) > name_max_length:
            # 尝试保留 #[id]
            suffix = ''
            if f"#{self.workshop_id}" in new_name:
                suffix = new_name[new_name.rfind(f"#{self.workshop_id}") : ]
            elif self.workshop_id and new_name.endswith(self.workshop_id):
                suffix = self.workshop_id
            available = name_max_length - len(suffix) - 1 if suffix else name_max_length
            if available > 3:
                new_name = new_name[:available - 1] + '…' + ((' ' + suffix) if suffix else '')
            else:
                new_name = new_name[:name_max_length]

        return new_name
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "path": str(self.path),
            "folder_name": self.folder_name,
            "workshop_id": self.workshop_id,
            "title": self.title,
            "description": self.description,
            "content_rating": self.content_rating,
            "rating_sex": self.rating_sex,
            "rating_violence": self.rating_violence,
            "tags": self.tags,
            "file_name": self.file_name,
            "preview": self.preview,
            "wallpaper_type": self.wallpaper_type,
            "created_time": self.created_time.isoformat(),
            "modified_time": self.modified_time.isoformat(),
            "size": self.size,
        }


def load_project_json(project_path: Path) -> Optional[Dict[str, Any]]:
    """加载 project.json 文件"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"无法加载 {project_path}: {e}")
        return None


def get_folder_stats(folder_path: Path) -> tuple[datetime, datetime, int]:
    """获取文件夹统计信息"""
    try:
        stat = folder_path.stat()
        created_time = datetime.fromtimestamp(stat.st_ctime)
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        
        # 计算文件夹大小
        total_size = 0
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, PermissionError):
                    continue
                    
        return created_time, modified_time, total_size
    except (OSError, PermissionError) as e:
        logger.error(f"无法获取文件夹统计信息 {folder_path}: {e}")
        return datetime.now(), datetime.now(), 0


def create_wallpaper_folder(folder_path: Path) -> Optional[WallpaperFolder]:
    """从文件夹路径创建 WallpaperFolder 对象"""
    project_json_path = folder_path / "project.json"
    
    if not project_json_path.exists():
        logger.warning(f"未找到 project.json: {project_json_path}")
        return None
    
    project_data = load_project_json(project_json_path)
    if not project_data:
        return None
    
    created_time, modified_time, size = get_folder_stats(folder_path)
    folder_name = folder_path.name
    
    # 从路径中提取 workshop ID（通常是文件夹名的数字部分）
    workshop_id = folder_name
    
    return WallpaperFolder(
        path=folder_path,
        folder_name=folder_name,
        workshop_id=workshop_id,
        project_data=project_data,
        created_time=created_time,
        modified_time=modified_time,
        size=size
    )
