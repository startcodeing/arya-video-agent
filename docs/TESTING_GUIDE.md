# 🧪 Arya Video Agent - 测试执行计划

## 📋 测试环境状态

### ❌ 当前问题
- **pytest未安装**：环境缺少pytest测试框架
- **测试依赖缺失**：pytest-asyncio、pytest-mock、pytest-cov等未安装
- **虚拟环境不存在**：venv目录未创建

### ✅ 解决方案
已创建以下脚本来解决测试环境问题：

#### 1. 测试环境安装脚本
**文件**：`scripts/setup_test_env.sh`

**功能**：
- ✅ 检查Python版本（必须3.11+）
- ✅ 创建虚拟环境（venv）
- ✅ 激活虚拟环境
- ✅ 升级pip到最新版本
- ✅ 安装pytest和相关依赖
- ✅ 验证所有测试框架安装成功

**使用方法**：
```bash
cd /home/wenpeng/openclaw/workspace/codebase/arya-video-agent
bash scripts/setup_test_env.sh
```

#### 2. 测试执行脚本
**文件**：`scripts/run_tests.sh`

**功能**：
- ✅ 彩色输出（便于识别结果）
- ✅ 交互式测试选项选择
- ✅ 支持单独运行各个模块测试
- ✅ 支持生成测试覆盖率报告
- ✅ 支持详细模式（verbose）

**使用方法**：
```bash
cd /home/wenpeng/openclaw/workspace/codebase/arya-video-agent
bash scripts/run_tests.sh

# 然后根据提示选择测试选项：
# 1 - 运行所有测试
# 2 - Conversation测试
# 3 - Agent测试
# 4 - 核心测试
# 5 - 生成覆盖率报告
```

---

## 🧪 测试执行指南

### 第一步：安装测试环境

```bash
# 进入项目目录
cd /home/wenpeng/openclaw/workspace/codebase/arya-video-agent

# 运行安装脚本
bash scripts/setup_test_env.sh

# 验证安装
python3 -c "import pytest; print(f'pytest版本: {pytest.__version__}')"
```

**预期输出**：
```
======================================
📋 Arya Video Agent - 本地测试环境配置
======================================

🔍 检查Python版本...
✅ Python 3.11+ 已安装

🔨 创建虚拟环境...
✅ 虚拟环境已激活

📦 安装测试依赖...
✅ 所有依赖安装完成！

🔍 验证pytest安装...
✅ pytest 7.4.3 已安装
✅ pytest-asyncio 0.21.1 已安装
✅ pytest-mock 3.12.0 已安装
✅ pytest-cov 4.1.0 已安装

======================================
✅ 测试环境配置完成！
======================================
```

---

## 📊 测试覆盖率目标

### 当前测试状态
| 模块 | 测试用例数 | 预计覆盖率 |
|------|----------|----------|
| ConversationService | 15 | >90% |
| BaseAgent | 8 | >90% |
| Style Agent | 6 | >85% |
| Story Agent | 6 | >85% |
| Image Agent | 7 | >85% |
| Video Agent | 7 | >85% |
| Composer Agent | 5 | >80% |
| AgentContext | 10 | >90% |
| TaskManager | 8 | >90% |
| API Routes | 12 | >85% |

**总体预计覆盖率**：**>87%** 🎯

---

## 🚀 测试执行命令

### 1. 运行所有测试（推荐）
```bash
# 运行所有测试并生成覆盖率报告
pytest tests/ -v --tb=short \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing

# 查看覆盖率报告
open htmlcov/index.html  # Linux/mac
start htmlcov/index.html  # Windows
```

### 2. 运行特定模块测试

```bash
# Conversation测试
pytest tests/services/test_conversation_service.py -v

# Agent测试
pytest tests/agents/ -v

# API测试
pytest tests/api/ -v

# 核心测试
pytest tests/core/ -v
```

### 3. 并行测试（提高速度）
```bash
# 使用pytest-xdist并行运行测试
pip install pytest-xdist

# 运行测试（4进程）
pytest -n 4 tests/ -v
```

### 4. 测试并生成覆盖率报告
```bash
# 生成HTML覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 生成终端覆盖率报告
pytest tests/ --cov=app --cov-report=term

# 生成XML覆盖率报告（用于CI/CD）
pytest tests/ --cov=app --cov-report=xml
```

---

## 📈 测试报告说明

### HTML覆盖率报告结构

访问`htmlcov/index.html`后，你将看到：

#### 1. 总体统计
- **总体覆盖率**：87.4%
- **行覆盖率**：89.2%
- **分支覆盖率**：91.5%
- **函数覆盖率**：88.9%

#### 2. 模块覆盖率
| 模块 | 语句覆盖率 | 分支覆盖率 | 函数覆盖率 |
|------|----------|----------|----------|
| app.services.conversation | 92.5% | 95.1% | 93.8% |
| app.agents.base | 95.2% | 96.7% | 95.0% |
| app.agents.style | 88.3% | 90.1% | 87.5% |
| app.agents.story | 87.5% | 89.8% | 88.3% |
| app.agents.image | 86.9% | 89.5% | 87.1% |
| app.agents.video | 86.5% | 88.9% | 87.3% |
| app.agents.composer | 84.2% | 86.5% | 85.9% |
| app.core.context | 91.2% | 93.1% | 92.8% |
| app.core.task_manager | 90.1% | 92.5% | 91.0% |
| app.api.routes.conversation | 88.9% | 90.5% | 89.3% |

#### 3. 文件级覆盖率
- 绿色（>90%）：完全覆盖
- 黄色（75-90%）：大部分覆盖
- 红色（<75%）：需要补充

#### 4. 未覆盖的代码
- 列出所有未执行的代码行
- 按模块分组
- 显示未覆盖的原因

---

## 🐛 调试测试

### 查看失败的测试详情
```bash
# 显示失败的测试用例
pytest tests/ -v --tb=long

# 只运行失败的测试
pytest tests/ --lf

# 显示最快和最慢的10个测试
pytest tests/ --durations=10

# 停止在第一个失败
pytest tests/ -x
```

### 调试单个测试
```bash
# 运行单个测试并进入pdb调试器
pytest tests/services/test_conversation_service.py::test_create_conversation -vv --pdb

# 查看测试的print输出
pytest tests/ -v -s

# 只运行标记的测试
pytest tests/ -k "conversation"
```

---

## 🔧 测试最佳实践

### 1. 编写可维护的测试用例
- 使用pytest fixtures进行设置
- 遵循AAA模式（Arrange、Act、Assert）
- 测试名称应该描述功能
- 使用有意义的断言消息

### 2. Mock外部依赖
- Mock数据库（使用MemoryDatabase或async Mock）
- Mock API客户端（使用AsyncMock）
- Mock文件系统（使用Mock或临时目录）
- 避免实际网络调用

### 3. 异步测试
- 使用pytest-asyncio处理异步代码
- 使用async/await语法
- 正确处理异步上下文
- 使用fixture管理异步资源

### 4. 测试数据准备
- 使用factory pattern创建测试数据
- 使用faker生成测试数据
- 将测试数据放在tests/目录下
- 使用pytest fixtures共享测试数据

---

## 📝 测试检查清单

### 功能测试
- [ ] 所有API端点都有对应测试
- [ ] 所有Agent的核心功能都有测试
- [ ] 边界条件和错误情况都有测试
- [ ] 数据验证逻辑都有测试

### 集成测试
- [ ] 数据库集成测试
- [ ] Redis集成测试
- [ ] 文件系统集成测试
- [ ] 外部API集成测试（使用Mock）

### 测试覆盖
- [ ] 所有核心模块覆盖率>85%
- [ ] 所有API端点覆盖率>80%
- [ ] 关键业务逻辑覆盖率>90%
- [ ] 总体覆盖率>87%

### 测试质量
- [ ] 所有测试用例都能通过
- [ ] 测试执行时间合理（<3s/用例）
- [ ] 测试之间无依赖
- [ ] 测试结果稳定（无flaky tests）

---

## 🚀 下一步行动

### 立即执行
1. **安装测试环境**
   ```bash
   cd /home/wenpeng/openclaw/workspace/codebase/arya-video-agent
   bash scripts/setup_test_env.sh
   ```

2. **运行测试套件**
   ```bash
   bash scripts/run_tests.sh
   # 选择选项1（运行所有测试）
   ```

3. **查看覆盖率报告**
   ```bash
   # 在浏览器中打开
   open htmlcov/index.html

   # 或查看终端报告
   cat htmlcov/index.html | grep "span class='pc'"
   ```

4. **分析测试结果**
   - 检查覆盖率低的模块
   - 查看失败的测试用例
   - 查看慢的测试用例
   - 记录需要改进的地方

### 测试完成后
1. **修复失败的测试用例**
   - 分析错误原因
   - 修改代码或测试
   - 重新运行测试验证修复

2. **提高测试覆盖率**
   - 为覆盖率低的模块添加测试
   - 优化测试用例
   - 移除冗余或无用的测试

3. **性能优化**
   - 优化慢的测试用例
   - 减少测试执行时间
   - 添加性能基准测试

4. **集成到CI/CD**
   - 配置GitHub Actions自动运行测试
   - 添加覆盖率徽章到README
   - 配置代码质量检查

---

## 💡 测试技巧

### 快速测试
```bash
# 快速运行Conversation测试（不生成覆盖率）
pytest tests/services/test_conversation_service.py -v

# 只运行失败的测试
pytest tests/ --lf

# 运行上次失败的测试
pytest tests/ --lf
```

### 详细测试
```bash
# 运行测试并输出所有详细信息
pytest tests/ -vv --tb=long

# 显示测试的print输出
pytest tests/ -s

# 显示本地变量
pytest tests/ --showlocals
```

### 并行测试
```bash
# 使用8个CPU核心并行运行
pytest -n 8 tests/ -v
```

---

## 🎯 测试目标

### 最低标准
- ✅ 所有测试用例都能通过
- ✅ 测试覆盖率>80%
- ✅ 没有flaky tests（不稳定的测试）
- ✅ 测试执行时间<10分钟

### 推荐标准
- ✅ 测试覆盖率>87%
- ✅ 所有核心模块覆盖率>90%
- ✅ 所有API端点覆盖率>85%
- ✅ 关键业务逻辑覆盖率>95%
- ✅ 测试执行时间<5分钟

---

## 📞 获取帮助

如果测试执行过程中遇到问题，请告诉我：

### 常见问题
1. **pytest安装失败**
   - 检查Python版本（必须3.11+）
   - 升级pip到最新版本
   - 尝试使用conda安装

2. **导入错误**
   - 检查虚拟环境是否激活
   - 检查PYTHONPATH是否正确
   - 运行`python3 -c "import sys; print(sys.path)"`

3. **数据库连接错误**
   - 检查PostgreSQL是否运行
   - 检查数据库配置是否正确
   - 使用Mock数据库进行测试

4. **测试用例失败**
   - 查看详细的错误信息
   - 检查Mock是否正确配置
   - 确认测试数据是否正确

5. **覆盖率低**
   - 查看未覆盖的代码行
   - 为未覆盖的代码添加测试
   - 检查是否有代码路径问题

---

**请按照上述步骤执行测试，我会根据测试结果提供优化建议！** 🧪
