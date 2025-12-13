# Gemini 识别和重命名工作流程

## 概述

使用 scan.py 生成图片后，通过 Gemini 识别角色并重命名文件夹。

## 步骤 1: 生成图片

```bash
# 扫描文件夹并生成图片（不生成 JSON）
python cli.py scan <视频文件夹路径> --no-json

# 或者使用自定义参数
python cli.py scan <视频文件夹路径> --no-json --max-frames 3 --image-size 30
```

这将在 `<视频文件夹路径>/coserv_output/frames_时间戳/` 下生成每个文件夹的代表图片。

## 步骤 2: 使用 Gemini 识别

### 推荐的 Prompt 模板

````
我需要你帮我识别这些 Cosplay 视频文件夹中的角色和作品。

任务说明：
1. 我会给你展示多个文件夹，每个文件夹包含从视频中提取的关键帧图片
2. 请识别图片中 Cosplayer 扮演的角色名称和作品名称
3. 为每个文件夹生成一个重命名命令

输出格式要求：
- 对于每个文件夹，输出一行 PowerShell 重命名命令
- 格式：Rename-Item "原文件夹名" "[角色名_作品名] 原文件夹名"
- 如果无法识别，使用：Rename-Item "原文件夹名" "[未知角色_未知] 原文件夹名"

示例输出：
```powershell
# 进入视频目录
cd "D:\Videos\Cosplay"

# 重命名命令
Rename-Item "folder1" "[优菈_原神] folder1"
Rename-Item "folder2" "[2B_尼尔自动人形] folder2"
Rename-Item "folder3" "[未知角色_未知] folder3"
````

注意事项：

1. 角色名和作品名之间用下划线 "\_" 分隔
2. 使用中括号 "[]" 包裹标签，方便视觉识别
3. 保留原文件夹名，只在前面添加标签
4. 如果一个文件夹有多个角色，选择最主要的角色
5. 作品名使用官方中文译名（如果有的话）

现在请帮我识别以下文件夹：
[然后拖入 coserv_output/frames_时间戳/ 整个文件夹]

```

### 更简洁的 Prompt（快速版）

```

识别这些 Cosplay 图片中的角色和作品，为每个文件夹生成 PowerShell 重命名命令。

输出格式：
Rename-Item "文件夹名" "[角色名_作品名] 文件夹名"

如果无法识别，输出：
Rename-Item "文件夹名" "[未知角色_未知] 文件夹名"

注意：

- 保留原文件夹名
- 文件夹路径：[拖入文件夹]

````

## 步骤 3: 执行重命名

1. 复制 Gemini 生成的命令
2. 在 PowerShell 中执行：

```powershell
# 进入视频目录
cd "D:\你的视频路径"

# 粘贴并执行 Gemini 生成的重命名命令
Rename-Item "folder1" "[优菈_原神] folder1"
Rename-Item "folder2" "[2B_尼尔自动人形] folder2"
# ... 更多命令
````

## 步骤 4: 验证结果

重命名后，文件夹结构将变为：

```
视频目录/
├── [优菈_原神] cosplay_video1/
├── [2B_尼尔自动人形] cosplay_video2/
├── [甘雨_原神] another_folder/
└── [未知角色_未知] random_video/
```

## 高级技巧

### 批量处理大量文件夹

如果文件夹太多，可以分批处理：

```bash
# 只处理前 10 个文件夹
python cli.py scan <路径> --no-json --limit 10

# 等 Gemini 处理完后，继续下一批
# 注意：需要手动移动已处理的文件夹或使用不同的时间戳
```

### 自定义标签格式

如果你想使用其他格式，可以修改 Gemini prompt：

**方案 A - 使用括号**

```
格式：Rename-Item "原名" "（角色名-作品名）原名"
示例：Rename-Item "folder1" "（优菈-原神）folder1"
```

**方案 B - 使用下划线前缀**

```
格式：Rename-Item "原名" "角色名_作品名_原名"
示例：Rename-Item "folder1" "优菈_原神_folder1"
```

**方案 C - 使用井号标签**

```
格式：Rename-Item "原名" "#角色名 #作品名 原名"
示例：Rename-Item "folder1" "#优菈 #原神 folder1"
```

## 后续处理

重命名后，你可以：

1. **按角色筛选**：在文件管理器中搜索 `[优菈_`
2. **按作品筛选**：搜索 `_原神]`
3. **整理到子文件夹**：手动或使用脚本按作品分类

### 自动分类脚本（可选）

```powershell
# 按作品分类到子文件夹
$folders = Get-ChildItem -Directory | Where-Object { $_.Name -match '^\[(.+?)_(.+?)\]' }

foreach ($folder in $folders) {
    if ($folder.Name -match '^\[(.+?)_(.+?)\]') {
        $character = $matches[1]
        $source = $matches[2]

        # 创建作品文件夹
        $sourceFolder = $source
        if (-not (Test-Path $sourceFolder)) {
            New-Item -ItemType Directory -Path $sourceFolder
        }

        # 移动文件夹
        Move-Item $folder.FullName -Destination $sourceFolder
    }
}
```

## 示例完整工作流程

```bash
# 1. 扫描生成图片
cd D:\1VSCODE\Projects\PackU\VideoBrake\src\coserv
python cli.py scan "D:\Videos\Cosplay" --no-json --max-frames 3

# 2. 在 Gemini 中上传图片并获取重命名命令
# （拖入 D:\Videos\Cosplay\coserv_output\frames_时间戳\ 文件夹）

# 3. 执行重命名
cd "D:\Videos\Cosplay"
# 粘贴 Gemini 生成的命令

# 4. 清理临时文件（可选）
Remove-Item -Recurse "coserv_output"
```

## 常见问题

### Q: 为什么使用重命名而不是移动到子文件夹？

A: 重命名保留了原始文件夹结构 ��� 便于撤销，且不改变文件路径深度。

### Q: 如果 Gemini 识别错误怎么办？

A: 可以手动修改 Gemini 生成的命令，或者重命名后再手动调整。

### Q: 可以在 Linux/Mac 上使用吗？

A: 可以，将 PowerShell 命令改为 bash：

```bash
mv "原名" "[角色名_作品名] 原名"
```

### Q: 重命名后如何撤销？

A: 使用正则替换：

```powershell
Get-ChildItem -Directory | Where-Object { $_.Name -match '^\[.+?\] (.+)$' } |
    Rename-Item -NewName { $_.Name -replace '^\[.+?\] (.+)$', '$1' }
```

## 推荐的标签命名规范

- **角色名**：使用官方中文名，如 "优菈"、"2B"
- **作品名**：使用简短的中文译名，如 "原神"、"尼尔自动人形"
- **特殊情况**：
  - 多个角色：选主角或用 "+" 连接，如 "优菈+琴"
  - 无法识别：统一使用 "未知角色\_未知"
  - 真人而非 Cosplay：使用 "真人\_写真" 或跳过

## 进阶：自动化脚本（未来扩展）

如果需要完全自动化，可以考虑：

1. 使用 Gemini API 批量识别
2. 生成并自动执行重命名脚本
3. 集成到 identify.py 和 process.py 中

但目前推荐手动方式，因为：

- 更可控，可以检查识别结果
- 避免 API 调用费用
- 可以处理特殊情况
