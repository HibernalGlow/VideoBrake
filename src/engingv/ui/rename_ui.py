"""
重命名工具 UI 模块
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..core.models import WallpaperFolder
from ..core.renamer import FolderRenamer
from ..utils.config import get_config


def create_rename_interface(filtered_wallpapers: List[WallpaperFolder]) -> None:
    """创建重命名界面"""
    if not filtered_wallpapers:
        st.info("请先在浏览页面筛选壁纸")
        return
    
    config = get_config()
    st.write(f"将对 {len(filtered_wallpapers)} 个壁纸进行重命名")
    
    # 命名模板配置
    st.subheader("命名模板")
    
    # 模板选择
    templates = config.get_templates()
    template_names = list(templates.keys())
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_template_name = st.selectbox(
            "选择预设模板",
            template_names,
            index=0 if template_names else 0
        )
    
    with col2:
        if st.button("管理模板"):
            st.session_state.show_template_manager = not st.session_state.get("show_template_manager", False)
    
    # 模板管理器
    if st.session_state.get("show_template_manager", False):
        _create_template_manager(config)
    
    # 当前模板
    current_template = templates.get(selected_template_name, "[#{id}]{original_name}+{title}")
    
    name_template = st.text_input(
        "命名模板",
        value=current_template,
        help="可用占位符: {id}, {title}, {original_name}, {type}, {rating}"
    )
    
    # 验证模板
    renamer = FolderRenamer(dry_run=True)
    template_issues = renamer.validate_template(name_template)
    
    if template_issues:
        for issue in template_issues:
            st.warning(f"⚠️ {issue}")
    else:
        st.success("✅ 模板格式正确")
    
    # 预览示例
    if not template_issues and filtered_wallpapers:
        st.subheader("重命名预览")
        preview_count = min(5, len(filtered_wallpapers))
        
        preview_data = []
        for wp in filtered_wallpapers[:preview_count]:
            new_name = wp.generate_new_name(name_template)
            preview_data.append({
                "原名称": wp.folder_name,
                "新名称": new_name,
                "标题": wp.title,
                "类型": wp.wallpaper_type
            })
        
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True)
        
        if len(filtered_wallpapers) > preview_count:
            st.info(f"只显示前 {preview_count} 个预览，共 {len(filtered_wallpapers)} 个")
    
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
        target_dir = None
        if rename_mode == "复制到新位置":
            target_dir = st.text_input("目标目录", "")
            if target_dir and not target_dir.strip():
                target_dir = None
            elif target_dir and not Path(target_dir).exists():
                st.warning("⚠️ 目标目录不存在")
    
    # 执行重命名
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 预览重命名", type="secondary"):
            if template_issues:
                st.error("请先修复模板问题")
            else:
                _show_full_preview(filtered_wallpapers, name_template, target_dir)
    
    with col2:
        if st.button("✅ 执行重命名", type="primary"):
            if template_issues:
                st.error("请先修复模板问题")
            elif rename_mode == "复制到新位置" and (not target_dir or not Path(target_dir).exists()):
                st.error("请设置有效的目标目录")
            else:
                _execute_rename(filtered_wallpapers, name_template, target_dir, config)


def _create_template_manager(config) -> None:
    """创建模板管理器"""
    st.subheader("模板管理")
    
    # 添加新模板
    with st.expander("添加新模板"):
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_template_name = st.text_input("模板名称", key="new_template_name")
        
        with col2:
            new_template_value = st.text_input("模板内容", key="new_template_value")
        
        with col3:
            if st.button("添加"):
                if new_template_name and new_template_value:
                    config.add_template(new_template_name, new_template_value)
                    st.success(f"模板 '{new_template_name}' 已添加")
                    st.rerun()
                else:
                    st.error("请填写模板名称和内容")
    
    # 管理现有模板
    templates = config.get_templates()
    
    if templates:
        st.write("现有模板:")
        
        for name, template in templates.items():
            col1, col2, col3 = st.columns([2, 4, 1])
            
            with col1:
                st.write(f"**{name}**")
            
            with col2:
                st.code(template, language="text")
            
            with col3:
                if name != "标准格式":  # 保护默认模板
                    if st.button("🗑️", key=f"delete_{name}", help="删除模板"):
                        config.remove_template(name)
                        st.success(f"模板 '{name}' 已删除")
                        st.rerun()


def _show_full_preview(wallpapers: List[WallpaperFolder], template: str, target_dir: str = None) -> None:
    """显示完整预览"""
    with st.spinner("生成重命名预览..."):
        renamer = FolderRenamer(dry_run=True)
        results = renamer.rename_folders(wallpapers, template, target_dir)
        
        # 显示完整预览
        preview_data = []
        for result in results:
            preview_data.append({
                "标题": result["title"],
                "原名称": result["old_name"],
                "新名称": result["new_name"],
                "状态": "预览" if result["status"] == "planned" else result["status"]
            })
        
        df_full_preview = pd.DataFrame(preview_data)
        st.dataframe(df_full_preview, use_container_width=True)


def _execute_rename(wallpapers: List[WallpaperFolder], template: str, target_dir: str, config) -> None:
    """执行重命名"""
    # 确认对话框
    if not st.session_state.get("rename_confirmed", False):
        st.warning("⚠️ 此操作将修改文件夹，请确认继续")
        if st.button("确认执行"):
            st.session_state.rename_confirmed = True
            st.rerun()
        return
    
    # 执行重命名
    with st.spinner("正在执行重命名..."):
        renamer = FolderRenamer(dry_run=False)
        results = renamer.rename_folders(wallpapers, template, target_dir)
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] in ["renamed", "copied"])
        error_count = sum(1 for r in results if r["status"] == "error")
        
        if success_count > 0:
            st.success(f"重命名完成！成功: {success_count}, 失败: {error_count}")
        
        if error_count > 0:
            st.error(f"部分重命名失败: {error_count}")
            
            # 显示错误详情
            error_results = [r for r in results if r["status"] == "error"]
            if error_results:
                st.subheader("错误详情")
                error_data = []
                for result in error_results:
                    error_data.append({
                        "标题": result["title"],
                        "原路径": result["old_path"],
                        "错误": result.get("error", "未知错误")
                    })
                
                df_errors = pd.DataFrame(error_data)
                st.dataframe(df_errors, use_container_width=True)
        
        # 导出日志
        log_file = f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        renamer.export_rename_log(log_file)
        st.info(f"重命名日志已保存到 {log_file}")
        
        # 保存模板到配置
        config.set("name_template", template)
        
        # 重置确认状态
        st.session_state.rename_confirmed = False
