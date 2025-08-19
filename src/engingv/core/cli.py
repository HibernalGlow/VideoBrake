"""
Wallpaper Engine 工坊管理工具 - CLI 入口
"""

import argparse
import sys
import subprocess
import socket
from pathlib import Path
from loguru import logger

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def start_streamlit(port: int | None = None, auto: bool = True):
    """启动 Streamlit 应用

    Args:
        port: 指定端口；None 则依据 auto 选择
        auto: True 时自动寻找空闲端口
    """
    app_path = Path(__file__).parent / "app_simple.py"

    if port is None and auto:
        port = _find_free_port()
    elif port is None:
        # 不指定端口，交由默认 8501；可能冲突
        pass

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    if port is not None:
        cmd += ["--server.port", str(port)]
    cmd += ["--server.address", "localhost"]

    show_port = port if port is not None else "(auto/default)"
    print("启动 Wallpaper Engine 工坊管理工具...")
    print(f"使用端口: {show_port}")
    if port is not None:
        print(f"访问地址: http://localhost:{port}")
    else:
        print("若 8501 被占用，Streamlit 将尝试其它端口。")

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
    
    parser.add_argument("--version", "-v", action="version", version="%(prog)s 1.0.0")
    parser.add_argument("--port", type=int, help="指定端口；不指定则自动找空闲端口")
    parser.add_argument("--no-auto-port", action="store_true", help="禁用自动找端口")
    
    args = parser.parse_args()
    
    if args.scan:
        scan_workshop(args.scan, args.output)
    else:
        start_streamlit(port=args.port, auto=not args.no_auto_port and args.port is None)

if __name__ == "__main__":
    main()
