@echo off
chcp 65001 > nul

echo 🚀 启动期货套保策略分析工具...
echo.

REM 检查Python版本
python --version
echo.

REM 检查依赖
echo 🔍 检查依赖库...
python -c "import streamlit, pandas, numpy, plotly, akshare, statsmodels, scipy" 2>nul
if errorlevel 1 (
    echo ❌ 缺少依赖包
    echo 请运行: pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ 所有依赖包已安装

REM 创建缓存目录
if not exist cache mkdir cache
echo ✅ 缓存目录已准备

REM 启动应用
echo.
echo 🌐 启动Streamlit应用...
echo 应用将在浏览器中打开: http://localhost:8501
echo.
echo 如需停止应用，请按 Ctrl+C
echo ==================================

streamlit run app.py

pause