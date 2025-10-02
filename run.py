"""
期货套保策略分析工具 - 启动脚本
"""

import subprocess
import sys
import os

def main():
    """主函数"""
    print("🚀 启动期货套保策略分析工具...")

    # 检查依赖
    try:
        import streamlit
        import pandas
        import numpy
        import plotly
        import akshare
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return

    # 创建cache目录
    if not os.path.exists("cache"):
        os.makedirs("cache")
        print("✅ 创建缓存目录")

    # 启动Streamlit应用
    print("🌐 启动Web应用...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ 启动失败")
        return

if __name__ == "__main__":
    main()