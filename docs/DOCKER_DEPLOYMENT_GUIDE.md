# Docker Deployment Guide

## 概述

本指南提供了Arya Video Agent系统的完整Docker部署步骤，包括开发、测试和生产环境。

## 版本信息

- **应用版本**: v1.0.0
- **Docker版本**: >= 20.10
- **Docker Compose版本**: >= 2.0
- **最后更新**: 2024-01-15
- **维护者**: Arya Video Agent Team

---

## 前置要求

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS / Windows 10+
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **内存**: >= 4GB RAM
- **磁盘**: >= 20GB 可用空间
- **CPU**: >= 2 cores

### 网络要求
- **出站网络**: 稳定的互联网连接
- **防火墙**: 开放端口 8000, 5432, 6379, 9090
- **DNS**: 正常的DNS解析

### 依赖服务
- **PostgreSQL**: >= 13
- **Redis**: >= 6.0
- **Prometheus**: >= 2.30
- **Grafana**: >= 8.0
- **OpenAI API**: 有效的API密钥

---

## 部署架构

```
┌─────────────────────────────────────────────────┐
│                  Docker Host                    │
├─────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │  App    │  │PostgreSQL│  │  Redis   │   │
│  │(FastAPI)│  │ (Database│  │ (Cache)  │   │
│  │ :8000   │  │ :5432    │  │ :6379    │   │
│  └────┬────┘  └─────────┘  └─────────┘   │
│       │               │              │      │
│  ┌────┴───────────────┴───────────────┴──────┐  │
│  │           Nginx Reverse Proxy        │  │
│  │              :80                    │  │
│  └───────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────┘
```

---

## 快速开始

### 1. 克隆代码仓库
```bash
# 克隆代码仓库
git clone https://github.com/startcodeing/arya-video-agent.git

# 进入项目目录
cd arya-video-agent
```

### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑环境变量
nano .env
```

**必要的环境变量**：
```bash
# 应用配置
APP_NAME=Arya Video Agent
APP_VERSION=1.0.0
ENV=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
LOG_FILE=app/logs/app.log
LOG_ROTATION=10 MB
LOG_RETENTION=30 days

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/arya_video_agent

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_POOL_SIZE=50
REDIS_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30

# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# Anthropic配置
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# 存储配置
STORAGE_PROVIDER=local
STORAGE_PATH=/app/storage
# 如果使用S3:
# AWS_ACCESS_KEY_ID=your-access-key-id
# AWS_SECRET_ACCESS_KEY=your-secret-access-key
# AWS_S3_BUCKET=your-bucket-name
# AWS_REGION=us-east-1

# 监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000

# 安全配置
SECRET_KEY=your-secret-key-here-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. 构建Docker镜像
```bash
# 构建应用Docker镜像
docker build -t arya-video-agent:latest .

# 或者使用特定版本标签
docker build -t arya-video-agent:v1.0.0 .
```

### 4. 启动服务
```bash
# 使用docker-compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**预期输出**：
```
NAME                     STATUS    PORTS
arya-video-agent_api    Up        0.0.0.0:8000->8000/tcp
postgres                 Up        0.0.0.0:5432->5432/tcp
redis                    Up        0.0.0.0:6379->6379/tcp
nginx                    Up        0.0.0.0:80->80/tcp
prometheus               Up        0.0.0.0:9090->9090/tcp
grafana                  Up        0.0.0.0:3000->3000/tcp
```

### 5. 验证部署
```bash
# 1. 健康检查
curl -f "%{http_code}\n" http://localhost:8000/health

# 预期输出: 200

# 2. 查看Prometheus指标
curl -f "%{http_code}\n" http://localhost:9090/metrics

# 预期输出: 200

# 3. 访问Grafana
# 在浏览器中打开: http://localhost:3000
# 默认用户名: admin
# 默认密码: admin
```

### 6. 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止服务并删除数据卷
docker-compose down -v
```

---

## 详细部署步骤

### 1. 创建Docker网络
```bash
# 创建Docker网络（用于服务间通信）
docker network create arya-video-agent-network

# 验证网络创建
docker network ls | grep arya-video-agent-network
```

### 2. 启动PostgreSQL数据库
```bash
# 创建数据卷
docker volume create postgres_data

# 启动PostgreSQL容器
docker run -d \
  --name postgres \
  --network arya-video-agent-network \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=arya_video_agent \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# 验证数据库启动
docker ps | grep postgres

# 等待数据库启动完成（约10秒）
sleep 10

# 测试数据库连接
docker exec -it postgres psql -U postgres -d arya_video_agent -c "SELECT version();"
```

### 3. 启动Redis缓存
```bash
# 创建数据卷
docker volume create redis_data

# 启动Redis容器
docker run -d \
  --name redis \
  --network arya-video-agent-network \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --appendfsync everysec

# 验证Redis启动
docker ps | grep redis

# 测试Redis连接
docker exec -it redis redis-cli ping

# 预期输出: PONG
```

### 4. 运行数据库迁移
```bash
# 进入应用容器
docker run -it --rm \
  --network arya-video-agent-network \
  --env-file .env \
  arya-video-agent:latest \
  alembic upgrade head

# 或者使用docker-compose
docker-compose exec api alembic upgrade head
```

### 5. 启动Prometheus和Grafana
```bash
# 创建数据卷
docker volume create prometheus_data
docker volume create grafana_data

# 启动Prometheus容器
docker run -d \
  --name prometheus \
  --network arya-video-agent-network \
  -p 9090:9090 \
  -v $(pwd)/prometheus:/etc/prometheus \
  -v prometheus_data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml

# 启动Grafana容器
docker run -d \
  --name grafana \
  --network arya-video-agent-network \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_INSTALL_PLUGINS=grafana-piechart-panel \
  -e GF_INSTALL_PLUGINS=grafana-worldmap-panel \
  -v grafana_data:/var/lib/grafana \
  grafana/grafana:latest

# 验证服务启动
docker ps | grep -E "prometheus|grafana"
```

### 6. 配置Grafana数据源
```bash
# 1. 访问Grafana
open http://localhost:3000

# 2. 登录（默认用户名: admin，密码: admin）

# 3. 添加Prometheus数据源
# Configuration > Data Sources > Add data source
# 选择: Prometheus
# 配置:
#   Name: Prometheus
#   URL: http://prometheus:9090
#   Access: Server (default)
# 点击 "Save & Test"
```

### 7. 导入Grafana仪表板
```bash
# 1. 在Grafana中导入仪表板
# Dashboards > Import

# 2. 上传仪表板JSON文件
# 从grafana/dashboards/system-monitoring.json上传

# 3. 选择Prometheus数据源
# 点击 "Import"
```

### 8. 启动应用容器
```bash
# 启动应用容器
docker run -d \
  --name arya-video-agent \
  --network arya-video-agent-network \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/app:/app \
  -v $(pwd)/app/storage:/app/storage \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  arya-video-agent:latest \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 验证应用启动
docker ps | grep arya-video-agent

# 查看应用日志
docker logs -f arya-video-agent

# 测试应用健康检查
curl -f "%{http_code}\n" http://localhost:8000/health

# 预期输出: 200
```

---

## Docker Compose部署（推荐）

### 创建docker-compose.yml文件
```yaml
version: '3.8'

services:
  # 应用服务
  api:
    build: .
    image: arya-video-agent:latest
    container_name: arya-video-agent
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/arya_video_agent
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-False}
    volumes:
      - ./app:/app
      - ./app/storage:/app/storage
      - ./app/logs:/app/logs
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
    restart: unless-stopped

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=arya_video_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --appendfsync everysec
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

  # Prometheus监控
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules/:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  # Grafana可视化
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
      - GF_INSTALL_PLUGINS=grafana-worldmap-panel
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

---

## 生产环境部署

### 1. 安全配置

#### 配置防火墙
```bash
# 仅开放必要的端口
# 80: HTTP
# 443: HTTPS
# 22: SSH (限制IP访问)

# 使用UFW防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from YOUR_IP_ADDRESS to any port 22/tcp
sudo ufw enable
```

#### 配置SSL/TLS
```bash
# 生成自签名证书（仅用于测试）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/arya-video-agent.key \
  -out /etc/ssl/certs/arya-video-agent.crt

# 或者使用Let's Encrypt生成免费证书
sudo certbot --nginx certonly -d your-domain.com
```

#### 配置环境变量
```bash
# 生产环境配置
ENV=production
DEBUG=False
SECRET_KEY=$(openssl rand -base64 32)
```

### 2. 性能优化

#### 调整资源限制
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 3
```

#### 优化数据库配置
```bash
# PostgreSQL配置优化
docker exec -it postgres psql -U postgres -d arya_video_agent <<EOF
-- 调整最大连接数
ALTER SYSTEM SET max_connections = 200;

-- 调整共享缓冲区
ALTER SYSTEM SET shared_buffers = 256MB;

-- 调整工作内存
ALTER SYSTEM SET work_mem = 64MB;

-- 调整维护工作内存
ALTER SYSTEM SET maintenance_work_mem = 128MB;

-- 启用查询计划缓存
ALTER SYSTEM SET enable_querycache = on;

-- 设置查询计划缓存大小
ALTER SYSTEM SET shared_buffers = 256MB;
EOF
```

#### 优化Redis配置
```bash
# Redis配置优化
docker exec -it redis redis-cli <<EOF
-- 设置最大内存限制
CONFIG SET maxmemory 2gb

-- 设置内存淘汰策略
CONFIG SET maxmemory-policy allkeys-lru

-- 设置持久化策略
CONFIG SET appendonly yes
CONFIG SET appendfsync everysec
EOF
```

---

## 备份和恢复

### 1. 数据库备份
```bash
# 创建数据库备份
docker exec postgres pg_dump -U postgres arya_video_agent > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i postgres psql -U postgres arya_video_agent < backup_20240115.sql
```

### 2. 数据卷备份
```bash
# 备份数据卷
docker run --rm \
  --v $(pwd)/backups:/backups \
  -v postgres_data:/data \
  -v redis_data:/data \
  alpine tar czf /backups/backup_$(date +%Y%m%d).tar.gz /data
```

### 3. 配置备份
```bash
# 备份配置文件
tar czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml nginx/
```

---

## 日志和监控

### 1. 查看应用日志
```bash
# 查看所有日志
docker-compose logs

# 查看特定服务的日志
docker-compose logs api

# 实时跟踪日志
docker-compose logs -f api

# 查看最近100行日志
docker-compose logs --tail=100 api
```

### 2. 配置日志轮转
```yaml
# docker-compose.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=arya-video-agent"
```

### 3. 集成Prometheus和Grafana
```bash
# 访问Prometheus
open http://localhost:9090

# 访问Grafana
open http://localhost:3000
```

---

## 更新部署

### 1. 重新构建镜像
```bash
# 重新构建镜像
docker-compose build

# 或者不使用缓存重新构建
docker-compose build --no-cache
```

### 2. 滚动更新部署
```bash
# 停止旧容器，启动新容器
docker-compose up -d

# 或者使用零停机部署
docker-compose up -d --force-recreate api
```

### 3. 数据库迁移
```bash
# 运行数据库迁移
docker-compose exec api alembic upgrade head

# 回滚迁移（如果需要）
docker-compose exec api alembic downgrade -1
```

---

## 健康检查

### 1. 容器健康检查
```bash
# 检查所有容器状态
docker ps

# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' arya-video-agent

# 检查容器资源使用
docker stats arya-video-agent
```

### 2. 应用健康检查
```bash
# API健康检查
curl -f "%{http_code}\n" http://localhost:8000/health

# Prometheus健康检查
curl -f "%{http_code}\n" http://localhost:9090/-/healthy

# Grafana健康检查
curl -f "%{http_code}\n" http://localhost:3000/api/health
```

---

## 性能调优

### 1. 调整数据库连接池
```bash
# 查看数据库连接数
docker exec postgres psql -U postgres -d arya_video_agent -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"

# 查看数据库锁状态
docker exec postgres psql -U postgres -d arya_video_agent -c "SELECT * FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type IS NOT NULL;"
```

### 2. 调整Redis连接池
```bash
# 查看Redis连接数
docker exec redis redis-cli INFO clients

# 查看Redis内存使用
docker exec redis redis-cli INFO memory

# 查看Redis慢查询
docker exec redis redis-cli SLOWLOG GET 10
```

### 3. 调整应用资源限制
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

---

## 故障排查

### 1. 容器无法启动
```bash
# 查看容器日志
docker-compose logs api

# 进入容器调试
docker-compose exec api sh

# 查看容器事件
docker events arya-video-agent
```

### 2. 网络连接问题
```bash
# 检查网络配置
docker network inspect arya-video-agent-network

# 测试容器间连接
docker exec -it arya-video-agent ping postgres

# 查看DNS解析
docker exec -it arya-video-agent nslookup postgres
```

### 3. 性能问题
```bash
# 查看容器资源使用
docker stats arya-video-agent postgres redis prometheus grafana

# 查看应用日志
docker-compose logs api | tail -100
```

---

## 安全检查清单

- [ ] 使用强密码（16+字符，包含大小写字母、数字和特殊字符）
- [ ] 配置防火墙，仅开放必要的端口
- [ ] 使用SSL/TLS加密所有通信
- [ ] 定期更新依赖包
- [ ] 启用应用日志（记录所有关键操作）
- [ ] 配置资源限制（防止DoS攻击）
- [ ] 使用非root用户运行容器
- [ ] 定期备份配置和数据
- [ ] 配置监控和告警
- [ ] 使用最新的Docker镜像版本

---

## 支持和联系

如有任何部署问题或建议，请联系：
- **Email**: support@arya-video-agent.com
- **GitHub Issues**: https://github.com/startcodeing/arya-video-agent/issues
- **Discord社区**: https://discord.gg/arya-video-agent

---

**文档版本**: v1.0.0
**最后更新**: 2024-01-15
**维护者**: Arya Video Agent Team
