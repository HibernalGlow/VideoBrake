"""
Wallpaper Engine 工坊扫描器
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from engingv.core.models import WallpaperFolder, create_wallpaper_folder

from loguru import logger


class WorkshopScanner:
    """工坊目录扫描器"""
    
    def __init__(self, workshop_path: str):
        self.workshop_path = Path(workshop_path)
        self.wallpapers: List[WallpaperFolder] = []
        
    def scan_workshop(self, max_workers: int = 4) -> List[WallpaperFolder]:
        """扫描工坊目录，返回壁纸列表"""
        if not self.workshop_path.exists():
            raise FileNotFoundError(f"工坊目录不存在: {self.workshop_path}")
            
        logger.info(f"开始扫描工坊目录: {self.workshop_path}")
        
        # 获取所有子目录
        subdirs = [d for d in self.workshop_path.iterdir() 
                  if d.is_dir() and (d / "project.json").exists()]
        
        logger.info(f"找到 {len(subdirs)} 个包含 project.json 的目录")
        
        wallpapers = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(create_wallpaper_folder, subdir): subdir 
                for subdir in subdirs
            }
            
            for future in as_completed(future_to_path):
                subdir = future_to_path[future]
                try:
                    wallpaper = future.result()
                    if wallpaper:
                        wallpapers.append(wallpaper)
                        logger.debug(f"成功加载: {wallpaper.title}")
                    else:
                        logger.warning(f"跳过无效目录: {subdir}")
                except Exception as e:
                    logger.error(f"处理目录 {subdir} 时出错: {e}")
        
        self.wallpapers = wallpapers
        logger.info(f"扫描完成，共加载 {len(wallpapers)} 个壁纸")
        return wallpapers
    
    def filter_wallpapers(self, filters: Dict[str, Any]) -> List[WallpaperFolder]:
        """根据过滤条件筛选壁纸"""
        filtered = []
        for wallpaper in self.wallpapers:
            if wallpaper.matches_filter(filters):
                filtered.append(wallpaper)
        
        logger.info(f"过滤后剩余 {len(filtered)} 个壁纸")
        return filtered
    
    def get_unique_values(self, field: str) -> List[str]:
        """获取指定字段的所有唯一值"""
        values = set()
        for wallpaper in self.wallpapers:
            if field == "contentrating":
                if wallpaper.content_rating:
                    values.add(wallpaper.content_rating)
            elif field == "type":
                if wallpaper.wallpaper_type:
                    values.add(wallpaper.wallpaper_type)
            elif field == "ratingsex":
                if wallpaper.rating_sex:
                    values.add(wallpaper.rating_sex)
            elif field == "ratingviolence":
                if wallpaper.rating_violence:
                    values.add(wallpaper.rating_violence)
            elif field == "tags":
                values.update(wallpaper.tags)
        
        return sorted(list(values))
    
    def export_filtered_paths(self, filtered_wallpapers: List[WallpaperFolder], 
                            output_file: str = "wallpaper_paths.txt") -> None:
        """导出过滤后的壁纸路径"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for wallpaper in filtered_wallpapers:
                f.write(str(wallpaper.path) + '\n')
        
        logger.info(f"已导出 {len(filtered_wallpapers)} 个路径到 {output_file}")
    
    def export_filtered_json(self, filtered_wallpapers: List[WallpaperFolder], 
                           output_file: str = "wallpapers.json") -> None:
        """导出过滤后的壁纸信息为JSON"""
        data = [wallpaper.to_dict() for wallpaper in filtered_wallpapers]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 {len(filtered_wallpapers)} 个壁纸信息到 {output_file}")


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"无法加载配置文件 {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """保存配置文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到 {config_path}")
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
