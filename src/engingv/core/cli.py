"""
Wallpaper Engine 工坊管理工具 - CLI 入口
"""

import argparse
import sys
import subprocess
from pathlib import Path
from loguru import logger

def start_streamlit():
    """启动 Streamlit 应用"""
    app_path = Path(__file__).parent / "app_simple.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ]
    
    print("启动 Wallpaper Engine 工坊管理工具...")
    print(f"访问地址: http://localhost:8501")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n程序已停止")
    except FileNotFoundError:
        print("错误: 未找到 streamlit，请先安装: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

def scan_workshop(workshop_path: str, output_file: str = None):
    """扫描工坊目录"""
    from engingv.core.scanner import WorkshopScanner
    
    try:
        scanner = WorkshopScanner(workshop_path)
        wallpapers = scanner.scan_workshop()
        
        print(f"扫描完成！找到 {len(wallpapers)} 个壁纸")
        
        if output_file:
            scanner.export_filtered_json(wallpapers, output_file)
            print(f"结果已导出到: {output_file}")
        
        # 显示基本统计
        types = {}
        ratings = {}
        
        for wp in wallpapers:
            if wp.wallpaper_type:
                types[wp.wallpaper_type] = types.get(wp.wallpaper_type, 0) + 1
            if wp.content_rating:
                ratings[wp.content_rating] = ratings.get(wp.content_rating, 0) + 1
        
        print("\n类型分布:")
        for type_name, count in sorted(types.items()):
            print(f"  {type_name}: {count}")
        
        print("\n内容评级分布:")
        for rating, count in sorted(ratings.items()):
            print(f"  {rating}: {count}")
            
    except FileNotFoundError:
        print(f"错误: 工坊目录不存在: {workshop_path}")
        sys.exit(1)
    except Exception as e:
        print(f"扫描失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Wallpaper Engine 工坊管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  engingv                                    # 启动 Web 界面
  engingv --gui                              # 启动 Web 界面
  engingv --scan "C:\\Steam\\steamapps\\workshop\\content\\431960"  # 扫描工坊目录
  engingv --scan "path" --output "result.json"  # 扫描并导出结果
        """
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true",
        help="启动 Streamlit Web 界面（默认行为）"
    )
    
    parser.add_argument(
        "--scan",
        metavar="PATH",
        help="扫描指定的工坊目录"
    )
    
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="指定输出文件（与 --scan 一起使用）"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    args = parser.parse_args()
    
    if args.scan:
        scan_workshop(args.scan, args.output)
    else:
        # 默认启动 GUI
        start_streamlit()

if __name__ == "__main__":
    main()
