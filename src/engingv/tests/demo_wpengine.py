"""
Wallpaper Engine 工具快速演示
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

# 创建演示数据
def create_demo_data():
    """创建演示用的工坊数据"""
    demo_dir = Path("demo_workshop")
    demo_dir.mkdir(exist_ok=True)
    
    # 创建几个演示壁纸文件夹
    demo_wallpapers = [
        {
            "id": "123456789",
            "data": {
                "title": "Beautiful Anime Landscape",
                "description": "A stunning anime landscape wallpaper",
                "contentrating": "Everyone",
                "ratingsex": "none",
                "ratingviolence": "none",
                "tags": ["Anime", "Landscape", "Nature"],
                "file": "wallpaper.mp4",
                "preview": "preview.gif",
                "type": "Video"
            }
        },
        {
            "id": "987654321",
            "data": {
                "title": "Cyberpunk City",
                "description": "Futuristic cyberpunk cityscape",
                "contentrating": "Mature",
                "ratingsex": "mild",
                "ratingviolence": "mild",
                "tags": ["Cyberpunk", "City", "Futuristic"],
                "file": "scene.html",
                "preview": "preview.jpg",
                "type": "Web"
            }
        },
        {
            "id": "555666777",
            "data": {
                "title": "Peaceful Forest",
                "description": "Calm forest scene with gentle rain",
                "contentrating": "Everyone",
                "ratingsex": "none",
                "ratingviolence": "none",
                "tags": ["Nature", "Forest", "Rain"],
                "file": "forest.mp4",
                "preview": "preview.gif",
                "type": "Video"
            }
        }
    ]
    
    for wallpaper in demo_wallpapers:
        folder_path = demo_dir / wallpaper["id"]
        folder_path.mkdir(exist_ok=True)
        
        # 创建 project.json
        project_file = folder_path / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(wallpaper["data"], f, ensure_ascii=False, indent=2)
        
        # 创建一个虚拟的预览文件
        preview_file = folder_path / wallpaper["data"]["preview"]
        preview_file.touch()
        
        # 创建一个虚拟的主文件
        main_file = folder_path / wallpaper["data"]["file"]
        main_file.touch()
    
    print(f"演示数据已创建在: {demo_dir.absolute()}")
    return demo_dir

def test_scanner():
    """测试扫描功能"""
    print("=== 测试扫描功能 ===")
    
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from engingv.core.scanner import WorkshopScanner
    
    demo_dir = create_demo_data()
    
    try:
        scanner = WorkshopScanner(str(demo_dir))
        wallpapers = scanner.scan_workshop()
        
        print(f"扫描到 {len(wallpapers)} 个壁纸:")
        for wp in wallpapers:
            print(f"  - {wp.title} ({wp.workshop_id}) - {wp.wallpaper_type}")
        
        # 测试过滤
        print("\n=== 测试过滤功能 ===")
        video_filters = {"type": "Video"}
        video_wallpapers = scanner.filter_wallpapers(video_filters)
        print(f"Video 类型壁纸: {len(video_wallpapers)} 个")
        
        # 测试获取唯一值
        print("\n=== 测试统计功能 ===")
        types = scanner.get_unique_values("type")
        ratings = scanner.get_unique_values("contentrating")
        tags = scanner.get_unique_values("tags")
        
        print(f"类型: {types}")
        print(f"评级: {ratings}")
        print(f"标签: {tags}")
        
    finally:
        # 清理演示数据
        import shutil
        shutil.rmtree(demo_dir, ignore_errors=True)

def test_renamer():
    """测试重命名功能"""
    print("\n=== 测试重命名功能 ===")
    
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from engingv.core.scanner import WorkshopScanner
    from engingv.core.renamer import FolderRenamer
    
    demo_dir = create_demo_data()
    
    try:
        scanner = WorkshopScanner(str(demo_dir))
        wallpapers = scanner.scan_workshop()
        
        renamer = FolderRenamer(dry_run=True)
        
        # 测试不同的命名模板
        templates = [
            "[#{id}]{original_name}+{title}",
            "{title}_{id}",
            "{type}_{rating}_{title}"
        ]
        
        for template in templates:
            print(f"\n模板: {template}")
            issues = renamer.validate_template(template)
            if issues:
                print(f"  问题: {issues}")
            else:
                print("  ✓ 模板有效")
                
                # 显示重命名预览
                for wp in wallpapers[:2]:  # 只显示前2个
                    new_name = wp.generate_new_name(template)
                    print(f"  {wp.folder_name} → {new_name}")
        
    finally:
        # 清理演示数据
        import shutil
        shutil.rmtree(demo_dir, ignore_errors=True)

def main():
    """主演示函数"""
    print("🖼️  Wallpaper Engine 工坊管理工具演示")
    print("=" * 50)
    
    try:
        test_scanner()
        test_renamer()
        print("\n✅ 所有测试完成！")
        print("\n启动 Web 界面:")
        print("  python -m engingv")
        print("或者:")
        print("  streamlit run src/engingv/app_simple.py")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
