"""
文件夹重命名工具
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from engingv.core.models import WallpaperFolder
from engingv.utils.config import get_config

from loguru import logger


class FolderRenamer:
    """文件夹重命名工具"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.rename_log: List[Dict[str, str]] = []
    
    def rename_folders(self, wallpapers: List[WallpaperFolder], 
                      name_template: str, 
                      target_base_dir: Optional[str] = None) -> List[Dict[str, str]]:
        """
        重命名文件夹
        
        Args:
            wallpapers: 壁纸列表
            name_template: 命名模板，如 "[#{id}]{original_name}+{title}"
            target_base_dir: 目标基础目录，如果为None则在原位置重命名
        
        Returns:
            重命名记录列表
        """
        rename_results = []

        # 读取配置中的长度限制
        cfg = get_config()
        desc_len = cfg.get("rename_settings.description_max_length", 18)
        name_len = cfg.get("rename_settings.name_max_length", 120)

        for wallpaper in wallpapers:
            try:
                new_name = wallpaper.generate_new_name(
                    name_template,
                    description_max_length=desc_len,
                    name_max_length=name_len,
                )
                old_path = wallpaper.path

                if target_base_dir:
                    # 移动到目标目录
                    target_dir = Path(target_base_dir)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    new_path = target_dir / new_name
                else:
                    # 在原位置重命名
                    new_path = old_path.parent / new_name

                # 避免重复命名
                if new_path.exists() and new_path != old_path:
                    counter = 1
                    base_name = new_name
                    while new_path.exists():
                        new_name = f"{base_name}_{counter}"
                        if target_base_dir:
                            new_path = Path(target_base_dir) / new_name
                        else:
                            new_path = old_path.parent / new_name
                        counter += 1

                rename_record = {
                    "workshop_id": wallpaper.workshop_id,
                    "title": wallpaper.title,
                    "old_path": str(old_path),
                    "new_path": str(new_path),
                    "old_name": wallpaper.folder_name,
                    "new_name": new_name,
                    "status": "planned",
                }

                if not self.dry_run:
                    if target_base_dir:
                        # 复制文件夹
                        shutil.copytree(old_path, new_path, dirs_exist_ok=True)
                        rename_record["status"] = "copied"
                        logger.info(f"已复制: {old_path} -> {new_path}")
                    else:
                        # 重命名文件夹
                        old_path.rename(new_path)
                        rename_record["status"] = "renamed"
                        logger.info(f"已重命名: {old_path} -> {new_path}")
                else:
                    logger.info(f"预览模式: {old_path} -> {new_path}")

                rename_results.append(rename_record)

            except Exception as e:
                error_record = {
                    "workshop_id": wallpaper.workshop_id,
                    "title": wallpaper.title,
                    "old_path": str(wallpaper.path),
                    "new_path": "",
                    "old_name": wallpaper.folder_name,
                    "new_name": "",
                    "status": "error",
                    "error": str(e),
                }
                rename_results.append(error_record)
                logger.error(f"重命名失败 {wallpaper.path}: {e}")

        self.rename_log.extend(rename_results)
        return rename_results
    
    def export_rename_log(self, output_file: str = "rename_log.json") -> None:
        """导出重命名日志"""
        import json
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.rename_log, f, ensure_ascii=False, indent=2)
        
        logger.info(f"重命名日志已导出到 {output_file}")
    
    def validate_template(self, template: str) -> List[str]:
        """验证命名模板"""
        valid_placeholders = ["{id}", "{title}", "{original_name}", "{type}", "{rating}", "{desc}"]
        issues = []
        
        # 检查是否包含非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in template:
                issues.append(f"模板包含非法字符: {char}")
        
        # 检查占位符
        used_placeholders = []
        for placeholder in valid_placeholders:
            if placeholder in template:
                used_placeholders.append(placeholder)
        
        if not used_placeholders:
            issues.append("模板中没有使用任何占位符")

        # 提示未识别的 {xxx}
        import re
        for m in re.findall(r"\{[^}]+\}", template):
            if m not in valid_placeholders:
                issues.append(f"未识别的占位符: {m}")
        
        return issues
