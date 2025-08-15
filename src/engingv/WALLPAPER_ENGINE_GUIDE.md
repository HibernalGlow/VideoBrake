# Wallpaper Engine 工坊管理工具使用指南

## 快速开始

### 方法一：直接运行 Streamlit 应用
```bash
cd "d:\1VSCODE\Projects\PackU\VideoBrake"
streamlit run src/engingv/app.py
```

### 方法二：使用 CLI 工具
```bash
cd "d:\1VSCODE\Projects\PackU\VideoBrake"
python -m engingv
```

### 方法三：使用启动脚本
```bash
cd "d:\1VSCODE\Projects\PackU\VideoBrake"
python run_engingv.py
```

## 工具功能详解

### 1. 工坊目录扫描
- 自动扫描指定目录下的所有壁纸文件夹
- 读取每个文件夹的 `project.json` 文件
- 提取壁纸元数据（标题、描述、标签、评级等）
- 获取文件夹时间戳和大小信息

### 2. 智能过滤系统
支持多种过滤条件：
- **标题搜索**: 模糊匹配壁纸标题
- **内容评级**: Everyone, Mature, Adult
- **壁纸类型**: Video, Scene, Web, Application
- **性内容评级**: none, mild, moderate, explicit
- **暴力内容评级**: none, mild, moderate, explicit  
- **标签过滤**: 支持多选标签组合

### 3. 预览展示
- **网格视图**: 卡片式展示，显示预览图和基本信息
- **列表视图**: 表格形式显示详细信息
- **预览图支持**: 自动加载 `preview.gif` 或其他预览文件

### 4. 批量重命名
#### 命名模板
支持以下占位符：
- `{id}`: 工坊 ID（文件夹名）
- `{title}`: 壁纸标题
- `{original_name}`: 原始文件夹名
- `{type}`: 壁纸类型（Video/Scene/Web等）
- `{rating}`: 内容评级（Everyone/Mature等）

#### 模板示例
```
[#{id}]{original_name}+{title}
→ [#123456789]original_folder+My Awesome Wallpaper

{title}_{id}
→ My Awesome Wallpaper_123456789

{type}_{rating}_{title}
→ Video_Everyone_My Awesome Wallpaper
```

#### 重命名模式
- **原位重命名**: 直接修改文件夹名称
- **复制到新位置**: 保留原文件，在新位置创建重命名副本

### 5. 数据导出
- **路径列表**: 导出过滤后的文件夹路径列表（.txt）
- **JSON数据**: 导出完整的壁纸元数据（.json）  
- **重命名日志**: 记录重命名操作的详细信息

### 6. 统计分析
- 壁纸总数统计
- 文件总大小统计
- 类型分布图表
- 内容评级分布图表
- 热门标签统计

## 典型使用场景

### 场景1：清理和整理工坊壁纸
1. 设置工坊目录路径
2. 扫描所有壁纸
3. 使用过滤器找出特定类型的壁纸
4. 批量重命名为统一格式
5. 导出清理后的路径列表

### 场景2：按评级分类壁纸
1. 扫描工坊目录
2. 按内容评级过滤（Everyone/Mature/Adult）
3. 使用包含评级的命名模板重命名
4. 复制到不同的分类目录

### 场景3：查找特定主题壁纸
1. 使用标题搜索功能
2. 结合标签过滤
3. 预览确认壁纸内容
4. 导出符合条件的壁纸路径

## 配置文件说明

工具会自动创建 `wallpaper_config.json` 配置文件：

```json
{
  "workshop_path": "C:\\Steam\\steamapps\\workshop\\content\\431960",
  "name_template": "[#{id}]{original_name}+{title}",
  "max_workers": 4,
  "recent_paths": [
    "C:\\Steam\\steamapps\\workshop\\content\\431960"
  ]
}
```

## 常见问题

### Q: 工坊目录在哪里？
A: 通常位于 `C:\Program Files (x86)\Steam\steamapps\workshop\content\431960`

### Q: 如何处理重名文件夹？
A: 工具会自动在重名文件夹后添加数字后缀，如 `filename_1`, `filename_2`

### Q: 重命名后能恢复吗？
A: 如果使用"原位重命名"，建议先备份。"复制到新位置"模式会保留原文件。

### Q: 扫描很慢怎么办？
A: 可以调整"并发线程数"设置，但过高可能影响系统性能。

### Q: 预览图不显示？
A: 确保 `project.json` 中的 `preview` 字段正确，且预览文件存在。

## 安全提醒

1. **重要数据备份**: 在进行批量操作前，请备份重要数据
2. **权限检查**: 确保程序有足够权限访问工坊目录
3. **预览确认**: 在实际执行重命名前，请使用预览功能确认结果
4. **分批处理**: 对于大量文件，建议分批处理以避免意外

## 技术支持

如遇到问题，请检查：
1. Python 环境是否正确安装
2. 依赖包是否完整（streamlit, pandas 等）
3. 工坊目录路径是否正确
4. 文件权限是否足够
