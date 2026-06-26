@echo off
chcp 65001 >nul
echo ====================================
echo  AI Autonomy Radar - 启动中...
echo ====================================
cd /d "%~dp0"

REM 检查Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到Python, 请先安装Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖 (首次运行)
if not exist "venv\" (
    echo [首次运行] 创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    call venv\Scripts\activate.bat
)

REM 启动服务
echo [启动] 后端服务 http://localhost:7777
echo [前端] 浏览器打开 http://localhost:7777
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 7777 --reload

pause