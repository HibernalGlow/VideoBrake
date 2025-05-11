"""
视频格式过滤器模块

提供视频文件格式转换功能，包括添加/移除.nov后缀和检查重复项
"""

from .__main__ import (
    FormatFilter,
    main,
    process_videos,
    process_single_file,
    check_and_save_duplicates,
)

__version__ = '0.1.0'