"""
Streamlit UI 组件模块
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.models import WallpaperFolder


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def display_wallpaper_grid(wallpapers: List[WallpaperFolder]) -> None:
    """显示壁纸网格"""
    cols = st.columns(3)
    
    for i, wallpaper in enumerate(wallpapers):
        with cols[i % 3]:
            st.subheader(wallpaper.title or "无标题")
            
            # 显示预览图
            if wallpaper.preview_path and wallpaper.preview_path.exists():
                try:
                    st.image(str(wallpaper.preview_path), use_container_width=True)
                except Exception as e:
                    st.error(f"无法显示预览图: {e}")
            else:
                st.info("无预览图")
            
            # 显示基本信息
            st.write(f"**ID:** {wallpaper.workshop_id}")
            st.write(f"**类型:** {wallpaper.wallpaper_type}")
            st.write(f"**内容评级:** {wallpaper.content_rating}")
            st.write(f"**大小:** {format_file_size(wallpaper.size)}")
            st.write(f"**修改时间:** {wallpaper.modified_time.strftime('%Y-%m-%d %H:%M')}")
            
            if wallpaper.tags:
                st.write(f"**标签:** {', '.join(wallpaper.tags)}")
            
            if wallpaper.description:
                with st.expander("描述"):
                    st.write(wallpaper.description)


def display_wallpaper_checkbox_view(wallpapers: List[WallpaperFolder]) -> None:
    """显示带勾选框的壁纸视图"""
    st.write(f"已选择 {len(st.session_state.selected_wallpapers)} 个壁纸")
    
    # 分页设置
    items_per_page = 20
    total_pages = (len(wallpapers) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("选择页面", range(1, total_pages + 1)) - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(wallpapers))
    page_wallpapers = wallpapers[start_idx:end_idx]
    
    # 显示当前页的壁纸
    for wallpaper in page_wallpapers:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 7])
            
            with col1:
                # 勾选框
                is_selected = wallpaper.workshop_id in st.session_state.selected_wallpapers
                selected = st.checkbox(
                    "",
                    value=is_selected,
                    key=f"checkbox_{wallpaper.workshop_id}",
                    label_visibility="collapsed"
                )
                
                if selected and not is_selected:
                    st.session_state.selected_wallpapers.add(wallpaper.workshop_id)
                    st.rerun()
                elif not selected and is_selected:
                    st.session_state.selected_wallpapers.discard(wallpaper.workshop_id)
                    st.rerun()
            
            with col2:
                # 预览图（缩略图）
                if wallpaper.preview_path and wallpaper.preview_path.exists():
                    try:
                        st.image(str(wallpaper.preview_path), width=120)
                    except Exception as e:
                        st.error("预览失败")
                else:
                    st.info("无预览")
            
            with col3:
                # 详细信息
                st.markdown(f"**{wallpaper.title or '无标题'}**")
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.write(f"ID: {wallpaper.workshop_id}")
                    st.write(f"类型: {wallpaper.wallpaper_type}")
                    st.write(f"评级: {wallpaper.content_rating}")
                
                with info_col2:
                    st.write(f"大小: {format_file_size(wallpaper.size)}")
                    st.write(f"修改: {wallpaper.modified_time.strftime('%Y-%m-%d %H:%M')}")
                    if wallpaper.tags:
                        st.write(f"标签: {', '.join(wallpaper.tags[:3])}{'...' if len(wallpaper.tags) > 3 else ''}")
            
            st.divider()
    
    # 批量操作按钮
    if st.session_state.selected_wallpapers:
        st.subheader("批量操作")
        selected_count = len(st.session_state.selected_wallpapers)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"📄 导出选中的 {selected_count} 个路径"):
                selected_wallpapers = [wp for wp in wallpapers if wp.workshop_id in st.session_state.selected_wallpapers]
                output_file = f"selected_wallpaper_paths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    for wp in selected_wallpapers:
                        f.write(str(wp.path) + '\n')
                
                st.success(f"已导出 {len(selected_wallpapers)} 个路径到 {output_file}")
        
        with col2:
            if st.button(f"📋 导出选中的 {selected_count} 个JSON"):
                selected_wallpapers = [wp for wp in wallpapers if wp.workshop_id in st.session_state.selected_wallpapers]
                output_file = f"selected_wallpapers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                data = [wp.to_dict() for wp in selected_wallpapers]
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                st.success(f"已导出 {len(selected_wallpapers)} 个壁纸信息到 {output_file}")
        
        with col3:
            if st.button(f"🗑️ 清空选择"):
                st.session_state.selected_wallpapers = set()
                st.rerun()


def create_filter_interface(scanner, wallpapers: List[WallpaperFolder]) -> Dict[str, Any]:
    """创建过滤器界面"""
    filters = {}
    
    # 基本过滤
    with st.expander("基本过滤", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 标题搜索
            title_filter = st.text_input("搜索标题", "")
            if title_filter:
                filters["title"] = title_filter
            
            # 内容评级过滤
            content_ratings = scanner.get_unique_values("contentrating")
            selected_rating = st.selectbox("内容评级", ["全部"] + content_ratings)
            if selected_rating != "全部":
                filters["contentrating"] = selected_rating
            
        with col2:
            # 类型过滤
            types = scanner.get_unique_values("type")
            selected_type = st.selectbox("壁纸类型", ["全部"] + types)
            if selected_type != "全部":
                filters["type"] = selected_type
            
            # 性内容评级
            sex_ratings = scanner.get_unique_values("ratingsex")
            selected_sex_rating = st.selectbox("性内容评级", ["全部"] + sex_ratings)
            if selected_sex_rating != "全部":
                filters["ratingsex"] = selected_sex_rating
            
        with col3:
            # 暴力内容评级
            violence_ratings = scanner.get_unique_values("ratingviolence")
            selected_violence_rating = st.selectbox("暴力内容评级", ["全部"] + violence_ratings)
            if selected_violence_rating != "全部":
                filters["ratingviolence"] = selected_violence_rating
            
            # 标签过滤
            all_tags = scanner.get_unique_values("tags")
            selected_tags = st.multiselect("标签", all_tags)
            if selected_tags:
                filters["tags"] = selected_tags
    
    # 高级过滤
    with st.expander("高级过滤", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 时间过滤
            st.subheader("📅 时间范围")
            enable_date_filter = st.checkbox("启用时间过滤")
            
            if enable_date_filter:
                # 获取时间范围
                min_date = min(wp.modified_time.date() for wp in wallpapers)
                max_date = max(wp.modified_time.date() for wp in wallpapers)
                
                date_range = st.date_input(
                    "选择时间范围",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    help="选择壁纸修改时间的范围"
                )
                
                if len(date_range) == 2:
                    filters["date_range"] = date_range
        
        with col2:
            # 大小过滤
            st.subheader("📦 文件大小")
            enable_size_filter = st.checkbox("启用大小过滤")
            
            if enable_size_filter:
                # 获取大小范围（以MB为单位）
                min_size_mb = min(wp.size for wp in wallpapers) / (1024 * 1024)
                max_size_mb = max(wp.size for wp in wallpapers) / (1024 * 1024)
                
                size_range_mb = st.slider(
                    "文件大小范围 (MB)",
                    min_value=float(min_size_mb),
                    max_value=float(max_size_mb),
                    value=[float(min_size_mb), float(max_size_mb)],
                    step=0.1,
                    help="选择文件大小范围"
                )
                # 转换为字节
                filters["size_range"] = [size_range_mb[0] * 1024 * 1024, size_range_mb[1] * 1024 * 1024]
    
    return filters


def create_display_controls(filtered_wallpapers: List[WallpaperFolder]) -> str:
    """创建显示控制界面"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        display_mode = st.radio("显示模式", ["网格视图", "列表视图", "勾选视图"], horizontal=True)
    
    # 初始化选中状态
    if "selected_wallpapers" not in st.session_state:
        st.session_state.selected_wallpapers = set()
    
    if display_mode == "勾选视图":
        with col2:
            if st.button("全选"):
                st.session_state.selected_wallpapers.update(wp.workshop_id for wp in filtered_wallpapers)
                st.rerun()
        
        with col3:
            if st.button("取消全选"):
                st.session_state.selected_wallpapers = set()
                st.rerun()
    
    return display_mode


def create_statistics_view(wallpapers: List[WallpaperFolder]) -> None:
    """创建统计视图"""
    if not wallpapers:
        st.info("请先扫描工坊目录")
        return
    
    # 基本统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总数量", len(wallpapers))
    
    with col2:
        total_size = sum(wp.size for wp in wallpapers)
        st.metric("总大小", format_file_size(total_size))
    
    with col3:
        types = [wp.wallpaper_type for wp in wallpapers if wp.wallpaper_type]
        st.metric("类型数量", len(set(types)))
    
    with col4:
        ratings = [wp.content_rating for wp in wallpapers if wp.content_rating]
        st.metric("评级数量", len(set(ratings)))
    
    # 图表统计
    col1, col2 = st.columns(2)
    
    with col1:
        # 类型分布
        if types:
            type_counts = pd.Series(types).value_counts()
            st.subheader("类型分布")
            st.bar_chart(type_counts)
    
    with col2:
        # 评级分布
        if ratings:
            rating_counts = pd.Series(ratings).value_counts()
            st.subheader("内容评级分布")
            st.bar_chart(rating_counts)
    
    # 标签云
    all_tags = []
    for wp in wallpapers:
        all_tags.extend(wp.tags)
    
    if all_tags:
        tag_counts = pd.Series(all_tags).value_counts().head(20)
        st.subheader("热门标签 (前20)")
        st.bar_chart(tag_counts)


def create_export_buttons(scanner, filtered_wallpapers: List[WallpaperFolder]) -> None:
    """创建导出按钮"""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 导出路径列表"):
            output_file = f"wallpaper_paths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            scanner.export_filtered_paths(filtered_wallpapers, output_file)
            st.success(f"已导出到 {output_file}")
    
    with col2:
        if st.button("📋 导出JSON数据"):
            output_file = f"wallpapers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scanner.export_filtered_json(filtered_wallpapers, output_file)
            st.success(f"已导出到 {output_file}")
