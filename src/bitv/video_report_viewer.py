"""
brakev 视频报告查看器

一个Streamlit应用，用于可视化和筛选视频分析JSON报告数据
"""

import os
import json
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, ColumnsAutoSizeMode, GridUpdateMode
import plotly.express as px

# 设置页面标题
st.set_page_config(
    page_title="brakev 视频报告查看器",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 启用AgGrid企业版模块
st.markdown("""
<style>
div[data-testid="stSidebar"] {
    min-width: 300px;
    max-width: 400px;
}
.ag-theme-streamlit {
    --ag-header-foreground-color: #0078cc;
    --ag-header-background-color: #f0f0f0;
    --ag-row-hover-color: #e6f7ff;
    --ag-selected-row-background-color: #cce8ff;
}
</style>
""", unsafe_allow_html=True)

def load_json_report(file_path):
    """加载JSON报告文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"加载JSON文件出错: {str(e)}")
        return None

def extract_videos_from_report(report_data):
    """从报告中提取视频信息"""
    videos = []
    
    # 检查是否是分析报告格式
    if isinstance(report_data, list):
        # 直接作为视频列表
        return report_data
    elif "videos" in report_data:
        for video in report_data["videos"]:
            if "info" in video:
                videos.append(video["info"])
            else:
                videos.append(video)
    # 检查是否是分类报告格式
    elif "results" in report_data:
        if isinstance(report_data["results"], dict):
            # 如果results是字典（按bitrate_level分组）
            for level, results_list in report_data["results"].items():
                for result in results_list:
                    if "video_info" in result:
                        video_info = result["video_info"]
                        # 添加bitrate_level字段
                        if "bitrate_level" not in video_info:
                            video_info["bitrate_level"] = level
                        videos.append(video_info)
        else:
            # 如果results是列表
            for result in report_data["results"]:
                if "video_info" in result:
                    videos.append(result["video_info"])
    # 检查是否是results_by_level格式
    elif "results_by_level" in report_data:
        for level, results_list in report_data["results_by_level"].items():
            for result in results_list:
                if "video_info" in result:
                    video_info = result["video_info"]
                    # 添加bitrate_level字段
                    if "bitrate_level" not in video_info:
                        video_info["bitrate_level"] = level
                    videos.append(video_info)
    
    return videos

def create_dataframe(videos):
    """将视频信息转换为DataFrame"""
    if not videos:
        return pd.DataFrame()
    
    # 提取所有的键，确保包含所有可能的列
    all_keys = set()
    for video in videos:
        all_keys.update(video.keys())
    
    # 创建DataFrame - 保持数据原始形态，不进行任何转换
    df = pd.DataFrame(videos)
    
    # 确保包含常用列，如果不存在则添加
    essential_columns = [
        "filename", "duration_formatted",
        "bitrate_mbps", "bitrate_mbps",
        "width", "height", "resolution",
        "fps", "size_mb", "size_formatted",
        "bitrate_level"
    ]
    
    for col in essential_columns:
        if col not in df.columns:
            df[col] = None
    
    # 如果有duration列但没有duration_formatted列，则创建它
    if "duration" in df.columns and "duration_formatted" not in df.columns:
        df["duration_formatted"] = df["duration"].apply(format_duration)
    
    # 如果有size_bytes列但没有size_formatted列，则创建它
    if "size_bytes" in df.columns and "size_formatted" not in df.columns:
        df["size_formatted"] = df["size_bytes"].apply(format_size)
        if "size_mb" not in df.columns:
            df["size_mb"] = df["size_bytes"] / (1024 * 1024)
    
    # 如果有bitrate列但没有bitrate_formatted列，则创建它
    # if "bitrate" in df.columns:
    #     if "bitrate_formatted" not in df.columns:
    #         # df["bitrate_formatted"] = df["bitrate"].apply(format_bitrate)
    #         df["bitrate_formatted"] = df["bitrate"]
        # if "bitrate_mbps" not in df.columns:
        #     df["bitrate_mbps"] = df["bitrate"] / 1_000_000
    
    # 创建分辨率说明
    if "width" in df.columns and "height" in df.columns and "resolution" not in df.columns:
        df["resolution"] = df.apply(lambda row: format_resolution(row["width"], row["height"]), axis=1)
    
    return df

def format_duration(seconds):
    """将秒转换为时:分:秒格式"""
    if pd.isna(seconds):
        return "00:00:00"
    
    from datetime import timedelta
    td = timedelta(seconds=float(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if td.days > 0:
        return f"{td.days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_size(size_bytes):
    """格式化文件大小"""
    if pd.isna(size_bytes):
        return "0 B"
    
    size_bytes = float(size_bytes)
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024)::.2f} GB"

def format_bitrate(bitrate):
    """格式化码率"""
    if pd.isna(bitrate):
        return "0 bps"
    
    bitrate = float(bitrate)
    if bitrate < 1000:
        return f"{bitrate:.2f} bps"
    elif bitrate < 1000000:
        return f"{bitrate / 1000:.2f} Kbps"
    else:
        return f"{bitrate / 1000000:.2f} Mbps"

def format_resolution(width, height):
    """格式化分辨率"""
    if pd.isna(width) or pd.isna(height):
        return "未知"
    
    width = int(width)
    height = int(height)
    
    if width == 3840 and height == 2160:
        return f"{width}x{height} (4K UHD)"
    elif width == 1920 and height == 1080:
        return f"{width}x{height} (1080p Full HD)"
    elif width == 1280 and height == 720:
        return f"{width}x{height} (720p HD)"
    else:
        return f"{width}x{height}"

def configure_grid(df):
    """配置AG Grid"""
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # 列宽度自动调整
    gb.configure_default_column(
        resizable=True, 
        filterable=True, 
        sortable=True,
        editable=False,
        suppressMenu=False,  # 显示列菜单
        enableRowGroup=True,
        enablePivot=True,
        enableValue=True
    )
    
    # 配置特定列
    if "filename" in df.columns:
        gb.configure_column("filename", headerName="文件名", width=200)
    
    if "duration_formatted" in df.columns:
        gb.configure_column("duration_formatted", headerName="时长", width=120)
    
    # 使用bitrate_mbps作为码率列显示，但不进行四舍五入，保持原始精度
    if "bitrate_mbps" in df.columns:
        gb.configure_column("bitrate_mbps", headerName="码率(Mbps)", width=120)
    # elif "bitrate_formatted" in df.columns:
    #     gb.configure_column("bitrate_formatted", headerName="码率", width=120)
    
    if "resolution" in df.columns:
        gb.configure_column("resolution", headerName="分辨率", width=180)
    
    if "size_formatted" in df.columns:
        gb.configure_column("size_formatted", headerName="大小", width=120)
    
    if "fps" in df.columns:
        gb.configure_column("fps", headerName="帧率", width=80)
    
    # if "bitrate_level" in df.columns:
    #     gb.configure_column(
    #         "bitrate_level", 
    #         headerName="码率等级", 
    #         width=120,
    #         rowGroup=True,  # 默认按码率等级分组
    #         enableRowGroup=True
    #     )
    
    # 添加选择框
    gb.configure_selection(
        selection_mode="multiple", 
        use_checkbox=True,
        groupSelectsChildren=True,
        groupSelectsFiltered=True
    )
    
    # 添加行过滤和其他高级功能
    gb.configure_grid_options(
        # 基本功能
        enableRangeSelection=True, 
        rowSelection="multiple",
        
        # 企业版功能 - 高级筛选
        enableAdvancedFilter=True,
        enableFilter=True,
        
        # 企业版功能 - 行分组和透视
        enableGroupEdit=True,
        groupDefaultExpanded=1,
        groupIncludeFooter=True,
        groupIncludeTotalFooter=True,
        groupSelectsChildren=True,
        groupMultiAutoColumn=True,
        groupDisplayType="groupRows",
        rowGroupPanelShow='always',
        
        # 企业版功能 - 聚合和计算
        enableValue=True,
        enablePivot=True,
        pivotPanelShow="always",
        
        # 企业版功能 - 状态栏
        enableStatusBar=True,
        alwaysShowStatusBar=True,
        
        # 企业版功能 - 图表
        enableCharts=True,
        
        # 企业版功能 - 右侧工具栏
        enableSideBar=True,
        sideBar={
            "toolPanels": [
                {
                    "id": "columns",
                    "labelDefault": "列",
                    "labelKey": "columns",
                    "iconKey": "columns",
                    "toolPanel": "agColumnsToolPanel",
                    "minWidth": 225,
                    "maxWidth": 225,
                    "width": 225
                },
                {
                    "id": "filters",
                    "labelDefault": "筛选器",
                    "labelKey": "filters",
                    "iconKey": "filter",
                    "toolPanel": "agFiltersToolPanel",
                    "minWidth": 180,
                    "maxWidth": 400,
                    "width": 250
                },
                {
                    "id": "rows",
                    "labelDefault": "行",
                    "labelKey": "rows",
                    "iconKey": "rowGroupPanel",
                    "toolPanel": "agRowGroupPanel"
                }
            ],
            "position": "right",
            "defaultToolPanel": "filters"
        },
        
        # 企业版功能 - 菜单
        suppressMenuHide=True,
        popupParent=JsCode("document.body"),
        
        # 企业版功能 - 行操作
        ensureDomOrder=True,
        suppressCellSelection=True,
        suppressRowClickSelection=True,
        
        # 企业版功能 - 导出
        enableRangeHandle=True,
        copyHeadersToClipboard=True,
        enableCellTextSelection=True,
        
        # 企业版功能 - 外观
        headerHeight=35,
        rowHeight=35,
        animateRows=True,
        suppressAnimationFrame=True,
        suppressColumnVirtualisation=True,
        domLayout='autoHeight',
        
        # 企业版功能 - 可访问性
        suppressColumnMoveAnimation=True,
        suppressLoadingOverlay=True,
        suppressNoRowsOverlay=True,
        
        # 企业版功能 - 设置面板
        enableFillHandle=True,
        suppressContextMenu=True,
        allowContextMenuWithControlKey=True,
        getContextMenuItems=JsCode('''
        function getContextMenuItems(params) {
            var result = [
                {
                    name: "导出所选数据",
                    subMenu: [
                        { name: "CSV格式", action: function() { params.api.exportDataAsCsv({ onlySelected: true }); } },
                        { name: "Excel格式", action: function() { params.api.exportDataAsExcel({ onlySelected: true }); } }
                    ]
                },
                "separator",
                "copy",
                "copyWithHeaders",
                "separator",
                "autoSizeAll",
                "resetColumns"
            ];
            return result;
        }
        '''),
        
        # 企业版功能 - 全文搜索
        enableCellChangeFlash=True,
    )
    
    return gb.build()

def main():
    """主函数"""
    st.title("🎬 brakev 视频报告查看器")
    
    # 侧边栏
    with st.sidebar:
        st.header("📁 选择报告文件")
        
        # 上传JSON文件
        uploaded_file = st.file_uploader("上传JSON报告文件", type=["json"])
        
        # 或者选择本地文件
        st.write("--- 或者 ---")
        json_file_path = st.text_input("输入本地JSON文件路径:")
        
        if st.button("加载文件"):
            if not json_file_path:
                st.error("请输入JSON文件路径")
            elif not os.path.exists(json_file_path):
                st.error("文件不存在")
        
        st.divider()
        st.write("### 筛选选项")
        # 这些筛选选项将在数据加载后动态生成
    
    # 加载数据
    data = None
    if uploaded_file is not None:
        # 从上传的文件加载
        try:
            data = json.loads(uploaded_file.getvalue().decode("utf-8"))
            st.success(f"成功加载上传的JSON文件")
        except Exception as e:
            st.error(f"加载JSON文件出错: {str(e)}")
    elif json_file_path and os.path.exists(json_file_path):
        # 从本地文件加载
        data = load_json_report(json_file_path)
        if data:
            st.success(f"成功加载文件: {json_file_path}")
    
    # 如果数据加载成功，处理并显示
    if data:
        # 显示报告基本信息
        if "timestamp" in data:
            st.info(f"报告生成时间: {data['timestamp']}")
        
        if "folder_path" in data:
            st.info(f"文件夹: {data['folder_path']}")
        
        # 提取视频信息
        videos = extract_videos_from_report(data)
        if not videos:
            st.warning("未找到视频信息")
        else:
            st.success(f"找到 {len(videos)} 个视频文件")
            
            # 创建DataFrame
            df = create_dataframe(videos)
            
            # 统计信息卡片 - 不进行格式化，显示原始数据
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("视频总数", len(df))
            with col2:
                total_duration_hours = df["duration"].sum() / 3600 if "duration" in df.columns else 0
                st.metric("总时长(小时)", total_duration_hours)
            with col3:
                total_size_gb = df["size_mb"].sum() / 1024 if "size_mb" in df.columns else 0
                st.metric("总大小(GB)", total_size_gb)
            with col4:
                avg_bitrate = df["bitrate_mbps"].mean() if "bitrate_mbps" in df.columns else 0
                st.metric("平均码率(Mbps)", avg_bitrate)
            
            # 创建标签页
            tab1, tab2, tab3 = st.tabs(["📊 数据表", "📈 图表分析", "⚙️ 高级设置"])
            
            with tab1:
                # 使用AGGrid显示数据表格
                st.header("视频数据表")
                
                # 列选择
                if not df.empty:
                    # 确定要显示的列
                    default_columns = [
                        "filename", "duration_formatted", "bitrate_mbps",
                        "resolution", "fps", "size_formatted", "bitrate_level"
                    ]
                    
                    available_columns = df.columns.tolist()
                    selected_columns = []
                    
                    for col in default_columns:
                        if col in available_columns:
                            selected_columns.append(col)
                    
                    # 显示列选择器
                    with st.expander("选择显示的列"):
                        display_cols = st.multiselect(
                            "选择要显示的列",
                            options=available_columns,
                            default=selected_columns
                        )
                    
                    if display_cols:
                        display_df = df[display_cols]
                    else:
                        display_df = df
                    
                    # 配置AG Grid
                    grid_options = configure_grid(display_df)
                    
                    # 显示表格
                    grid_response = AgGrid(
                        display_df,
                        gridOptions=grid_options,
                        enable_enterprise_modules=True,  # 启用企业版模块
                        update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED,
                        fit_columns_on_grid_load=True,
                        custom_css={
                            "#gridToolBar": {"padding-bottom": "0px !important"},
                            ".ag-theme-streamlit .ag-header": {"font-weight": "bold"},
                            ".ag-theme-streamlit .ag-header-group-cell": {"font-weight": "bold"},
                            ".ag-theme-streamlit .ag-row-hover": {"background-color": "#e6f7ff !important"}
                        },
                        allow_unsafe_jscode=True,  # 允许不安全的JS代码
                        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,  # 自适应列宽
                        height=600,
                        width='100%',
                        theme='streamlit',  # 使用Streamlit主题
                        key="grid_1",  # 添加key确保组件正常重渲染
                        reload_data=True,  # 确保数据重新加载
                        enable_quicksearch=True,  # 启用快速搜索
                        data_return_mode="AS_INPUT",  # 保持原始数据格式
                    )
                    
                    # 获取选中的数据
                    selected_rows = grid_response["selected_rows"]
                    if selected_rows:
                        st.write(f"已选择 {len(selected_rows)} 个视频")
                        with st.expander("查看选中的视频"):
                            st.json(selected_rows)
                            
                        # 添加导出选中项的快捷按钮
                        export_col1, export_col2, export_col3 = st.columns(3)
                        with export_col1:
                            if st.button("导出选中项为CSV"):
                                selected_df = pd.DataFrame(selected_rows)
                                csv = selected_df.to_csv(index=True)
                                st.download_button(
                                    label="下载CSV文件",
                                    data=csv,
                                    file_name="selected_videos_export.csv",
                                    mime="text/csv",
                                )
                        with export_col2:
                            if st.button("导出选中项为Excel"):
                                import io
                                selected_df = pd.DataFrame(selected_rows)
                                buffer = io.BytesIO()
                                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                                    selected_df.to_excel(writer, index=True, sheet_name="SelectedVideos")
                                buffer.seek(0)
                                st.download_button(
                                    label="下载Excel文件",
                                    data=buffer,
                                    file_name="selected_videos_export.xlsx",
                                    mime="application/vnd.ms-excel",
                                )
                        with export_col3:
                            if st.button("导出选中项为JSON"):
                                selected_json = json.dumps(selected_rows, ensure_ascii=True, indent=2)
                                st.download_button(
                                    label="下载JSON文件",
                                    data=selected_json,
                                    file_name="selected_videos_export.json",
                                    mime="application/json",
                                )
            
            with tab2:
                st.header("数据可视化")
                
                # 检查是否有数据可以可视化
                if not df.empty:
                    # 创建分布图
                    if "bitrate_level" in df.columns:
                        st.subheader("码率等级分布")
                        bitrate_counts = df["bitrate_level"].value_counts().reset_index()
                        bitrate_counts.columns = ["bitrate_level", "count"]
                        fig = px.bar(
                            bitrate_counts, 
                            x="bitrate_level", 
                            y="count",
                            title="视频码率等级分布"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 创建散点图
                    st.subheader("视频大小与时长关系")
                    if all(col in df.columns for col in ["size_mb", "duration"]):
                        # 创建图表时保留原始数据格式，不进行四舍五入
                        fig = px.scatter(
                            df, 
                            x="duration", 
                            y="size_mb",
                            hover_name="filename",
                            color="bitrate_level" if "bitrate_level" in df.columns else None,
                            size="bitrate_mbps" if "bitrate_mbps" in df.columns else None,
                            title="视频大小与时长的关系",
                            labels={"duration": "时长(秒)", "size_mb": "大小(MB)"},
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 创建直方图
                    if "bitrate_mbps" in df.columns:
                        st.subheader("码率分布")
                        fig = px.histogram(
                            df, 
                            x="bitrate_mbps", 
                            nbins=20,
                            title="视频码率分布",
                            labels={"bitrate_mbps": "码率(Mbps)"},
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 创建饼图
                    if "resolution" in df.columns:
                        st.subheader("分辨率分布")
                        resolution_counts = df["resolution"].value_counts().reset_index()
                        resolution_counts.columns = ["resolution", "count"]
                        fig = px.pie(
                            resolution_counts, 
                            names="resolution", 
                            values="count",
                            title="视频分辨率分布"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("没有可用于可视化的数据")
            
            with tab3:
                st.header("高级设置")
                st.write("这里可以添加其他高级设置选项")
                
                # 导出功能
                st.subheader("导出数据")
                if not df.empty:
                    export_format = st.selectbox("选择导出格式", ["CSV", "Excel", "JSON"])
                    if st.button("导出数据"):
                        if export_format == "CSV":
                            csv = df.to_csv(index=True)
                            st.download_button(
                                label="下载CSV文件",
                                data=csv,
                                file_name="video_report_export.csv",
                                mime="text/csv",
                            )
                        elif export_format == "Excel":
                            # 使用BytesIO创建Excel文件
                            import io
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                                df.to_excel(writer, index=True, sheet_name="VideoReport")
                            buffer.seek(0)
                            st.download_button(
                                label="下载Excel文件",
                                data=buffer,
                                file_name="video_report_export.xlsx",
                                mime="application/vnd.ms-excel",
                            )
                        elif export_format == "JSON":
                            # 使用ensure_ascii=False以正确处理中文字符
                            export_json = json.dumps(
                                json.loads(df.to_json(orient="records")), 
                                ensure_ascii=False,
                                indent=2
                            )
                            st.download_button(
                                label="下载JSON文件",
                                data=export_json,
                                file_name="video_report_export.json",
                                mime="application/json",
                            )
                
                # 批处理操作
                st.subheader("批处理操作")
                st.write("这里可以添加批处理功能，例如生成脚本批量处理选中的视频")
    else:
        # 显示使用说明
        st.write("## 使用说明")
        st.write("""
        1. 使用左侧边栏上传JSON报告文件或输入本地文件路径
        2. 加载后可以查看视频数据表格和统计信息
        3. 可以筛选、排序和搜索视频文件
        4. 可以通过图表分析视频数据分布
        """)
        
        # 显示示例图标
        st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
        st.write("期待您的使用！")

if __name__ == "__main__":
    main()