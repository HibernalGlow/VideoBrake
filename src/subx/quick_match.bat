@echo off
chcp 65001 >nul
echo =====================================
echo SubX-CLI 快速字幕匹配脚本
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
echo 步骤 1: 试运行 (预览操作)
echo =====================================
echo.
echo 正在执行试运行，预览将要执行的操作...
echo.

"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --dry-run --copy

echo.
echo =====================================
echo 试运行完成
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

:copy_exec
echo.
echo =====================================
echo 执行复制操作
echo =====================================
echo.
echo 正在执行字幕匹配和复制操作 (带备份)...
"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --copy --backup
echo.
echo 复制操作完成！字幕文件已复制到对应的视频目录。
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
"%SUBX_EXE%" match -i "%SOURCE_DIR%" -i "%TARGET_DIR%" --recursive --move --backup
echo.
echo 移动操作完成！字幕文件已移动到对应的视频目录。
goto end

:end
echo.
echo =====================================
echo 操作完成
echo =====================================
echo.
echo 提示：
echo - 如需重新匹配，请先清除缓存：%SUBX_EXE% cache clear
echo - 如需转换字幕格式：%SUBX_EXE% convert --format srt "%TARGET_DIR%"
echo - 如需同步时间轴：%SUBX_EXE% sync --batch "%TARGET_DIR%"
echo.
pause
