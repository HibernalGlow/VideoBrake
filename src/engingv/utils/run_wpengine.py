#!/usr/bin/env python3
"""
Wallpaper Engine 工坊管理工具启动脚本
"""

import subprocess
import sys
from pathlib import Path
from loguru import logger

def main():
    """启动 Streamlit 应用"""
    app_path = Path(__file__).parent / "app.py"
    
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
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()
