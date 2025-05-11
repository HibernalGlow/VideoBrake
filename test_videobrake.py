#!/usr/bin/env python3
"""
brakev 测试脚本

测试主包可以正确导入并调用子包的功能
"""

import os
import sys
import importlib
import argparse
from typing import List

# 测试模块列表
TEST_MODULES = [
    'brakev',
    'brakev.cli',
    'brakev.interactive',
    'bitv',
    'bitv.__main__',
    'formatv',
    'formatv.__main__',
]

def test_imports() -> List[str]:
    """
    测试所有模块是否可以正常导入
    
    Returns:
        List[str]: 导入失败的模块列表
    """
    print("测试模块导入...")
    failed_modules = []
    
    for module_name in TEST_MODULES:
        try:
            print(f"  导入 {module_name}...", end="")
            module = importlib.import_module(module_name)
            print(" 成功")
        except Exception as e:
            print(f" 失败: {str(e)}")
            failed_modules.append(module_name)
    
    return failed_modules

def test_interactive_entry():
    """测试交互式入口点"""
    print("\n测试交互式入口点...")
    
    try:
        from brakev.__main__ import main
        # 这里不实际运行main()函数，因为它会启动交互式界面
        print(f"  导入主入口点函数 main 成功")
    except Exception as e:
        print(f"  导入主入口点函数失败: {str(e)}")
        return False
    
    return True

def test_cli_entry():
    """测试命令行入口点"""
    print("\n测试命令行入口点...")
    
    try:
        from brakev.cli import app
        print(f"  导入命令行入口点 app 成功")
    except Exception as e:
        print(f"  导入命令行入口点失败: {str(e)}")
        return False
    
    return True
    
def test_formatv_functions():
    """测试formatv包的功能"""
    print("\n测试formatv包的功能...")
    
    try:
        from formatv.__main__ import add_nov_extension, remove_nov_extension, interactive_main
        print(f"  导入add_nov_extension, remove_nov_extension, interactive_main 成功")
    except Exception as e:
        print(f"  导入formatv函数失败: {str(e)}")
        return False
    
    return True

def test_bitv_functions():
    """测试bitv包的功能"""
    print("\n测试bitv包的功能...")
    
    try:
        from bitv.__main__ import analyze_file, analyze_dir, interactive_main
        print(f"  导入analyze_file, analyze_dir, interactive_main 成功")
    except Exception as e:
        print(f"  导入bitv函数失败: {str(e)}")
        return False
    
    return True

def main():
    """主函数"""
    print("brakev 功能测试\n")
    
    # 测试导入
    failed_modules = test_imports()
    
    if failed_modules:
        print(f"\n警告: 以下模块导入失败: {', '.join(failed_modules)}")
    else:
        print("\n模块导入测试通过!")
    
    # 测试入口点
    cli_ok = test_cli_entry()
    interactive_ok = test_interactive_entry()
    formatv_ok = test_formatv_functions()
    bitv_ok = test_bitv_functions()
    
    # 汇总测试结果
    print("\n测试结果汇总:")
    print(f"  模块导入测试: {'通过' if not failed_modules else '失败'}")
    print(f"  命令行入口点测试: {'通过' if cli_ok else '失败'}")
    print(f"  交互式入口点测试: {'通过' if interactive_ok else '失败'}")
    print(f"  formatv功能测试: {'通过' if formatv_ok else '失败'}")
    print(f"  bitv功能测试: {'通过' if bitv_ok else '失败'}")
    
    # 整体结果
    all_passed = (not failed_modules and cli_ok and interactive_ok and formatv_ok and bitv_ok)
    print(f"\n整体测试结果: {'通过' if all_passed else '失败'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
