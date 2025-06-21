"""
Streamlit 应用主程序
"""

import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .scanner import WorkshopScanner, load_config, save_config
from .models import WallpaperFolder
from .renamer import FolderRenamer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = "wallpaper_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "workshop_path": "",
    "name_template": "[#{id}]{original_name}+{title}",
    "max_workers": 4,
    "recent_paths": []
}


def load_app_config() -> Dict[str, Any]:
    """加载应用配置"""
    config = load_config(CONFIG_FILE)
    if not config:
        config = DEFAULT_CONFIG.copy()
        save_config(config, CONFIG_FILE)
    return config


def save_app_config(config: Dict[str, Any]) -> None:
    """保存应用配置"""
    save_config(config, CONFIG_FILE)


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
                    st.image(str(wallpaper.preview_path), use_column_width=True)
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


def main():
    """主程序"""
    st.set_page_config(
        page_title="Wallpaper Engine 工坊管理工具",
        page_icon="🖼️",
        layout="wide"
    )
    
    st.title("🖼️ Wallpaper Engine 工坊管理工具")
    
    # 加载配置
    config = load_app_config()
    
    # 侧边栏配置
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
            config["workshop_path"] = workshop_path
            # 添加到最近使用路径
            recent_paths = config.get("recent_paths", [])
            if workshop_path and workshop_path not in recent_paths:
                recent_paths.insert(0, workshop_path)
                recent_paths = recent_paths[:5]  # 只保留最近5个
                config["recent_paths"] = recent_paths
            save_app_config(config)
        
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
                config["workshop_path"] = selected_recent
                save_app_config(config)
                st.rerun()
        
        # 扫描配置
        max_workers = st.slider("并发线程数", 1, 8, config.get("max_workers", 4))
        config["max_workers"] = max_workers
        
        # 扫描按钮
        scan_button = st.button("🔍 扫描工坊目录", type="primary")
    
    # 主内容区域
    if not workshop_path:
        st.info("请在侧边栏设置工坊目录路径")
        return
    
    if not Path(workshop_path).exists():
        st.error(f"目录不存在: {workshop_path}")
        return
    
    # 初始化会话状态
    if "scanner" not in st.session_state:
        st.session_state.scanner = None
    if "wallpapers" not in st.session_state:
        st.session_state.wallpapers = []
    if "filtered_wallpapers" not in st.session_state:
        st.session_state.filtered_wallpapers = []
    
    # 执行扫描
    if scan_button or st.session_state.scanner is None:
        with st.spinner("正在扫描工坊目录..."):
            try:
                scanner = WorkshopScanner(workshop_path)
                wallpapers = scanner.scan_workshop(max_workers=max_workers)
                st.session_state.scanner = scanner
                st.session_state.wallpapers = wallpapers
                st.session_state.filtered_wallpapers = wallpapers
                st.success(f"扫描完成！找到 {len(wallpapers)} 个壁纸")
            except Exception as e:
                st.error(f"扫描失败: {e}")
                return
    
    if not st.session_state.wallpapers:
        st.info("没有找到壁纸，请检查目录路径")
        return
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📋 浏览与过滤", "📁 重命名工具", "📊 统计信息"])
    
    with tab1:
        st.header("浏览与过滤")
        
        # 过滤器
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 标题搜索
            title_filter = st.text_input("搜索标题", "")
            
            # 内容评级过滤
            content_ratings = st.session_state.scanner.get_unique_values("contentrating")
            selected_rating = st.selectbox("内容评级", ["全部"] + content_ratings)
            
        with col2:
            # 类型过滤
            types = st.session_state.scanner.get_unique_values("type")
            selected_type = st.selectbox("壁纸类型", ["全部"] + types)
            
            # 性内容评级
            sex_ratings = st.session_state.scanner.get_unique_values("ratingsex")
            selected_sex_rating = st.selectbox("性内容评级", ["全部"] + sex_ratings)
            
        with col3:
            # 暴力内容评级
            violence_ratings = st.session_state.scanner.get_unique_values("ratingviolence")
            selected_violence_rating = st.selectbox("暴力内容评级", ["全部"] + violence_ratings)
            
            # 标签过滤
            all_tags = st.session_state.scanner.get_unique_values("tags")
            selected_tags = st.multiselect("标签", all_tags)
        
        # 应用过滤器
        filters = {}
        if title_filter:
            filters["title"] = title_filter
        if selected_rating != "全部":
            filters["contentrating"] = selected_rating
        if selected_type != "全部":
            filters["type"] = selected_type
        if selected_sex_rating != "全部":
            filters["ratingsex"] = selected_sex_rating
        if selected_violence_rating != "全部":
            filters["ratingviolence"] = selected_violence_rating
        if selected_tags:
            filters["tags"] = selected_tags
        
        # 执行过滤
        if filters:
            filtered_wallpapers = st.session_state.scanner.filter_wallpapers(filters)
        else:
            filtered_wallpapers = st.session_state.wallpapers
        
        st.session_state.filtered_wallpapers = filtered_wallpapers
        
        st.write(f"显示 {len(filtered_wallpapers)} / {len(st.session_state.wallpapers)} 个壁纸")
        
        # 导出按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 导出路径列表"):
                output_file = f"wallpaper_paths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                st.session_state.scanner.export_filtered_paths(filtered_wallpapers, output_file)
                st.success(f"已导出到 {output_file}")
        
        with col2:
            if st.button("📋 导出JSON数据"):
                output_file = f"wallpapers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                st.session_state.scanner.export_filtered_json(filtered_wallpapers, output_file)
                st.success(f"已导出到 {output_file}")
        
        # 显示模式选择
        display_mode = st.radio("显示模式", ["网格视图", "列表视图"], horizontal=True)
        
        if display_mode == "网格视图":
            # 显示壁纸网格
            if filtered_wallpapers:
                display_wallpaper_grid(filtered_wallpapers)
            else:
                st.info("没有符合条件的壁纸")
        else:
            # 列表视图
            if filtered_wallpapers:
                # 转换为DataFrame
                data = []
                for wp in filtered_wallpapers:
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
            else:
                st.info("没有符合条件的壁纸")
    
    with tab2:
        st.header("重命名工具")
        
        if not st.session_state.filtered_wallpapers:
            st.info("请先在浏览页面筛选壁纸")
        else:
            st.write(f"将对 {len(st.session_state.filtered_wallpapers)} 个壁纸进行重命名")
            
            # 命名模板配置
            st.subheader("命名模板")
            name_template = st.text_input(
                "命名模板",
                value=config.get("name_template", "[#{id}]{original_name}+{title}"),
                help="可用占位符: {id}, {title}, {original_name}, {type}, {rating}"
            )
            
            # 验证模板
            renamer = FolderRenamer(dry_run=True)
            template_issues = renamer.validate_template(name_template)
            if template_issues:
                for issue in template_issues:
                    st.warning(issue)
            
            # 预览示例
            if st.session_state.filtered_wallpapers and not template_issues:
                st.subheader("重命名预览")
                preview_count = min(5, len(st.session_state.filtered_wallpapers))
                
                preview_data = []
                for wp in st.session_state.filtered_wallpapers[:preview_count]:
                    new_name = wp.generate_new_name(name_template)
                    preview_data.append({
                        "原名称": wp.folder_name,
                        "新名称": new_name,
                        "标题": wp.title
                    })
                
                df_preview = pd.DataFrame(preview_data)
                st.dataframe(df_preview, use_container_width=True)
                
                if len(st.session_state.filtered_wallpapers) > preview_count:
                    st.info(f"只显示前 {preview_count} 个预览，共 {len(st.session_state.filtered_wallpapers)} 个")
            
            # 重命名选项
            st.subheader("重命名选项")
            
            col1, col2 = st.columns(2)
            with col1:
                rename_mode = st.radio(
                    "重命名模式",
                    ["原位重命名", "复制到新位置"],
                    help="原位重命名会直接修改文件夹名称，复制到新位置会保留原文件"
                )
            
            with col2:
                if rename_mode == "复制到新位置":
                    target_dir = st.text_input("目标目录", "")
                    if target_dir and not Path(target_dir).exists():
                        st.warning("目标目录不存在")
                else:
                    target_dir = None
            
            # 执行重命名
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 预览重命名", type="secondary"):
                    if not template_issues:
                        with st.spinner("生成重命名预览..."):
                            renamer = FolderRenamer(dry_run=True)
                            results = renamer.rename_folders(
                                st.session_state.filtered_wallpapers,
                                name_template,
                                target_dir if rename_mode == "复制到新位置" else None
                            )
                            
                            # 显示完整预览
                            preview_data = []
                            for result in results:
                                preview_data.append({
                                    "标题": result["title"],
                                    "原名称": result["old_name"],
                                    "新名称": result["new_name"],
                                    "状态": result["status"]
                                })
                            
                            df_full_preview = pd.DataFrame(preview_data)
                            st.dataframe(df_full_preview, use_container_width=True)
            
            with col2:
                if st.button("✅ 执行重命名", type="primary"):
                    if template_issues:
                        st.error("请先修复模板问题")
                    elif rename_mode == "复制到新位置" and (not target_dir or not Path(target_dir).exists()):
                        st.error("请设置有效的目标目录")
                    else:
                        # 确认对话框
                        if st.session_state.get("rename_confirmed", False):
                            with st.spinner("正在执行重命名..."):
                                renamer = FolderRenamer(dry_run=False)
                                results = renamer.rename_folders(
                                    st.session_state.filtered_wallpapers,
                                    name_template,
                                    target_dir if rename_mode == "复制到新位置" else None
                                )
                                
                                # 统计结果
                                success_count = sum(1 for r in results if r["status"] in ["renamed", "copied"])
                                error_count = sum(1 for r in results if r["status"] == "error")
                                
                                st.success(f"重命名完成！成功: {success_count}, 失败: {error_count}")
                                
                                # 导出日志
                                log_file = f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                                renamer.export_rename_log(log_file)
                                st.info(f"重命名日志已保存到 {log_file}")
                                
                                # 重置确认状态
                                st.session_state.rename_confirmed = False
                        else:
                            st.warning("⚠️ 此操作将修改文件夹，请确认继续")
                            if st.button("确认执行"):
                                st.session_state.rename_confirmed = True
                                st.rerun()
            
            # 保存模板到配置
            if name_template != config.get("name_template", ""):
                config["name_template"] = name_template
                save_app_config(config)
    
    with tab3:
        st.header("统计信息")
        
        if st.session_state.wallpapers:
            wallpapers = st.session_state.wallpapers
            
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
        else:
            st.info("请先扫描工坊目录")


if __name__ == "__main__":
    main()
