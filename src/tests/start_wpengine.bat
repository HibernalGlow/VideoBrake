@echo off
echo 启动 Wallpaper Engine 工坊管理工具...
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    uv pip install streamlit pandas plotly
    if errorlevel 1 (
        echo 依赖安装失败，请手动运行: pip install streamlit pandas plotly
        pause
        exit /b 1
    )
)

echo 启动 Web 界面...
echo 访问地址: http://localhost:8501
echo 按 Ctrl+C 停止服务
echo.

streamlit run src/engingv/app.py --server.port 8501 --server.address localhost

pause
