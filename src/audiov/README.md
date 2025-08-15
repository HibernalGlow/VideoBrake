# AudioV - 视频音频提取工具

一个基于 FFmpeg 的 Python 视频音频提取工具，支持多种音频格式，提供丰富的终端交互界面。

## 功能特性

- 🎵 **多格式支持**: MP3, AAC, WAV, FLAC, M4A
- 📁 **灵活输入**: 目录扫描、手动输入、剪贴板粘贴
- ⚙️ **配置管理**: JSON 配置文件，支持自定义参数
- 🎨 **富交互界面**: 使用 Rich 库提供美观的终端界面
- 📊 **进度显示**: 实时进度条和处理状态
- 🔍 **文件验证**: 自动检测和验证视频文件
- 📋 **批量处理**: 支持多文件同时处理

## 安装要求

### 系统要求
- Python 3.11+
- FFmpeg (已安装并添加到 PATH)

### Python 依赖
```bash
pip install rich pyperclip
```

## 使用方法

### 1. 快速测试
```bash
# 测试 FFmpeg 是否可用
test_audiov.bat

# 或使用 Python 直接测试
python audiov_cli.py --test
```

### 2. 交互式界面
```bash
# Windows
audiov_start.bat

# 或直接使用 Python
python -m src.audiov
```

### 3. 命令行模式
```bash
# 提取单个文件
python audiov_cli.py "path/to/video.mp4"

# 扫描目录 (递归)
python audiov_cli.py "path/to/videos" -r

# 指定格式和输出目录
python audiov_cli.py "path/to/videos" -f aac -o "extracted_audio"

# 自定义质量参数
python audiov_cli.py "video.mp4" -f mp3 -q "-q:a 0"
```

### 2. 交互式操作流程

1. **检查 FFmpeg**: 自动检测 FFmpeg 是否可用
2. **选择输入方式**:
   - 扫描目录 (支持递归)
   - 手动输入文件路径
   - 从剪贴板粘贴路径
3. **选择音频格式**: 从预设格式中选择或自定义质量参数
4. **设置输出目录**: 默认目录、自定义目录或源文件目录
5. **确认并开始**: 查看处理摘要，确认后开始提取
6. **查看结果**: 显示处理结果和成功/失败统计

## 配置文件

配置文件位于 `src/audiov/config.json`，包含以下设置：

### FFmpeg 设置
```json
{
  "ffmpeg": {
    "executable_path": "ffmpeg",  // FFmpeg 可执行文件路径
    "timeout": 300                // 处理超时时间(秒)
  }
}
```

### 音频格式设置
```json
{
  "audio_formats": {
    "mp3": {
      "codec": "libmp3lame",
      "extension": ".mp3",
      "quality": "-q:a 2",          // 质量参数
      "description": "MP3 (高质量)"
    }
  }
}
```

### 输出设置
```json
{
  "output": {
    "default_directory": "extracted_audio",  // 默认输出目录
    "preserve_structure": true,              // 保持目录结构
    "overwrite_existing": false,             // 是否覆盖现有文件
    "create_subdirs": true                   // 是否创建子目录
  }
}
```

### 界面设置
```json
{
  "ui": {
    "show_progress": true,        // 显示进度条
    "confirm_before_start": true, // 开始前确认
    "show_file_details": true     // 显示文件详情
  }
}
```

## 支持的文件格式

### 输入视频格式
- MP4, AVI, MOV, WMV, FLV, WebM, MKV
- M4V, 3GP, OGV, TS, MTS, M2TS

### 输出音频格式
- **MP3**: 使用 libmp3lame 编码器，高质量压缩
- **AAC**: 标准 AAC 编码，适合移动设备
- **WAV**: PCM 无损音频
- **FLAC**: 无损压缩音频
- **M4A**: AAC 格式，适合 Apple 设备

## 质量参数说明

### MP3 质量参数
- `-q:a 0`: 最高质量 (~245 kbps)
- `-q:a 2`: 高质量 (~190 kbps) - 默认
- `-q:a 4`: 标准质量 (~165 kbps)
- `-q:a 6`: 较低质量 (~130 kbps)

### AAC 质量参数
- `-b:a 320k`: 高质量
- `-b:a 192k`: 标准质量
- `-b:a 128k`: 较低质量

## 使用示例

### 1. 扫描目录提取音频
```
1. 运行工具
2. 选择 "扫描目录"
3. 输入视频目录路径: D:\Videos
4. 选择是否递归扫描
5. 选择音频格式: MP3
6. 设置输出目录
7. 确认并开始处理
```

### 2. 手动指定文件
```
1. 选择 "手动输入文件路径"
2. 逐个输入文件路径
3. 输入空行结束
4. 选择处理选项
```

### 3. 从剪贴板批量处理
```
1. 复制文件路径列表到剪贴板
2. 选择 "从剪贴板粘贴路径"
3. 自动解析路径列表
4. 选择处理选项
```

## 故障排除

### 编码错误 (UnicodeDecodeError)
如果遇到类似 `'gbk' codec can't decode byte` 的错误：

1. **Windows 用户**:
   ```bash
   # 在命令行中设置环境变量
   set PYTHONIOENCODING=utf-8
   chcp 65001
   
   # 或使用提供的 .bat 脚本启动
   audiov_start.bat
   ```

2. **配置文件设置**:
   在 `config.json` 中已经包含了编码处理设置：
   ```json
   {
     "ffmpeg": {
       "encoding": "utf-8",
       "hide_banner": true,
       "log_level": "error"
     }
   }
   ```

### FFmpeg 未找到
```bash
# Windows - 下载 FFmpeg 并添加到 PATH
# 或者在配置文件中指定完整路径
{
  "ffmpeg": {
    "executable_path": "C:\\ffmpeg\\bin\\ffmpeg.exe"
  }
}
```

### 权限错误
- 确保对输出目录有写权限
- 以管理员身份运行 (如果需要)

### 内存不足
- 减少 batch_size 设置
- 逐个处理大文件

### 音频提取失败
- 检查视频文件是否包含音频轨道
- 尝试不同的音频格式
- 检查输出目录是否有足够空间

## 项目结构

```
src/audiov/
├── __init__.py           # 包初始化
├── __main__.py           # 主入口点
├── config.json           # 配置文件
├── config.py             # 配置管理
├── ffmpeg_wrapper.py     # FFmpeg 封装
├── file_handler.py       # 文件处理
└── interactive.py        # 交互界面
```

## 开发说明

### 扩展音频格式
在 `config.json` 的 `audio_formats` 中添加新格式：
```json
{
  "ogg": {
    "codec": "libvorbis",
    "extension": ".ogg",
    "quality": "-q:a 5",
    "description": "OGG Vorbis"
  }
}
```

### 自定义 FFmpeg 参数
在质量参数中可以添加任何 FFmpeg 支持的参数：
```json
{
  "quality": "-ab 320k -ar 48000 -ac 2"
}
```

## 许可证

MIT License

## 更新日志

### v0.1.0
- 初始版本
- 支持基本音频提取功能
- Rich 终端界面
- JSON 配置管理
- 批量处理支持
