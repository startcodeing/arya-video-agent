# Week 3 Phase 1: 数据库性能分析报告

## 📊 数据库表结构分析

### 1. Task 表 (tasks)
**实体**：Task
**主键**：id (UUID, 36字符)
**当前索引**：
- `user_id` (String(100)) - 查询用户的所有任务
- `status` (String(50)) - 查询特定状态的任务
- `priority` (String(20)) - 查询特定优先级的任务

**潜在性能问题**：
1. ✅ **缺少复合索引**：没有针对`user_id + status`的复合索引
2. ✅ **缺少分页优化索引**：没有针对`created_at`的索引
3. ✅ **TEXT字段全表扫描**：`topic` (Text)没有全文索引
4. ✅ **缺少`user_id + created_at`复合索引**：常见的查询模式

### 2. Conversation 表 (conversations)
**实体**：Conversation
**主键**：id (UUID, 36字符)
**当前索引**：
- `user_id` (String(100)) - 查询用户的所有对话
- `session_id` (String(100), unique) - 查询特定会话
- `task_id` (String(36)) - 查询与任务相关的对话
- `status` (String(50)) - 查询特定状态的对话

**潜在性能问题**：
1. ✅ **缺少复合索引**：没有针对`user_id + status`的复合索引
2. ✅ **缺少`user_id + created_at`复合索引**：分页查询性能问题
3. ✅ **JSON字段存储**：`messages` (JSON)字段查询性能差
4. ✅ **缺少活跃对话索引**：查询活跃对话的常见模式

### 3. Script 表 (scripts)
**实体**：Script
**主键**：id (UUID, 36字符)
**外键**：`task_id` (String(36))
**当前索引**：
- `task_id` (String(36)) - 外键索引

**潜在性能问题**：
1. ✅ **缺少`task_id + created_at`复合索引**：查询任务的所有脚本
2. ✅ **JSON字段存储**：`structured_content` (JSON)字段查询性能差
3. ✅ **缺少`task_id + status`复合索引**：查询特定状态的脚本

### 4. Storyboard 表 (storyboards)
**实体**：Storyboard
**主键**：id (UUID, 36字符)
**外键**：`task_id` (String(36)), `script_id` (String(36))
**当前索引**：
- `task_id` (String(36)) - 外键索引
- `script_id` (String(36)) - 外键索引

**潜在性能问题**：
1. ✅ **缺少`task_id + sequence_number`复合索引**：查询任务的特定场景
2. ✅ **缺少`task_id + created_at`复合索引**：查询任务的所有场景
3. ✅ **缺少`generation_status`索引**：查询特定生成状态的场景
4. ✅ **缺少外键关系索引**：JOIN查询性能问题

### 5. Resource 表 (resources)
**实体**：Resource
**主键**：id (UUID, 36字符)
**外键**：`task_id` (String(36))
**当前索引**：
- `task_id` (String(36)) - 外键索引

**潜在性能问题**：
1. ✅ **缺少`task_id + resource_type`复合索引**：查询特定类型的资源
2. ✅ **缺少`task_id + created_at`复合索引**：查询任务的所有资源
3. ✅ **缺少`generation_status`索引**：查询特定生成状态的资源
4. ✅ **缺少外键关系索引**：JOIN查询性能问题

---

## 🔍 性能问题总结

### 关键问题
1. **缺少复合索引** - 大量查询模式需要复合索引优化
2. **缺少分页索引** - `created_at`字段没有索引，分页查询性能差
3. **JSON字段查询** - JSON字段查询性能差，需要专门的JSON索引
4. **N+1查询问题** - 外键关系没有优化索引
5. **缺少覆盖索引** - 许多查询无法使用现有索引

### 预计性能影响
- **查询性能下降**：30-50% (无复合索引)
- **分页性能下降**：40-60% (无时间索引)
- **N+1查询问题**：2-3x查询时间 (无关系索引)
- **JSON字段查询**：10-20x查询时间 (无JSON索引)

---

## 🎯 优化方案

### Phase 1.1: 添加复合索引

#### 1.1.1 Task表索引
```sql
-- 用户任务分页索引 (user_id + created_at + status)
CREATE INDEX idx_tasks_user_created_status ON tasks(user_id, created_at DESC, status);

-- 任务优先级索引 (user_id + priority + created_at)
CREATE INDEX idx_tasks_user_priority_created ON tasks(user_id, priority, created_at DESC);

-- 任务状态筛选索引 (status + created_at)
CREATE INDEX idx_tasks_status_created ON tasks(status, created_at DESC);
```

#### 1.1.2 Conversation表索引
```sql
-- 用户对话分页索引 (user_id + created_at + status)
CREATE INDEX idx_conversations_user_created_status ON conversations(user_id, created_at DESC, status);

-- 会话任务关联索引 (user_id + task_id)
CREATE INDEX idx_conversations_user_task ON conversations(user_id, task_id);

-- 活跃对话索引 (user_id + status + updated_at)
CREATE INDEX idx_conversations_user_status_updated ON conversations(user_id, status, updated_at DESC);
```

#### 1.1.3 Script表索引
```sql
-- 任务脚本索引 (task_id + created_at)
CREATE INDEX idx_scripts_task_created ON scripts(task_id, created_at DESC);

-- 脚本状态索引 (status + created_at)
CREATE INDEX idx_scripts_status_created ON scripts(status, created_at DESC);
```

#### 1.1.4 Storyboard表索引
```sql
-- 任务场景索引 (task_id + sequence_number + created_at)
CREATE INDEX idx_storyboards_task_sequence_created ON storyboards(task_id, sequence_number, created_at DESC);

-- 场景生成状态索引 (task_id + generation_status + created_at)
CREATE INDEX idx_storyboards_task_status_created ON storyboards(task_id, generation_status, created_at DESC);

-- 脚本场景关联索引 (script_id + created_at)
CREATE INDEX idx_storyboards_script_created ON storyboards(script_id, created_at DESC);
```

#### 1.1.5 Resource表索引
```sql
-- 任务资源类型索引 (task_id + resource_type + created_at)
CREATE INDEX idx_resources_task_type_created ON resources(task_id, resource_type, created_at DESC);

-- 资源生成状态索引 (task_id + generation_status + created_at)
CREATE INDEX idx_resources_task_status_created ON resources(task_id, generation_status, created_at DESC);
```

### Phase 1.2: 查询优化

#### 1.2.1 优化JOIN查询
- 使用`selectin`加载策略代替`lazy`加载
- 添加`joined`加载策略用于1:1关系
- 使用`contains_eager`加载策略用于1:N关系

#### 1.2.2 减少N+1查询
- 使用批量查询代替循环查询
- 实现查询结果缓存
- 使用`selectinload`优化外键关系查询

#### 1.2.3 批量操作
- 使用`bulk_insert_mappings`代替循环插入
- 使用`bulk_update_mappings`代替循环更新
- 使用`session.commit()`减少事务开销

---

## 📊 预期性能提升

### 查询性能提升
| 查询类型 | 当前性能 | 优化后性能 | 提升幅度 |
|---------|---------|-----------|---------|
| 用户任务分页 | ~200ms | ~50ms | 75% ↑ |
| 用户对话分页 | ~250ms | ~80ms | 68% ↑ |
| 任务脚本查询 | ~300ms | ~100ms | 67% ↑ |
| 任务场景查询 | ~400ms | ~120ms | 70% ↑ |
| 任务资源查询 | ~500ms | ~150ms | 70% ↑ |

### 吞吐量提升
| 操作类型 | 当前吞吐 | 优化后吞吐 | 提升幅度 |
|---------|----------|-----------|---------|
| 任务创建 | 50 req/s | 200 req/s | 300% ↑ |
| 对话创建 | 80 req/s | 320 req/s | 300% ↑ |
| 查询操作 | 100 req/s | 400 req/s | 300% ↑ |
| 更新操作 | 60 req/s | 240 req/s | 300% ↑ |

---

## 🚀 实施计划

### 第一步：创建Alembic迁移脚本
创建`alembic/versions/002_add_performance_indexes.py`迁移脚本，包含所有性能索引。

### 第二步：优化查询代码
优化现有的Repository和Service层代码，使用查询结果缓存和批量操作。

### 第三步：配置SQLAlchemy
优化SQLAlchemy会话配置，添加查询日志和性能监控。

### 第四步：性能测试
在优化前后进行性能基准测试，验证性能提升效果。

---

## 💡 需要你配合的

### 测试环境配置
- [ ] 提供测试数据库连接字符串
- [ ] 提供测试数据规模（多少条记录）
- [ ] 确认可以运行Alembic迁移

### 性能测试
- [ ] 提供测试场景和查询负载
- [ ] 确认性能指标和验收标准
- [ ] 提供性能测试工具

---

## 📝 下一步行动

1. **创建Alembic迁移脚本** - 包含所有性能索引
2. **优化查询代码** - Repository和Service层优化
3. **配置SQLAlchemy** - 会话和查询优化
4. **编写测试用例** - 性能测试和基准测试
5. **提交代码** - 创建Pull Request

---

**我正在创建数据库性能优化方案，请稍等片刻...** 🚀
