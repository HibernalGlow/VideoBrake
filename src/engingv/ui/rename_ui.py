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
        help="可用占位符: {id}, {title}, {original_name}, {type}, {rating}, {desc} (截断描述)"
    )

    # 截断设置
    with st.expander("高级: 描述与名称长度限制"):
        col_a, col_b = st.columns(2)
        with col_a:
            desc_len = st.number_input(
                "描述截断长度",
                min_value=0,
                max_value=500,
                value=config.get("rename_settings.description_max_length", 18),
                help="描述超过该长度将被截断并加上省略号。设为0表示不加入描述。"
            )
        with col_b:
            name_len = st.number_input(
                "最终名称最大长度",
                min_value=10,
                max_value=255,
                value=config.get("rename_settings.name_max_length", 120),
                help="超过将截断，尽量保留末尾的 #id" 
            )
        # 实时更新配置
        if desc_len != config.get("rename_settings.description_max_length"):
            cfg = config.get("rename_settings", {})
            cfg["description_max_length"] = desc_len
            config.set("rename_settings", cfg)
        if name_len != config.get("rename_settings.name_max_length"):
            cfg = config.get("rename_settings", {})
            cfg["name_max_length"] = name_len
            config.set("rename_settings", cfg)
    
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
            new_name = wp.generate_new_name(
                name_template,
                description_max_length=config.get("rename_settings.description_max_length", 18),
                name_max_length=config.get("rename_settings.name_max_length", 120)
            )
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
                # 存储参数并进入确认阶段
                st.session_state.rename_params = {
                    "wallpapers_ids": [wp.workshop_id for wp in filtered_wallpapers],
                    "template": name_template,
                    "target_dir": target_dir,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.rename_confirmed = False
                st.session_state.rename_ready = True
                st.rerun()

    # 若准备执行，显示确认与详细信息
    if st.session_state.get("rename_ready"):
        params = st.session_state.get("rename_params", {})
        id_set = set(params.get("wallpapers_ids", []))
        # 重新映射当前传入列表，避免引用失效
        wallpapers_map = {wp.workshop_id: wp for wp in filtered_wallpapers}
        rename_wallpapers = [wallpapers_map[w_id] for w_id in id_set if w_id in wallpapers_map]

        st.info(f"待重命名数量: {len(rename_wallpapers)}")
        if not st.session_state.get("rename_confirmed"):
            with st.expander("操作概要", expanded=True):
                st.write("示例前 5 条:")
                for wp in rename_wallpapers[:5]:
                    new_name_preview = wp.generate_new_name(
                        params["template"],
                        description_max_length=config.get("rename_settings.description_max_length", 18),
                        name_max_length=config.get("rename_settings.name_max_length", 120)
                    )
                    st.caption(f"{wp.folder_name} -> {new_name_preview}")
            col_c1, col_c2, col_c3 = st.columns([1,1,3])
            with col_c1:
                if st.button("确认执行", key="confirm_execute_final"):
                    st.session_state.rename_confirmed = True
                    st.rerun()
            with col_c2:
                if st.button("取消", key="cancel_execute"):
                    st.session_state.rename_ready = False
                    st.session_state.rename_params = {}
                    st.session_state.rename_confirmed = False
                    st.success("已取消")
        else:
            # 进入实际执行
            _execute_rename(rename_wallpapers, params["template"], params["target_dir"], config)
            # 清理状态
            st.session_state.rename_ready = False
            st.session_state.rename_params = {}


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
    if not wallpapers:
        st.warning("没有可重命名的壁纸")
        return

    progress = st.progress(0, text="初始化...")
    renamer = FolderRenamer(dry_run=False)
    results: List[Dict[str, Any]] = []
    total = len(wallpapers)
    for idx, wp in enumerate(wallpapers, start=1):
        single_results = renamer.rename_folders([wp], template, target_dir)
        results.extend(single_results)
        progress.progress(min(idx / total, 1.0), text=f"处理中 {idx}/{total}: {wp.folder_name}")
    progress.empty()

    # 统计结果
    success_count = sum(1 for r in results if r["status"] in ["renamed", "copied"])
    error_count = sum(1 for r in results if r["status"] == "error")
    unchanged_count = sum(1 for r in results if r["status"] == "planned")

    if success_count > 0:
        st.success(f"重命名完成！成功: {success_count}, 失败: {error_count}")
    if unchanged_count and success_count == 0 and error_count == 0:
        st.info(f"没有文件夹需要改名 (全部名称生成后与原名一致)。")

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
                    "错误": result.get("error", "未知错误"),
                })
            df_errors = pd.DataFrame(error_data)
            st.dataframe(df_errors, use_container_width=True)

    # 显示成功/计划详情
    with st.expander("结果明细", expanded=False):
        details = []
        for r in results:
            details.append({
                "ID": r.get("workshop_id"),
                "原名称": Path(r.get("old_path", "")).name if r.get("old_path") else "",
                "新名称": r.get("new_name"),
                "状态": r.get("status")
            })
        if details:
            df_details = pd.DataFrame(details)
            st.dataframe(df_details, use_container_width=True)

    # 导出日志
    log_file = f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    renamer.export_rename_log(log_file)
    st.info(f"重命名日志已保存到 {log_file}")

    # 保存模板到配置
    config.set("name_template", template)

    # 重置确认状态（允许再次执行）
    st.session_state.rename_confirmed = False
