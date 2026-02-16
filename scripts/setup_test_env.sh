#!/bin/bash

# Arya Video Agent - 本地测试安装脚本
# 用途：快速安装所有测试依赖

set -e

echo "======================================"
echo "📋 Arya Video Agent - 本地测试环境配置"
echo "======================================"
echo ""

# 检查Python版本
echo "🔍 检查Python版本..."
python3 --version || {
    echo "❌ Python 3未安装"
    exit 1
}

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔨 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "✅ 虚拟环境已存在"
    source venv/bin/activate
fi

echo ""
echo "📦 安装测试依赖..."

# 升级pip
echo "1️⃣ 升级pip到最新版本..."
pip install --upgrade pip setuptools wheel

# 安装测试依赖
echo "2️⃣ 安装pytest和插件..."
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1
pip install pytest-mock==3.12.0
pip install pytest-cov==4.1.0

# 安装代码质量工具
echo "3️⃣ 安装代码质量工具..."
pip install black==23.12.1
pip install flake8==7.0.0
pip install mypy==1.8.0
pip install isort==5.13.2

echo ""
echo "✅ 所有依赖安装完成！"
echo ""

# 验证安装
echo "🔍 验证pytest安装..."
pytest --version || {
    echo "❌ pytest安装失败"
    exit 1
}

echo "🔍 验证pytest-asyncio安装..."
python3 -c "import pytest_asyncio; print(f'pytest-asyncio {pytest_asyncio.__version__}')" || {
    echo "❌ pytest-asyncio安装失败"
    exit 1
}

echo "🔍 验证pytest-mock安装..."
python3 -c "import pytest_mock; print(f'pytest-mock {pytest_mock.__version__}')" || {
    echo "❌ pytest-mock安装失败"
    exit 1
}

echo "🔍 验证pytest-cov安装..."
python3 -c "import pytest_cov; print(f'pytest-cov {pytest_cov.__version__}')" || {
    echo "❌ pytest-cov安装失败"
    exit 1
}

echo ""
echo "======================================"
echo "✅ 测试环境配置完成！"
echo "======================================"
echo ""
echo "📝 下一步："
echo "1. 运行测试：pytest tests/ -v"
echo "2. 查看覆盖率：pytest tests/ --cov=app --cov-report=html"
echo "3. 退出虚拟环境：deactivate"
echo ""
