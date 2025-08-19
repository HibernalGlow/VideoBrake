"""
Streamlit 应用主程序 - 简化版
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from engingv.core.scanner import WorkshopScanner
from engingv.core.models import WallpaperFolder
from engingv.utils.config import get_config
from engingv.ui.ui_components import (
    display_wallpaper_grid, 
    display_wallpaper_checkbox_view, 
    create_filter_interface,
    create_display_controls,
    create_statistics_view,
    create_export_buttons,
    format_file_size
)
from engingv.ui.rename_ui import create_rename_interface


def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="Wallpaper Engine 工坊管理工具",
        page_icon="🖼️",
        layout="wide"
    )


def create_sidebar(config) -> tuple[str, int, bool]:
    """创建侧边栏"""
    with st.sidebar:
        st.header("配置")
        
        # 工坊路径配置
        workshop_path = st.text_input(
            "工坊目录路径",
            value=config.get("workshop_path", ""),
            help="Wallpaper Engine 工坊目录路径"
        )
        
        # 保存路径到配置
        if workshop_path != config.get("workshop_path", ""):
            config.set("workshop_path", workshop_path)
            if workshop_path:
                config.add_recent_path(workshop_path)
        
        # 最近使用的路径
        recent_paths = config.get("recent_paths", [])
        if recent_paths:
            st.subheader("最近使用的路径")
            selected_recent = st.selectbox(
                "选择最近使用的路径",
                [""] + recent_paths,
                index=0
            )
            if selected_recent:
                config.set("workshop_path", selected_recent)
                st.rerun()
        
        # 扫描配置
        max_workers = st.slider("并发线程数", 1, 8, config.get("max_workers", 4))
        if max_workers != config.get("max_workers"):
            config.set("max_workers", max_workers)
        
        # 扫描按钮
        scan_button = st.button("🔍 扫描工坊目录", type="primary")
        
        return workshop_path, max_workers, scan_button


def initialize_session_state():
    """初始化会话状态"""
    if "scanner" not in st.session_state:
        st.session_state.scanner = None
    if "wallpapers" not in st.session_state:
        st.session_state.wallpapers = []
    if "filtered_wallpapers" not in st.session_state:
        st.session_state.filtered_wallpapers = []
    if "selected_wallpapers" not in st.session_state:
        st.session_state.selected_wallpapers = set()


def scan_workshop_directory(workshop_path: str, max_workers: int) -> bool:
    """扫描工坊目录"""
    if not workshop_path:
        st.info("请在侧边栏设置工坊目录路径")
        return False
    
    if not Path(workshop_path).exists():
        st.error(f"目录不存在: {workshop_path}")
        return False
    
    with st.spinner("正在扫描工坊目录..."):
        try:
            scanner = WorkshopScanner(workshop_path)
            wallpapers = scanner.scan_workshop(max_workers=max_workers)
            st.session_state.scanner = scanner
            st.session_state.wallpapers = wallpapers
            st.session_state.filtered_wallpapers = wallpapers
            st.success(f"扫描完成！找到 {len(wallpapers)} 个壁纸")
            return True
        except Exception as e:
            st.error(f"扫描失败: {e}")
            return False


def create_browse_tab():
    """创建浏览与过滤标签页"""
    st.header("浏览与过滤")
    
    if not st.session_state.wallpapers:
        st.info("没有找到壁纸，请检查目录路径或重新扫描")
        return
    
    # 过滤器界面
    st.subheader("🔍 过滤条件")
    filters = create_filter_interface(st.session_state.scanner, st.session_state.wallpapers)
    
    # 执行过滤
    if filters:
        filtered_wallpapers = st.session_state.scanner.filter_wallpapers(filters)
    else:
        filtered_wallpapers = st.session_state.wallpapers
    
    st.session_state.filtered_wallpapers = filtered_wallpapers
    
    # 显示统计
    st.write(f"显示 {len(filtered_wallpapers)} / {len(st.session_state.wallpapers)} 个壁纸")
    
    # 导出按钮
    create_export_buttons(st.session_state.scanner, filtered_wallpapers)
    
    # 显示控制
    display_mode = create_display_controls(filtered_wallpapers)
    
    # 显示内容
    if not filtered_wallpapers:
        st.info("没有符合条件的壁纸")
        return
    
    if display_mode == "网格视图":
        display_wallpaper_grid(filtered_wallpapers)
    elif display_mode == "勾选视图":
        display_wallpaper_checkbox_view(filtered_wallpapers)
    else:  # 列表视图
        create_list_view(filtered_wallpapers)


def create_list_view(wallpapers: List[WallpaperFolder]):
    """创建列表视图"""
    data = []
    for wp in wallpapers:
        data.append({
            "ID": wp.workshop_id,
            "标题": wp.title,
            "类型": wp.wallpaper_type,
            "内容评级": wp.content_rating,
            "标签": ", ".join(wp.tags),
            "大小": format_file_size(wp.size),
            "修改时间": wp.modified_time.strftime('%Y-%m-%d %H:%M'),
            "路径": str(wp.path)
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


def main():
    """主程序"""
    setup_page_config()
    st.title("🖼️ Wallpaper Engine 工坊管理工具")
    
    # 加载配置
    config = get_config()
    
    # 初始化会话状态
    initialize_session_state()
    
    # 侧边栏
    workshop_path, max_workers, scan_button = create_sidebar(config)
    
    # 执行扫描
    if scan_button or st.session_state.scanner is None:
        if workshop_path:
            scan_workshop_directory(workshop_path, max_workers)
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📋 浏览与过滤", "📁 重命名工具", "📊 统计信息"])
    
    with tab1:
        create_browse_tab()
    
    with tab2:
        st.header("重命名工具")
        create_rename_interface(st.session_state.filtered_wallpapers)
    
    with tab3:
        st.header("统计信息")
        create_statistics_view(st.session_state.wallpapers)


if __name__ == "__main__":
    main()
