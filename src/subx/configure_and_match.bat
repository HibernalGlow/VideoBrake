@echo off
chcp 65001 >nul
echo =====================================
echo SubX-CLI 配置和字幕匹配脚本
echo =====================================
echo.

set SUBX_EXE=%~dp0subx.exe

if not exist "%SUBX_EXE%" (
    echo 错误：找不到 subx.exe 文件
    pause
    exit /b 1
)

echo 当前使用的 SubX 可执行文件：%SUBX_EXE%
echo.

echo =====================================
echo 步骤 1: 配置 AI 提供商
echo =====================================
echo.
echo 选择 AI 提供商：
echo 1. OpenRouter (推荐 - 免费 DeepSeek 模型)
echo 2. OpenAI
echo 3. Azure OpenAI
echo 4. 跳过配置 (如果已配置)
echo.
set /p choice="请选择 (1-4): "

if "%choice%"=="1" goto openrouter
if "%choice%"=="2" goto openai
if "%choice%"=="3" goto azure
if "%choice%"=="4" goto skip_config
echo 无效选择，默认使用 OpenRouter
goto openrouter

:openrouter
echo.
echo 配置 OpenRouter...
set /p api_key="请输入您的 OpenRouter API Key: "
if "%api_key%"=="" (
    echo 错误：API Key 不能为空
    goto openrouter
)
set OPENROUTER_API_KEY=%api_key%
"%SUBX_EXE%" config set ai.provider openrouter
"%SUBX_EXE%" config set ai.model "deepseek/deepseek-r1-0528:free"
echo OpenRouter 配置完成！
goto config_done

:openai
echo.
echo 配置 OpenAI...
set /p api_key="请输入您的 OpenAI API Key: "
if "%api_key%"=="" (
    echo 错误：API Key 不能为空
    goto openai
)
set OPENAI_API_KEY=%api_key%
"%SUBX_EXE%" config set ai.provider openai
"%SUBX_EXE%" config set ai.model "gpt-4o-mini"
echo OpenAI 配置完成！
goto config_done

:azure
echo.
echo 配置 Azure OpenAI...
set /p api_key="请输入您的 Azure OpenAI API Key: "
set /p endpoint="请输入您的 Azure OpenAI Endpoint: "
set /p deployment="请输入您的部署 ID: "
if "%api_key%"=="" (
    echo 错误：API Key 不能为空
    goto azure
)
set AZURE_OPENAI_API_KEY=%api_key%
set AZURE_OPENAI_ENDPOINT=%endpoint%
set AZURE_OPENAI_API_VERSION=2025-04-01-preview
"%SUBX_EXE%" config set ai.provider azure-openai
"%SUBX_EXE%" config set ai.model "%deployment%"
"%SUBX_EXE%" config set ai.api_version "2025-04-01-preview"
echo Azure OpenAI 配置完成！
goto config_done

:skip_config
echo 跳过 AI 配置...

:config_done
echo.
echo =====================================
echo 步骤 2: 配置其他设置
echo =====================================
echo.
echo 正在配置推荐设置...

REM 配置备份功能
"%SUBX_EXE%" config set general.backup_enabled true

REM 配置并行处理
"%SUBX_EXE%" config set parallel.max_workers 4
"%SUBX_EXE%" config set parallel.task_queue_size 1000

REM 配置匹配信心度
"%SUBX_EXE%" config set ai.temperature 0.3
"%SUBX_EXE%" config set ai.retry_attempts 3

echo 基础配置完成！
echo.

echo =====================================
echo 步骤 3: 执行字幕匹配 (试运行)
echo =====================================
echo.
echo 即将执行以下操作：
echo 源字幕目录：F:\1MOV\av1\srt
echo 目标视频目录：F:\1MOV\av1\#整理完成
echo.
echo 模式选择：
echo 1. 仅试运行 (dry-run) - 预览操作但不实际执行
echo 2. 复制模式 - 复制字幕到视频目录 (保留原文件)
echo 3. 移动模式 - 移动字幕到视频目录 (删除原文件)
echo.
set /p mode="请选择模式 (1-3): "

if "%mode%"=="1" goto dry_run
if "%mode%"=="2" goto copy_mode
if "%mode%"=="3" goto move_mode
echo 无效选择，默认执行试运行
goto dry_run

:dry_run
echo.
echo =====================================
echo 执行试运行 (预览模式)
echo =====================================
echo.
"%SUBX_EXE%" match -i "F:\1MOV\av1\srt" -i "F:\1MOV\av1\#整理完成" --recursive --dry-run --copy
echo.
echo 试运行完成！请查看上面的输出，确认操作正确后可以选择实际执行。
echo.
set /p confirm="是否要执行实际的复制操作？(y/n): "
if /i "%confirm%"=="y" (
    echo 执行实际复制操作...
    "%SUBX_EXE%" match -i "F:\1MOV\av1\srt" -i "F:\1MOV\av1\#整理完成" --recursive --copy --backup
    echo 复制操作完成！
) else (
    echo 操作已取消。
)
goto end

:copy_mode
echo.
echo =====================================
echo 执行复制模式
echo =====================================
echo.
echo 正在执行字幕匹配和复制操作...
"%SUBX_EXE%" match -i "F:\1MOV\av1\srt" -i "F:\1MOV\av1\#整理完成" --recursive --copy --backup
echo 复制操作完成！
goto end

:move_mode
echo.
echo =====================================
echo 执行移动模式
echo =====================================
echo.
echo 警告：移动模式将删除原始字幕文件！
set /p confirm="确定要继续吗？(y/n): "
if /i not "%confirm%"=="y" (
    echo 操作已取消。
    goto end
)
echo 正在执行字幕匹配和移动操作...
"%SUBX_EXE%" match -i "F:\1MOV\av1\srt" -i "F:\1MOV\av1\#整理完成" --recursive --move --backup
echo 移动操作完成！
goto end

:end
echo.
echo =====================================
echo 脚本执行完成
echo =====================================
echo.
echo 可用的其他命令：
echo 查看配置：%SUBX_EXE% config list
echo 清除缓存：%SUBX_EXE% cache clear
echo 格式转换：%SUBX_EXE% convert --format srt "目录路径"
echo 时间同步：%SUBX_EXE% sync --batch "媒体目录"
echo.
pause
