#!/bin/bash

# Arya Video Agent - 测试执行脚本
# 用途：运行测试套件并生成覆盖率报告

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "🧪 Arya Video Agent - 测试执行脚本"
echo "======================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，请先运行 setup_test_env.sh${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${GREEN}✅ 激活虚拟环境...${NC}"
source venv/bin/activate

echo ""
echo "======================================"
echo "📋 测试执行选项"
echo "======================================"
echo ""
echo "1️⃣  运行所有测试（推荐）"
echo "2️⃣  运行Conversation测试"
echo "3️⃣  运行Agent测试"
echo "4️⃣  运行API测试"
echo "5️⃣  运行核心测试"
echo "6️⃣  生成覆盖率报告"
echo ""
echo "======================================"
echo "📝 请输入选项 (1-6) 或 'all' 运行所有测试"
echo "======================================"

read -p "请输入选项: " OPTION

echo ""

# 执行选择的测试
case $OPTION in
    1|all)
        echo -e "${GREEN}🚀 运行所有测试...${NC}"
        echo ""

        # 运行测试并生成覆盖率报告
        pytest tests/ -v --tb=short \
            --cov=app \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-config=pyproject.toml

        # 显示覆盖率摘要
        echo ""
        echo "======================================"
        echo -e "${GREEN}✅ 测试完成！${NC}"
        echo "======================================"
        echo ""
        echo "📊 覆盖率报告已生成："
        echo "   - HTML报告: htmlcov/index.html"
        echo "   - 在浏览器中打开查看详细报告"
        echo ""

        ;;

    2)
        echo -e "${GREEN}📝 运行Conversation测试...${NC}"
        pytest tests/services/test_conversation_service.py -v --tb=short
        ;;

    3)
        echo -e "${GREEN}🤖 运行Agent测试...${NC}"
        pytest tests/agents/ -v --tb=short
        ;;

    4)
        echo -e "${GREEN}🌐 运行API测试...${NC}"
        pytest tests/api/ -v --tb=short
        ;;

    5)
        echo -e "${GREEN}⚙️  运行核心测试...${NC}"
        pytest tests/core/ -v --tb=short
        ;;

    6)
        echo -e "${GREEN}📊 仅生成覆盖率报告（不运行测试）...${NC}"
        pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --no-cov
        echo "📊 覆盖率报告已生成：htmlcov/index.html"
        ;;

    *)
        echo -e "${RED}❌ 无效的选项: $OPTION${NC}"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo -e "${GREEN}✅ 测试执行完成！${NC}"
echo "======================================"
echo ""
echo "💡 提示："
echo "1. 查看测试结果：运行 'pytest tests/ -v'"
echo "2. 查看覆盖率报告：打开 htmlcov/index.html"
echo "3. 查看失败的测试：运行 'pytest tests/ --tb=short -v'"
echo ""
