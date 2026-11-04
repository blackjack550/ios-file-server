@echo off
chcp 65001 >nul
title iOS 文件接收服务器（端口 8900）
cd /d "%~dp0"

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未检测到 Python，请先安装 Python 3.10+ 并勾选 "Add Python to PATH"
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/3] 检查依赖...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 首次运行，正在安装 Flask 依赖，请稍候...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败，请检查网络后重试
        pause
        exit /b 1
    )
)

echo [3/3] 启动服务器（关闭本窗口即停止服务）...
echo.
python app.py
echo.
echo 服务已停止
pause
