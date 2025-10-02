#!/bin/bash

# 期货套保策略分析工具启动脚本

echo "🚀 启动期货套保策略分析工具..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  未检测到虚拟环境"
    echo "建议使用虚拟环境运行:"
    echo "  python3 -m venv hedge_env"
    echo "  source hedge_env/bin/activate"
    echo ""
fi

# 检查依赖
echo "🔍 检查依赖库..."
required_packages=("streamlit" "pandas" "numpy" "plotly" "akshare" "statsmodels" "scipy")
missing_packages=()

for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -ne 0 ]; then
    echo "❌ 缺少以下依赖包: ${missing_packages[*]}"
    echo "请运行: pip install -r requirements.txt"
    exit 1
else
    echo "✅ 所有依赖包已安装"
fi

# 创建必要目录
mkdir -p cache
echo "✅ 缓存目录已准备"

# 启动应用
echo "🌐 启动Streamlit应用..."
echo "应用将在浏览器中打开: http://localhost:8501"
echo ""
echo "如需停止应用，请按 Ctrl+C"
echo "=================================="

# 启动Streamlit
streamlit run app.py --server.headless=false --server.port=8501