# Troubleshooting Guide

## 概述

本文档提供了Arya Video Agent系统的全面故障排查指南，包括常见问题、诊断步骤和解决方案。

## 版本信息

- **文档版本**: v1.0.0
- **适用系统版本**: Arya Video Agent v1.0.0+
- **最后更新**: 2024-01-15
- **维护者**: Arya Video Agent Team

---

## 应用启动问题

### 1.1 应用无法启动

#### 症状描述
应用启动时立即失败，没有响应。

#### 可能原因
1. **依赖包缺失或版本不兼容**
   - `ImportError` 或 `ModuleNotFoundError`
   
2. **环境变量未配置**
   - `KeyError` 或 `ValueError`
   
3. **数据库连接失败**
   - `ConnectionRefusedError` 或 `ConnectionTimeout`
   
4. **Redis连接失败**
   - `redis.exceptions.ConnectionError`

#### 诊断步骤
```bash
# 1. 检查依赖包
pip list | grep -i "error\|missing"

# 2. 检查环境变量
echo $DATABASE_URL
echo $REDIS_URL
echo $OPENAI_API_KEY

# 3. 测试数据库连接
python -c "from app.database.session import engine; import asyncio; print('Database OK')"

# 4. 测试Redis连接
python -c "import redis; r = redis.from_url('redis://localhost:6379'); print('Redis OK') if r.ping() else 'Redis Failed'"

# 5. 检查应用日志
tail -100 app/logs/app.log
```

#### 解决方案

##### 问题1：依赖包缺失
```bash
# 安装所有依赖
pip install -r requirements.txt

# 升级依赖包
pip install --upgrade -r requirements.txt
```

##### 问题2：环境变量未配置
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件
nano .env

# 加载环境变量
source .env
```

##### 问题3：数据库连接失败
```bash
# 检查数据库是否运行
ps aux | grep postgres
# 或者
docker ps | grep postgres

# 检查数据库端口
netstat -tuln | grep 5432

# 重启数据库
docker restart postgres
```

##### 问题4：Redis连接失败
```bash
# 检查Redis是否运行
ps aux | grep redis
# 或者
docker ps | grep redis

# 检查Redis端口
netstat -tuln | grep 6379

# 重启Redis
docker restart redis
```

### 1.2 应用启动缓慢

#### 症状描述
应用启动时间超过30秒。

#### 可能原因
1. **数据库连接池初始化慢**
2. **Redis连接初始化慢**
3. **大量模块导入**
4. **磁盘I/O性能差**

#### 诊断步骤
```bash
# 1. 检查启动时间
time python -m app.main

# 2. 检查数据库连接时间
python -c "from app.database.session import engine; import time; start = time.time(); engine.connect(); print(f'DB connect time: {time.time() - start:.3f}s')"

# 3. 检查Redis连接时间
python -c "import redis; import time; r = redis.from_url('redis://localhost:6379'); start = time.time(); r.ping(); print(f'Redis ping time: {time.time() - start:.3f}s')"

# 4. 检查磁盘I/O性能
iostat -x 1 10
```

#### 解决方案

##### 优化数据库连接池
```python
# app/database/session.py
# 减小连接池大小和超时时间
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,  # 减小连接池大小
    max_overflow=20,  # 减少最大溢出连接数
    pool_timeout=10,  # 减少连接超时时间
    connect_timeout=5,  # 减少连接超时时间
)
```

##### 优化Redis连接
```python
# app/services/redis_cache_service.py
# 减少最大连接数和超时时间
self._pool = ConnectionPool.from_url(
    self.redis_url,
    max_connections=20,  # 减少最大连接数
    socket_timeout=5,  # 减少socket超时
    socket_connect_timeout=5,  # 减少连接超时
)
```

---

## 数据库问题

### 2.1 数据库连接池耗尽

#### 症状描述
应用报错：`sqlalchemy.exc.PoolError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00`

#### 可能原因
1. **连接泄漏**：连接未正确释放
2. **连接池大小过小**：无法处理并发请求
3. **慢查询**：查询时间过长，连接占用时间太长

#### 诊断步骤
```bash
# 1. 检查数据库连接数
psql -U postgres -d arya_video_agent -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"

# 2. 检查慢查询
psql -U postgres -d arya_video_agent -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. 检查连接池配置
grep -r "pool_size\|max_overflow" app/database/
```

#### 解决方案

##### 问题1：连接泄漏
```python
# 确保使用async上下文管理器或确保session正确关闭
async def get_task(db: AsyncSession, task_id: str):
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        return task
    finally:
        await db.close()  # 确保session关闭
```

##### 问题2：连接池大小过小
```python
# 增加连接池大小
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=50,  # 增加连接池大小
    max_overflow=100,  # 增加最大溢出连接数
)
```

##### 问题3：慢查询
```python
# 优化慢查询，减少查询时间
# 使用索引、JOIN优化、批量操作
result = await db.execute(
    select(Task).where(Task.user_id == user_id).limit(20)
)
```

### 2.2 慢查询

#### 症状描述
查询响应时间超过1秒。

#### 可能原因
1. **缺少索引**：全表扫描
2. **N+1查询问题**：循环查询
3. **大数据量**：表数据量过大
4. **JOIN查询未优化**：笛卡尔积

#### 诊断步骤
```bash
# 1. 启用SQLAlchemy查询日志
# app/config.py
SQLALCHEMY_ECHO = True
SQLALCHEMY_ECHO_POOL = True

# 2. 使用EXPLAIN分析查询计划
from app.database.session import async_session
from sqlalchemy import text

async def analyze_query():
    async with async_session() as db:
        result = await db.execute(text("EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'user_123' LIMIT 20;"))
        print(result.mappings())
```

#### 解决方案

##### 添加索引
```sql
-- 为常用查询添加复合索引
CREATE INDEX idx_tasks_user_created_status ON tasks(user_id, created_at DESC, status);
CREATE INDEX idx_tasks_user_priority_created ON tasks(user_id, priority, created_at DESC);
```

##### 优化N+1查询
```python
# 使用selectinload或joinedload避免N+1查询
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Task)
    .options(selectinload(Task.scripts))
    .where(Task.user_id == user_id)
)
tasks = result.scalars().all()
```

---

## Redis问题

### 3.1 Redis连接失败

#### 症状描述
应用报错：`redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.`

#### 可能原因
1. **Redis服务未运行**
2. **Redis端口错误**
3. **防火墙阻止连接**
4. **网络问题**

#### 诊断步骤
```bash
# 1. 检查Redis服务是否运行
docker ps | grep redis
# 或者
ps aux | grep redis-server

# 2. 检查Redis端口
netstat -tuln | grep 6379

# 3. 测试Redis连接
redis-cli ping

# 4. 检查Redis日志
docker logs redis
```

#### 解决方案

##### 启动Redis服务
```bash
# 使用Docker启动Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# 或者使用docker-compose
docker-compose up -d redis
```

##### 检查Redis配置
```bash
# 检查redis配置
redis-cli CONFIG GET bind
redis-cli CONFIG GET port
redis-cli CONFIG GET protected-mode
```

### 3.2 Redis内存不足

#### 症状描述
Redis报错：`OOM command not allowed when used memory > 'maxmemory'.`

#### 可能原因
1. **Redis内存配置过小**
2. **缓存数据过多**
3. **缓存键未设置TTL**
4. **内存泄漏**

#### 诊断步骤
```bash
# 1. 检查Redis内存使用情况
redis-cli INFO memory

# 2. 检查缓存键数量
redis-cli DBSIZE

# 3. 检查最大的缓存键
redis-cli --bigkeys

# 4. 检查内存占用前10的键
redis-cli --memkeys | head -10
```

#### 解决方案

##### 增加Redis内存限制
```bash
# 编辑redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru

# 重启Redis
docker restart redis
```

##### 清理过期缓存键
```python
# 定期清理过期缓存键
from app.services.redis_cache_service import RedisCacheService

cache_service = RedisCacheService()
await cache_service.invalidate_prefix("tasks:")
```

---

## API问题

### 4.1 API响应慢

#### 症状描述
API响应时间超过1秒。

#### 可能原因
1. **数据库查询慢**
2. **缓存未命中**
3. **N+1查询问题**
4. **序列化慢**

#### 诊断步骤
```bash
# 1. 检查API响应时间
curl -w "@curl-format_total_time -o /dev/null -s" http://localhost:8000/api/v1/tasks

# 2. 检查Prometheus监控
# 访问 http://localhost:3000/d/arya-video-agent
# 查看API响应时间指标

# 3. 检查应用日志
tail -100 app/logs/app.log | grep "Slow request"
```

#### 解决方案

##### 优化数据库查询
```python
# 使用索引优化查询
result = await db.execute(
    select(Task).where(Task.user_id == user_id).limit(20)
)
```

##### 启用缓存
```python
# 使用Redis缓存API响应
cache_key = f"api:response:/api/v1/tasks?user_id={user_id}"
cached_response = await redis_cache_service.get(cache_key)

if cached_response:
    return cached_response

# 如果缓存未命中，从数据库查询并缓存
result = await get_tasks_from_db(user_id)
await redis_cache_service.set(cache_key, result, ttl=300)

return result
```

---

## 任务处理问题

### 5.1 任务处理失败

#### 症状描述
任务处理失败，错误信息不明确。

#### 可能原因
1. **Agent API调用失败**
2. **外部服务不可用**
3. **输入数据不正确**
4. **超时**

#### 诊断步骤
```bash
# 1. 检查任务日志
tail -100 app/logs/task_processor.log

# 2. 检查任务状态
curl -X GET http://localhost:8000/api/v1/tasks/{task_id}

# 3. 检查Agent调用日志
tail -100 app/logs/agent.log | grep "{task_id}"

# 4. 检查错误率
# 访问 http://localhost:3000/d/arya-video-agent
# 查看Agent错误率指标
```

#### 解决方案

##### 增加错误日志
```python
# 在Agent调用时添加详细的错误日志
try:
    response = await agent_client.generate_content(prompt)
except Exception as e:
    logger.error(f"Agent call failed: {str(e)}", exc_info=True)
    raise
```

##### 实现重试机制
```python
# 使用指数退避重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_agent_with_retry(prompt: str):
    """带重试的Agent调用"""
    return await agent_client.generate_content(prompt)
```

---

## 性能问题

### 6.1 高CPU使用率

#### 症状描述
CPU使用率持续超过80%。

#### 可能原因
1. **死循环**
2. **无限递归**
3. **CPU密集型任务**
4. **并发数过高**

#### 诊断步骤
```bash
# 1. 检查CPU使用率
top
# 或者
htop

# 2. 检查进程CPU使用率
ps aux --sort=-%cpu | head

# 3. 检查线程数
ps -efL | grep python | wc -l

# 4. 检查Prometheus监控
# 访问 http://localhost:3000/d/arya-video-agent
# 查看CPU使用率指标
```

#### 解决方案

##### 优化CPU密集型任务
```python
# 使用异步编程避免阻塞
import asyncio

async def process_tasks():
    tasks = [process_task(task_id) for task_id in task_ids]
    await asyncio.gather(*tasks)
```

##### 限制并发数
```python
# 使用信号量限制并发数
from asyncio import Semaphore

semaphore = Semaphore(50)  # 限制最多50个并发任务

async def process_task(task_id: str):
    async with semaphore:
        return await process_task_internal(task_id)
```

---

## 内存问题

### 7.1 内存泄漏

#### 症状描述
应用内存使用量持续增长，最终被系统杀掉（OOM Killer）。

#### 可能原因
1. **缓存未设置TTL**
2. **大对象未及时释放**
3. **循环引用**
4. **全局变量累积**

#### 诊断步骤
```bash
# 1. 检查内存使用情况
top
# 或者
htop

# 2. 使用memory_profiler分析内存
python -m memory_profiler app/main.py

# 3. 检查缓存大小
redis-cli INFO memory
redis-cli DBSIZE
```

#### 解决方案

##### 设置缓存TTL
```python
# 为所有缓存键设置TTL
cache_ttl = 300  # 5分钟
await redis_cache_service.set(cache_key, value, ttl=cache_ttl)
```

##### 释放大对象
```python
# 使用weakref避免循环引用
import weakref

# 在函数结束时主动释放大对象
def process_large_data(data):
    result = process(data)
    del data  # 主动释放大对象
    return result
```

---

## 网络问题

### 8.1 API调用超时

#### 症状描述
调用外部API时经常超时。

#### 可能原因
1. **网络延迟**
2. **DNS解析慢**
3. **防火墙阻止**
4. **外部服务不可用**

#### 诊断步骤
```bash
# 1. 检查网络延迟
ping api.example.com

# 2. 检查DNS解析
nslookup api.example.com

# 3. 检查端口连通性
telnet api.example.com 443

# 4. 使用curl测试API
curl -v -m 10 http://api.example.com/endpoint
```

#### 解决方案

##### 增加超时时间
```python
# 增加API调用的超时时间
timeout = 30  # 30秒超时
response = await httpx_client.post(url, json=data, timeout=timeout)
```

##### 实现重试机制
```python
# 使用指数退避重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_api_with_retry(url: str, data: dict):
    """带重试的API调用"""
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, timeout=30)
        return response.json()
```

---

## 日志和监控问题

### 9.1 日志未输出

#### 症状描述
应用运行但没有日志输出。

#### 可能原因
1. **日志级别设置过高**
2. **日志文件路径错误**
3. **日志配置未正确加载**
4. **日志写入权限问题**

#### 诊断步骤
```bash
# 1. 检查日志文件路径
ls -la app/logs/

# 2. 检查日志文件权限
ls -la app/logs/app.log

# 3. 检查日志配置
grep -r "LOG_LEVEL" app/
```

#### 解决方案

##### 调整日志级别
```python
# app/config.py
import logging

# 设置日志级别为DEBUG
LOG_LEVEL = "DEBUG"

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 部署问题

### 10.1 Docker容器无法启动

#### 症状描述
Docker容器启动后立即退出。

#### 可能原因
1. **启动命令错误**
2. **依赖服务未就绪**
3. **环境变量未配置**
4. **应用启动错误**

#### 诊断步骤
```bash
# 1. 检查容器状态
docker ps -a

# 2. 查看容器日志
docker logs <container_id>

# 3. 进入容器调试
docker exec -it <container_id> sh

# 4. 检查容器启动命令
docker inspect <container_id> | grep -A 10 Cmd
```

#### 解决方案

##### 添加健康检查
```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

##### 使用depends_on等待依赖服务
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 联系支持

如有任何问题或建议，请联系：
- **Email**: support@arya-video-agent.com
- **GitHub Issues**: https://github.com/startcodeing/arya-video-agent/issues
- **Discord社区**: https://discord.gg/arya-video-agent

---

**文档版本**: v1.0.0
**最后更新**: 2024-01-15
**维护者**: Arya Video Agent Team
