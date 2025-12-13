# 🛠️ Gemini CLI 安装指南

本项目使用 **Gemini CLI 命令行工具**而不是 Python API，这样更灵活且不需要额外的 Python 依赖。

---

## 📦 安装方法

### 方法 1：使用 npm 安装（推荐）

```bash
npm install -g @google/generative-ai-cli
```

安装完成后，验证安装：

```bash
gemini --version
```

### 方法 2：使用 pip 安装

```bash
pip install google-generativeai[cli]
```

安装完成后，验证：

```bash
gemini --version
```

### 方法 3：下载二进制文件

1. 访问 [Gemini CLI Releases](https://github.com/google/generative-ai-cli/releases)
2. 下载对应系统的二进制文件
3. 将其添加到系统 PATH，或在 `.env` 中指定完整路径

---

## ⚙️ 配置

### 1. 设置 API Key（如需要）

某些 CLI 版本需要 API Key，配置方法：

**方法 A：环境变量**

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="你的API密钥"

# Windows CMD
set GEMINI_API_KEY=你的API密钥

# Linux/Mac
export GEMINI_API_KEY="你的API密钥"
```

**方法 B：使用 CLI 配置命令**

```bash
gemini config set api-key "你的API密钥"
```

**方法 C：在项目 .env 文件中配置**

```bash
# 编辑 .env 文件
GEMINI_API_KEY=你的API密钥
```

### 2. 验证配置

测试 CLI 是否正常工作：

```bash
# 基本测试
gemini generate --prompt "你好"

# 带图片测试（如果你有测试图片）
gemini generate --prompt "描述这张图片" --image test.jpg --output-format json
```

---

## 🔧 自定义 CLI 路径

如果 `gemini` 命令不在系统 PATH 中，或者你想使用特定版本，可以在 `.env` 配置：

```bash
# Windows 示例
GEMINI_CLI_PATH=C:\tools\gemini.exe

# Linux/Mac 示例
GEMINI_CLI_PATH=/usr/local/bin/gemini

# 或使用相对路径
GEMINI_CLI_PATH=./tools/gemini
```

---

## 🧪 测试 CLI

创建一个测试脚本 `test_cli.py`：

```python
import subprocess
import json

# 测试基本调用
result = subprocess.run(
    ["gemini", "generate", "--prompt", "你好，请用JSON格式回复：{\"message\": \"你的回复\"}", "--output-format", "json"],
    capture_output=True,
    text=True
)

print("返回码:", result.returncode)
print("输出:", result.stdout)
print("错误:", result.stderr)

# 尝试解析 JSON
try:
    data = json.loads(result.stdout)
    print("解析成功:", data)
except:
    print("JSON 解析失败")
```

运行测试：

```bash
python test_cli.py
```

---

## ❓ 常见问题

### Q: 提示 "gemini: command not found"

**A:**

1. 确认是否安装成功：`npm list -g @google/generative-ai-cli`
2. 检查 npm 全局目录是否在 PATH 中
3. 尝试重启终端
4. 或直接在 `.env` 中指定完整路径

### Q: CLI 调用超时

**A:**

1. 检查网络连接
2. 在 `config.py` 中增加 `CLI_TIMEOUT` 值
3. 如果在国内，可能需要配置代理

### Q: 返回格式不是 JSON

**A:**

1. 确保使用 `--output-format json` 参数
2. 检查 CLI 版本是否支持 `--output-format`
3. 如不支持，需要在 prompt 中明确要求 JSON 格式

### Q: 需要代理访问

**A:**
在 `.env` 中配置：

```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 📚 CLI 常用命令

```bash
# 查看版本
gemini --version

# 查看帮助
gemini --help
gemini generate --help

# 简单文本生成
gemini generate --prompt "描述一下原神角色优菈"

# 分析图片
gemini generate --prompt "这是什么角色？" --image photo.jpg

# 指定模型
gemini generate --model gemini-1.5-flash --prompt "你好"

# JSON 输出
gemini generate --prompt "返回JSON：{\"name\": \"角色名\"}" --output-format json

# 多图片输入
gemini generate --prompt "对比这些图片" --image img1.jpg --image img2.jpg
```

---

## 🔗 相关链接

- [Gemini CLI GitHub](https://github.com/google/generative-ai-cli)
- [Gemini API 文档](https://ai.google.dev/docs)
- [获取 API Key](https://makersuite.google.com/app/apikey)

---

**✅ 安装完成后，运行 `python config.py` 检查配置是否正确！**
