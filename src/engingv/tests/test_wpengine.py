"""
Wallpaper Engine 工坊管理工具测试
"""

import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from engingv.core.models import WallpaperFolder, create_wallpaper_folder, load_project_json
from engingv.core.scanner import WorkshopScanner
from engingv.core.renamer import FolderRenamer


class TestWallpaperModels(unittest.TestCase):
    """测试壁纸模型"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_project_data = {
            "title": "Test Wallpaper",
            "description": "Test Description",
            "contentrating": "Everyone",
            "ratingsex": "none",
            "ratingviolence": "none",
            "tags": ["Test", "Demo"],
            "file": "test.mp4",
            "preview": "preview.gif",
            "type": "Video"
        }
    
    def test_wallpaper_folder_creation(self):
        """测试壁纸文件夹对象创建"""
        folder = WallpaperFolder(
            path=Path("/test/path"),
            folder_name="test_folder",
            workshop_id="123456",
            project_data=self.test_project_data,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            size=1024
        )
        
        self.assertEqual(folder.title, "Test Wallpaper")
        self.assertEqual(folder.content_rating, "Everyone")
        self.assertEqual(folder.tags, ["Test", "Demo"])
    
    def test_name_template_generation(self):
        """测试名称模板生成"""
        folder = WallpaperFolder(
            path=Path("/test/path"),
            folder_name="original_name",
            workshop_id="123456",
            project_data=self.test_project_data,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            size=1024
        )
        
        template = "[#{id}]{original_name}+{title}"
        new_name = folder.generate_new_name(template)
        expected = "[#123456]original_name+Test Wallpaper"
        self.assertEqual(new_name, expected)
    
    def test_filter_matching(self):
        """测试过滤匹配"""
        folder = WallpaperFolder(
            path=Path("/test/path"),
            folder_name="test_folder",
            workshop_id="123456",
            project_data=self.test_project_data,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            size=1024
        )
        
        # 匹配的过滤器
        filters = {"contentrating": "Everyone", "type": "Video"}
        self.assertTrue(folder.matches_filter(filters))
        
        # 不匹配的过滤器
        filters = {"contentrating": "Mature"}
        self.assertFalse(folder.matches_filter(filters))


class TestFolderRenamer(unittest.TestCase):
    """测试文件夹重命名器"""
    
    def test_template_validation(self):
        """测试模板验证"""
        renamer = FolderRenamer(dry_run=True)
        
        # 有效模板
        valid_template = "{title}_{id}"
        issues = renamer.validate_template(valid_template)
        self.assertEqual(len(issues), 0)
        
        # 包含非法字符的模板
        invalid_template = "{title}/<{id}>"
        issues = renamer.validate_template(invalid_template)
        self.assertGreater(len(issues), 0)
        
        # 没有占位符的模板
        no_placeholder_template = "static_name"
        issues = renamer.validate_template(no_placeholder_template)
        self.assertGreater(len(issues), 0)


class TestProjectJsonLoading(unittest.TestCase):
    """测试 project.json 加载"""
    
    def test_load_valid_json(self):
        """测试加载有效的 JSON 文件"""
        test_data = {
            "title": "Test",
            "contentrating": "Everyone",
            "type": "Video"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            loaded_data = load_project_json(Path(temp_path))
            self.assertIsNotNone(loaded_data)
            self.assertEqual(loaded_data["title"], "Test")
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_json(self):
        """测试加载无效的 JSON 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            loaded_data = load_project_json(Path(temp_path))
            self.assertIsNone(loaded_data)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
