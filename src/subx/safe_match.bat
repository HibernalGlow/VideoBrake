@echo off
chcp 65001 >nul
echo =====================================
echo SubX-CLI 安全字幕匹配脚本 (改进版)
echo =====================================
echo.

set SUBX_EXE=%~dp0subx.exe
set "SOURCE_DIR=F:\1MOV\av1\srt"
set "TARGET_DIR=F:\1MOV\av1\#整理完成"

if not exist "%SUBX_EXE%" (
    echo 错误：找不到 subx.exe 文件
    pause
    exit /b 1
)

echo 当前配置：
echo SubX 可执行文件：%SUBX_EXE%
echo 源字幕目录：%SOURCE_DIR%
echo 目标视频目录：%TARGET_DIR%
echo.

echo =====================================
echo 步骤 1: 检测字幕文件编码
echo =====================================
echo.
echo 正在检测字幕文件编码问题...
echo.

"%SUBX_EXE%" detect-encoding -i "%SOURCE_DIR%" --recursive --verbose

echo.
echo =====================================
echo 步骤 2: 配置 SubX 以处理编码问题
echo =====================================
echo.
echo 正在配置编码检测设置...

REM 降低编码检测信心度，提高容错性
"%SUBX_EXE%" config set formats.encoding_detection_confidence 0.6

REM 设置默认编码为 UTF-8
"%SUBX_EXE%" config set formats.default_encoding "utf-8"

REM 启用样式保留，可能有助于处理特殊字符
"%SUBX_EXE%" config set formats.preserve_styling false

REM 降低AI温度，提高匹配稳定性
"%SUBX_EXE%" config set ai.temperature 0.1

REM 增加重试次数
"%SUBX_EXE%" config set ai.retry_attempts 5

REM 启用备份
"%SUBX_EXE%" config set general.backup_enabled true

echo 配置完成！
echo.

echo =====================================
echo 步骤 3: 清除缓存并重新开始
echo =====================================
echo.
echo 清除之前的缓存数据...
"%SUBX_EXE%" cache clear
echo 缓存已清除。
echo.

echo =====================================
echo 步骤 4: 安全模式试运行
echo =====================================
echo.
echo 使用改进的设置执行试运行...
echo 注意：如果仍然出现错误，我们会尝试其他解决方案。
echo.

"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --dry-run --copy --confidence 70

set ERROR_LEVEL=%ERRORLEVEL%
if %ERROR_LEVEL% neq 0 (
    echo.
    echo =====================================
    echo 检测到错误，尝试替代方案
    echo =====================================
    echo.
    echo 错误代码：%ERROR_LEVEL%
    echo.
    echo 可能的解决方案：
    echo 1. 字幕文件包含特殊Unicode字符，需要预处理
    echo 2. 某些字幕文件编码不正确
    echo 3. 文件路径或名称包含特殊字符
    echo.
    echo 建议操作：
    echo A. 检查并修复有问题的字幕文件
    echo B. 转换所有字幕为标准SRT格式
    echo C. 手动处理有问题的文件
    echo.
    set /p action="选择操作 (A/B/C/Q退出): "
    
    if /i "%action%"=="A" goto check_files
    if /i "%action%"=="B" goto convert_first
    if /i "%action%"=="C" goto manual_process
    if /i "%action%"=="Q" goto end
    echo 无效选择，退出脚本。
    goto end
)

echo.
echo =====================================
echo 试运行成功完成
echo =====================================
echo.
echo 请查看上面的输出结果。如果一切正常，请选择是否继续：
echo.
echo 1. 执行复制操作 (保留原始字幕文件)
echo 2. 执行移动操作 (删除原始字幕文件)
echo 3. 退出
echo.
set /p choice="请选择 (1-3): "

if "%choice%"=="1" goto copy_exec
if "%choice%"=="2" goto move_exec
if "%choice%"=="3" goto end
echo 无效选择，退出脚本。
goto end

:check_files
echo.
echo =====================================
echo 检查问题文件
echo =====================================
echo.
echo 正在详细检查字幕文件...
"%SUBX_EXE%" detect-encoding -i "%SOURCE_DIR%" --recursive --verbose > encoding_report.txt 2>&1
echo.
echo 编码检测报告已保存到 encoding_report.txt
echo 请手动检查该文件，找出有问题的字幕文件。
echo.
echo 建议：
echo 1. 使用文本编辑器打开有问题的字幕文件
echo 2. 另存为 UTF-8 编码
echo 3. 删除文件中的特殊字符（如零宽度空格）
echo.
goto end

:convert_first
echo.
echo =====================================
echo 预先转换字幕格式
echo =====================================
echo.
echo 尝试将所有字幕转换为标准SRT格式...
echo 这可能有助于解决编码问题。
echo.
"%SUBX_EXE%" convert -i "%SOURCE_DIR%" --format srt --recursive --keep-original --encoding utf-8
echo.
echo 转换完成！现在尝试重新匹配...
goto restart_match

:manual_process
echo.
echo =====================================
echo 手动处理指南
echo =====================================
echo.
echo 请按以下步骤手动处理：
echo.
echo 1. 打开源字幕目录：%SOURCE_DIR%
echo 2. 逐个检查字幕文件
echo 3. 删除或修复包含特殊字符的文件
echo 4. 确保所有文件都是有效的UTF-8编码
echo 5. 重新运行此脚本
echo.
echo 常见问题文件特征：
echo - 文件名包含特殊字符
echo - 文件内容包含零宽度空格或其他不可见字符
echo - 编码不是UTF-8
echo.
goto end

:restart_match
echo.
echo 重新执行匹配操作...
"%SUBX_EXE%" cache clear
"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --dry-run --copy --confidence 70
if %ERRORLEVEL% neq 0 (
    echo 转换后仍有问题，建议手动检查字幕文件。
    goto end
)
echo.
echo 转换后匹配成功！请选择继续操作：
echo 1. 执行复制操作
echo 2. 执行移动操作
echo 3. 退出
echo.
set /p choice="请选择 (1-3): "
if "%choice%"=="1" goto copy_exec
if "%choice%"=="2" goto move_exec
goto end

:copy_exec
echo.
echo =====================================
echo 执行复制操作
echo =====================================
echo.
echo 正在执行字幕匹配和复制操作 (带备份)...
"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --copy --backup --confidence 70
if %ERRORLEVEL% neq 0 (
    echo 复制操作出现错误，请检查错误信息。
) else (
    echo 复制操作完成！字幕文件已复制到对应的视频目录。
)
goto end

:move_exec
echo.
echo =====================================
echo 执行移动操作
echo =====================================
echo.
echo 警告：移动操作将删除原始字幕文件！
set /p confirm="确定要继续吗？(y/n): "
if /i not "%confirm%"=="y" (
    echo 操作已取消。
    goto end
)
echo.
echo 正在执行字幕匹配和移动操作 (带备份)...
"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --move --backup --confidence 70
if %ERRORLEVEL% neq 0 (
    echo 移动操作出现错误，请检查错误信息。
) else (
    echo 移动操作完成！字幕文件已移动到对应的视频目录。
)
goto end

:end
echo.
echo =====================================
echo 操作完成
echo =====================================
echo.
echo 提示：
echo - 如需重新匹配：%SUBX_EXE% cache clear
echo - 如需转换字幕格式：%SUBX_EXE% convert --format srt "%TARGET_DIR%"
echo - 如需同步时间轴：%SUBX_EXE% sync --batch "%TARGET_DIR%"
echo - 如需检查编码：%SUBX_EXE% detect-encoding -i "%SOURCE_DIR%" --verbose
echo.
echo 如果仍有问题，请：
echo 1. 检查 encoding_report.txt 文件
echo 2. 手动修复有问题的字幕文件
echo 3. 使用文本编辑器将字幕另存为UTF-8格式
echo.
pause
