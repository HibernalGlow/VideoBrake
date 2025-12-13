# 📹 Coser 视频自动分类系统

> **让机器替你看视频，认出角色，自动归档。**

一个基于 AI 的本地视频自动整理系统，能够：

- 🎯 **智能截图**：自动提取多角度、有人脸、不重复的关键帧
- 🤖 **AI 识别**：使用 Gemini 1.5 Flash 识别 Coser 扮演的角色
- 📂 **自动归档**：创建角色文件夹并自动整理视频

---

## ✨ 特性

### 🔍 三重过滤机制

1. **场景检测** - 使用 PySceneDetect 提取不同镜头的画面
2. **人脸过滤** - 使用 MediaPipe 过滤无人脸的画面
3. **视觉去重** - 使用 ImageHash 剔除相似画面

### 🎯 智能识别

- 使用 Gemini 1.5 Flash，速度快、成本低
- JSON 模式确保输出格式稳定
- 支持多图联合识别，提高准确率

### 🛡️ 安全可靠

- 测试模式（`--dry-run`）预览结果
- 自动处理文件名冲突
- 支持限制处理数量（`--limit`）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制环境变量模板：

```bash
copy .env.example .env
```

编辑 `.env` 文件，填入你的 Gemini API Key：

```env
GEMINI_API_KEY=你的API密钥
```

> 💡 获取 API Key: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

### 3. 运行系统

**测试模式**（推荐首次使用）：

```bash
python main.py "D:\Videos\Cosplay" --dry-run --limit 3
```

**实际运行**：

```bash
python main.py "D:\Videos\Cosplay"
```

---

## 📖 使用指南

### 基本命令

```bash
# 查看帮助
python main.py --help

# 测试模式（不移动文件）
python main.py /path/to/videos --dry-run

# 限制处理数量
python main.py /path/to/videos --limit 5

# 递归处理子目录
python main.py /path/to/videos --recursive

# 处理单个视频
python main.py /path/to/videos --single video.mp4
```

### 处理流程

```
┌─────────────┐
│  扫描视频   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ 场景检测    │────▶│ 提取关键帧   │
└─────────────┘     └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  人脸过滤    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  视觉去重    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  AI 识别     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  创建文件夹  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  移动视频    │
                    └──────────────┘
```

---

## ⚙️ 配置说明

编辑 `config.py` 可以调整以下参数：

### 视频处理

```python
SCENE_THRESHOLD = 27.0           # 场景检测阈值（越低越敏感）
MAX_FRAMES_PER_VIDEO = 10        # 每个视频最多提取的帧数
MIN_SCENE_LENGTH = 2.0           # 最小场景长度（秒）
```

### 人脸检测

```python
FACE_DETECTION_CONFIDENCE = 0.5  # 人脸检测置信度
MIN_FACE_SIZE_RATIO = 0.1        # 最小人脸大小比例
```

### 图像去重

```python
HASH_DIFF_THRESHOLD = 10         # 哈希差异阈值（越小越严格）
```

### 文件操作

```python
MOVE_FILES = True                # True=移动，False=复制
UNKNOWN_FOLDER_NAME = "未识别角色"  # 未识别视频的文件夹名
```

---

## 🧪 独立模块测试

### 测试截图模块

```bash
python frame_extractor.py video.mp4
```

会在 `test_output/` 目录生成提取的帧。

### 测试识别模块

```bash
python character_identifier.py image1.jpg image2.jpg
```

会输出识别结果。

### 测试文件组织模块

```bash
python file_organizer.py /path/to/videos
```

会列出所有视频文件。

---

## 📊 输出示例

```
====================================================
🚀 初始化视频分类系统
====================================================
✓ 人脸检测器初始化完成
✓ AI 模型初始化完成: gemini-1.5-flash
✓ 文件组织器初始化完成
====================================================

找到 15 个视频文件
开始处理...

====================================================
📹 处理: cosplay_video_001.mp4
====================================================

🎬 开始处理视频: cosplay_video_001.mp4
  ✓ 场景检测完成，获得 8 个候选帧
  ✓ 人脸过滤完成，保留 6 个有人脸的帧
  ✓ 去重完成，最终保留 4 个帧

🤖 开始 AI 识别（使用 4 张图片）...
  ✓ 识别成功: 优菈 (原神)

  ✓ 已移动到: 优菈(原神)/cosplay_video_001.mp4

====================================================
📊 处理统计
====================================================
总视频数: 15
✓ 成功识别并分类: 12
⚠ 未检测到人脸: 1
⚠ 无法识别角色: 2
❌ 处理错误: 0

成功率: 80.0%
====================================================

====================================================
📊 文件组织摘要
====================================================
  📁 优菈(原神): 5 个视频
  📁 2B(尼尔:自动人形): 3 个视频
  📁 甘雨(原神): 2 个视频
  📁 雷电将军(原神): 2 个视频
  📁 未识别角色: 2 个视频
====================================================
```

---

## 🔧 故障排除

### 安装问题

**OpenCV 安装失败**：

```bash
pip install opencv-python-headless
```

**MediaPipe 安装失败**：

```bash
pip install mediapipe --no-deps
pip install opencv-python numpy
```

### 运行问题

**API 请求失败**：

- 检查网络连接
- 验证 API Key 是否正确
- 如需代理，在 `.env` 中配置 `HTTP_PROXY`

**未检测到人脸**：

- 降低 `FACE_DETECTION_CONFIDENCE`
- 降低 `MIN_FACE_SIZE_RATIO`

**场景检测不准确**：

- 调整 `SCENE_THRESHOLD`（默认 27.0）
- 增加 `MAX_FRAMES_PER_VIDEO`

**识别率低**：

- 增加 `MAX_FRAMES_PER_VIDEO`
- 调整 `HASH_DIFF_THRESHOLD` 增加帧多样性
- 检查视频质量（模糊、抖动会影响识别）

---

## 📁 项目结构

```
coserv/
├── config.py                  # 配置中心
├── frame_extractor.py         # 智能截图模块
├── character_identifier.py    # AI 识别模块
├── file_organizer.py          # 文件管理模块
├── main.py                    # 主程序入口
├── requirements.txt           # 依赖列表
├── .env.example              # 环境变量模板
└── README.md                 # 本文件
```

---

## 🛣️ 路线图

- [x] 场景检测
- [x] 人脸过滤
- [x] 视觉去重
- [x] AI 识别
- [x] 自动归档
- [ ] Web UI 界面
- [ ] 批量重试失败项
- [ ] 自定义角色映射
- [ ] 支持更多 AI 模型
- [ ] 性能优化（并行处理）

---

## 📄 许可证

MIT License

---

## 🙏 致谢

本项目使用以下优秀的开源库：

- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) - 场景检测
- [MediaPipe](https://github.com/google/mediapipe) - 人脸检测
- [ImageHash](https://github.com/JohannesBuchner/imagehash) - 图像去重
- [Google Generative AI](https://ai.google.dev/) - AI 识别

---

**⭐ 如果这个项目帮到了你，请给个 Star！**
