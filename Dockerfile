# 多阶段构建 - 第一阶段：构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    zlib1g-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 多阶段构建 - 第二阶段：运行时阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/storage /app/logs && \
    chown -R appuser:appuser /app

# 安装系统依赖（仅运行时需要的）
RUN apt-get update && apt-get install -y \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=appuser:appuser app/ ./app/

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER_HOST=unix:///var/run/docker.sock \
    DOCKER_TLS_CERTDIR="" \
    DOCKER_TLS_VERIFY="" \
    APP_HOME=/app

# 暴露端口
EXPOSE 8000

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
