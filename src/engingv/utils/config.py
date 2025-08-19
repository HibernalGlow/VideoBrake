"""
配置管理模块
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = "wallpaper_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "workshop_path": "",
    "name_template": "[#{id}]{original_name}+{title}",
    "max_workers": 4,
    "recent_paths": [],
    # 重命名相关设置
    "rename_settings": {
        "description_max_length": 18,  # 描述截断长度
        "name_max_length": 120         # 最终文件夹名最大长度
    },
    "display_settings": {
        "items_per_page": 20,
    "default_view": "grid",
    "grid_columns": 3,
    "description_font_size": 12,
    "grid_selectable": True
    },
    "export_settings": {
        "include_metadata": True,
        "export_format": "json"
    },
    "templates": {
        "标准格式": "[#{id}]{original_name}+{title}",
        "简洁格式": "{title}_{id}",
        "类型分类": "{type}_{rating}_{title}",
    "自定义": "{title}",
    "含描述简洁": "{title}_{desc}_{id}",
    "含描述标准": "[#{id}]{title}+{desc}",
    "描述优先": "{desc}_{title}_{id}"
    }
}


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置，确保所有字段都存在
                merged_config = DEFAULT_CONFIG.copy()
                self._deep_merge(merged_config, config)
                return merged_config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.info(f"使用默认配置: {e}")
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> None:
        """保存配置"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到 {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        self.save_config()
    
    def add_recent_path(self, path: str) -> None:
        """添加最近使用的路径"""
        recent_paths = self.get("recent_paths", [])
        
        # 移除重复项
        if path in recent_paths:
            recent_paths.remove(path)
        
        # 添加到开头
        recent_paths.insert(0, path)
        
        # 只保留最近5个
        recent_paths = recent_paths[:5]
        
        self.set("recent_paths", recent_paths)
    
    def get_templates(self) -> Dict[str, str]:
        """获取命名模板"""
        return self.get("templates", {})
    
    def add_template(self, name: str, template: str) -> None:
        """添加命名模板"""
        templates = self.get_templates()
        templates[name] = template
        self.set("templates", templates)
    
    def remove_template(self, name: str) -> None:
        """删除命名模板"""
        templates = self.get_templates()
        if name in templates:
            del templates[name]
            self.set("templates", templates)
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
    
    def export_config(self, file_path: str) -> None:
        """导出配置"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已导出到 {file_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证配置结构
            if not isinstance(imported_config, dict):
                logger.error("无效的配置文件格式")
                return False
            
            # 合并配置
            merged_config = DEFAULT_CONFIG.copy()
            self._deep_merge(merged_config, imported_config)
            
            self.config = merged_config
            self.save_config()
            
            logger.info(f"配置已从 {file_path} 导入")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager
