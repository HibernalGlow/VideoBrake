@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 Coser 视频自动分类系统 - 快速启动
echo ========================================
echo.

REM 检查是否已创建 .env 文件
if not exist .env (
    echo ⚠ 未找到 .env 文件，正在创建...
    copy .env.example .env
    echo.
    echo ✓ 已创建 .env 文件
    echo 📝 请编辑 .env 文件，填入你的 GEMINI_API_KEY
    echo.
    pause
    exit /b
)

REM 检查依赖是否安装
python -c "import cv2" 2>nul
if errorlevel 1 (
    echo ⚠ 检测到依赖未安装，开始安装...
    echo.
    pip install -r requirements.txt
    echo.
)

echo ✓ 环境检查完成
echo.
echo 请选择运行模式：
echo.
echo 1. 测试模式（处理 3 个视频，不移动文件）
echo 2. 小批量测试（处理 10 个视频）
echo 3. 完整运行（处理所有视频）
echo 4. 处理单个视频
echo 5. 查看配置
echo 6. 退出
echo.

set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto test_mode
if "%choice%"=="2" goto batch_test
if "%choice%"=="3" goto full_run
if "%choice%"=="4" goto single_video
if "%choice%"=="5" goto show_config
if "%choice%"=="6" goto end

echo ❌ 无效选项
pause
exit /b

:test_mode
echo.
set /p video_dir=请输入视频文件夹路径: 
echo.
echo 开始测试模式...
python main.py "%video_dir%" --dry-run --limit 3
pause
exit /b

:batch_test
echo.
set /p video_dir=请输入视频文件夹路径: 
echo.
echo 开始小批量测试...
python main.py "%video_dir%" --limit 10
pause
exit /b

:full_run
echo.
set /p video_dir=请输入视频文件夹路径: 
echo.
echo ⚠ 即将处理所有视频，确认继续？
pause
echo.
python main.py "%video_dir%"
pause
exit /b

:single_video
echo.
set /p video_file=请输入视频文件路径: 
echo.
echo 开始处理单个视频...
python main.py . --single "%video_file%" --dry-run
pause
exit /b

:show_config
echo.
python config.py
pause
exit /b

:end
echo.
echo 👋 再见！
exit /b
