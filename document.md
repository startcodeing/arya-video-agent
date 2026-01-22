  1. 系统整体架构设计

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           外部接入层                                      │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  HTTP API Gateway (FastAPI)                                              │
  │  ├── RESTful API 接口                                                    │
  │  ├── WebSocket 实时状态推送                                               │
  │  └── 文件上传/下载服务                                                    │
  └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          任务调度层                                       │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  Task Scheduler (Celery + Redis)                                         │
  │  ├── 任务队列管理                                                         │
  │  ├── 优先级调度                                                           │
  │  ├── 失败重试机制                                                         │
  │  └── 并发控制                                                             │
  └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          Agent 编排层                                     │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  Agent Orchestrator                                                      │
  │  ├── Agent 生命周期管理                                                   │
  │  ├── Agent 间通信与协调                                                   │
  │  ├── 上下文共享与传递                                                     │
  │  └── 错误处理与回滚                                                       │
  │                                                                          │
  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
  │  │  Style    │ │  Story    │ │Storyboard │ │  Image    │               │
  │  │   Agent   │ │  Agent    │ │   Agent   │ │   Agent   │               │
  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │
  │                                                                          │
  │  ┌───────────┐ ┌───────────┐ ┌───────────┐                               │
  │  │  Video   │ │ Composer  │ │ Quality   │                               │
  │  │  Agent   │ │   Agent   │ │  Checker  │                               │
  │  └───────────┘ └───────────┘ └───────────┘                               │
  └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          模型抽象层                                       │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  Model Gateway                                                           │
  │  ├── LLM Provider (OpenAI, Claude, DeepSeek, etc.)                       │
  │  ├── Image Generation Provider (DALL-E, Stable Diffusion, etc.)         │
  │  ├── Video Generation Provider (Runway, Pika, etc.)                      │
  │  └── 模型路由与负载均衡                                                   │
  └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          基础服务层                                       │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  ├── Storage Service (OSS/S3/MinIO)      文件存储                         │
  │  ├── Video Processing (FFmpeg)          视频处理                         │
  │  ├── Cache Layer (Redis)                缓存服务                         │
  │  └── Logging & Monitoring (Prometheus)  监控告警                         │
  └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          数据持久层                                       │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  PostgreSQL                                                              │
  │  ├── 任务表 (tasks)                                                      │
  │  ├── 剧本表 (scripts)                                                    │
  │  ├── 分镜表 (storyboards)                                                │
  │  ├── 资源表 (resources)                                                  │
  │  └── 作业日志表 (job_logs)                                               │
  └─────────────────────────────────────────────────────────────────────────┘

  2. 技术选型说明
  ┌──────────┬───────────────────────────────┬──────────────────────────────────────────────────────────┐
  │   层次   │            技术栈             │                         选型理由                         │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ Web 框架 │ FastAPI                       │ 高性能、自动文档生成、原生异步支持、类型安全             │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 异步任务 │ Celery + Redis                │ 成熟稳定、支持分布式、丰富的任务特性（重试、链式任务等） │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 数据库   │ PostgreSQL                    │ 支持 JSONB、事务完整、适合复杂查询                       │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ ORM      │ SQLAlchemy 2.0                │ 异步支持、类型提示、成熟的生态系统                       │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 缓存     │ Redis                         │ 高性能、支持多种数据结构、Celery 依赖                    │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 视频处理 │ FFmpeg + ffmpeg-python        │ 业界标准、功能强大、Python 封装良好                      │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 模型调用 │ OpenAI SDK / Anthropic SDK    │ 标准化接口、易扩展                                       │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 文件存储 │ MinIO / AWS S3 API            │ 兼容 S3 协议、可自建部署                                 │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 消息队列 │ Redis (Celery Backend)        │ 与任务调度复用、减少组件复杂度                           │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 配置管理 │ Pydantic Settings             │ 类型安全、环境变量管理                                   │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 日志     │ Loguru                        │ 易用、支持异步、结构化日志                               │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ API 文档 │ FastAPI 自动生成 + Swagger UI │ 零配置、交互式文档                                       │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 监控     │ Prometheus + Grafana          │ 标准监控方案                                             │
  ├──────────┼───────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ 测试     │ pytest + pytest-asyncio       │ 异步测试支持、生态完善                                   │
  └──────────┴───────────────────────────────┴──────────────────────────────────────────────────────────┘
  可选扩展技术栈：
  - 流式处理：对于实时 WebSocket 推送，可集成 Socket.IO 或原生 WebSocket
  - 模型服务：如需本地部署模型，可考虑 vLLM、TensorRT-LLM
  - 视频 AI：如需视频理解，可集成 CLIP、BLIP 等模型

  3. 项目目录结构设计

  video_agent/
  ├── .github/                    # GitHub CI/CD 配置
  │   └── workflows/
  │       └── ci.yml
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                 # FastAPI 应用入口
  │   ├── config.py               # 配置管理
  │   │
  │   ├── api/                    # API 层
  │   │   ├── __init__.py
  │   │   ├── dependencies.py     # 依赖注入
  │   │   ├── routes/
  │   │   │   ├── __init__.py
  │   │   │   ├── tasks.py        # 任务相关接口
  │   │   │   ├── videos.py       # 视频相关接口
  │   │   │   ├── webhooks.py     # 回调接口
  │   │   │   └── health.py       # 健康检查
  │   │   └── schemas.py          # Pydantic 请求/响应模型
  │   │
  │   ├── core/                   # 核心业务层
  │   │   ├── __init__.py
  │   │   ├── task_manager.py     # 任务管理器
  │   │   ├── state_machine.py    # 任务状态机
  │   │   └── context.py          # Agent 上下文
  │   │
  │   ├── agents/                 # Agent 实现
  │   │   ├── __init__.py
  │   │   ├── base.py             # Agent 基类
  │   │   ├── style_agent.py      # 风格识别 Agent
  │   │   ├── story_agent.py      # 剧本生成 Agent
  │   │   ├── storyboard_agent.py # 分镜拆解 Agent
  │   │   ├── image_agent.py      # 首帧生成 Agent
  │   │   ├── video_agent.py      # 视频生成 Agent
  │   │   └── composer_agent.py   # 视频合成 Agent
  │   │
  │   ├── models/                 # 模型抽象层
  │   │   ├── __init__.py
  │   │   ├── llm/
  │   │   │   ├── __init__.py
  │   │   │   ├── base.py         # LLM 基类
  │   │   │   ├── openai.py       # OpenAI 实现
  │   │   │   └── claude.py       # Claude 实现
  │   │   ├── image/
  │   │   │   ├── __init__.py
  │   │   │   ├── base.py
  │   │   │   └── openai.py       # DALL-E 实现
  │   │   └── video/
  │   │       ├── __init__.py
  │   │       ├── base.py
  │   │       └── runway.py       # Runway 实现
  │   │
  │   ├── scheduler/              # 任务调度
  │   │   ├── __init__.py
  │   │   ├── celery_app.py       # Celery 应用配置
  │   │   └── tasks.py            # Celery 任务定义
  │   │
  │   ├── services/               # 基础服务
  │   │   ├── __init__.py
  │   │   ├── storage.py          # 文件存储服务
  │   │   ├── video_processor.py  # 视频处理服务 (FFmpeg)
  │   │   └── cache.py            # 缓存服务
  │   │
  │   ├── database/               # 数据库层
  │   │   ├── __init__.py
  │   │   ├── session.py          # 数据库会话管理
  │   │   ├── base.py             # 基类定义
  │   │   └── migrations/         # Alembic 迁移文件
  │   │
  │   ├── entities/               # 数据库实体 (ORM)
  │   │   ├── __init__.py
  │   │   ├── task.py
  │   │   ├── script.py
  │   │   ├── storyboard.py
  │   │   └── resource.py
  │   │
  │   ├── prompts/                # Prompt 模板
  │   │   ├── __init__.py
  │   │   ├── style.txt
  │   │   ├── story.txt
  │   │   ├── storyboard.txt
  │   │   └── image.txt
  │   │
  │   └── utils/                  # 工具函数
  │       ├── __init__.py
  │       ├── logger.py           # 日志配置
  │       ├── retry.py            # 重试装饰器
  │       └── validators.py       # 验证工具
  │
  ├── tests/                      # 测试
  │   ├── __init__.py
  │   ├── conftest.py             # pytest 配置
  │   ├── api/
  │   ├── agents/
  │   └── services/
  │
  ├── scripts/                    # 脚本工具
  │   ├── init_db.py              # 数据库初始化
  │   └── worker.py               # Celery Worker 启动
  │
  ├── docs/                       # 文档
  │   ├── architecture.md
  │   ├── api.md
  │   └── deployment.md
  │
  ├── .env.example                # 环境变量示例
  ├── .gitignore
  ├── docker-compose.yml          # 本地开发环境
  ├── Dockerfile                  # 生产环境镜像
  ├── requirements.txt            # Python 依赖
  ├── requirements-dev.txt        # 开发依赖
  ├── pyproject.toml              # 项目配置
  └── README.md

  4. 模块拆分与职责说明

  4.1 API 层 (app/api/)
  ┌────────────────────┬────────────────────────────────────────┐
  │        模块        │                  职责                  │
  ├────────────────────┼────────────────────────────────────────┤
  │ routes/tasks.py    │ 任务创建、查询、取消、重试接口         │
  ├────────────────────┼────────────────────────────────────────┤
  │ routes/videos.py   │ 视频下载、预览、元数据查询接口         │
  ├────────────────────┼────────────────────────────────────────┤
  │ routes/webhooks.py │ 外部模型服务的回调处理                 │
  ├────────────────────┼────────────────────────────────────────┤
  │ routes/health.py   │ 健康检查、版本信息                     │
  ├────────────────────┼────────────────────────────────────────┤
  │ schemas.py         │ 所有 API 请求/响应的 Pydantic 模型     │
  ├────────────────────┼────────────────────────────────────────┤
  │ dependencies.py    │ FastAPI 依赖注入（数据库会话、认证等） │
  └────────────────────┴────────────────────────────────────────┘
  4.2 核心业务层 (app/core/)
  ┌──────────────────┬────────────────────────────────────────┐
  │       模块       │                  职责                  │
  ├──────────────────┼────────────────────────────────────────┤
  │ task_manager.py  │ 任务生命周期管理、Agent 编排、错误处理 │
  ├──────────────────┼────────────────────────────────────────┤
  │ state_machine.py │ 任务状态转换逻辑、状态校验             │
  ├──────────────────┼────────────────────────────────────────┤
  │ context.py       │ Agent 间上下文传递、共享数据管理       │
  └──────────────────┴────────────────────────────────────────┘
  4.3 Agent 层 (app/agents/)
  ┌─────────────────────┬────────────────────────────────────────────┐
  │        模块         │                    职责                    │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ base.py             │ Agent 基类，定义标准接口和通用逻辑         │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ style_agent.py      │ 风格识别/选择，输出风格标签                │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ story_agent.py      │ 剧本生成，输出结构化剧本                   │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ storyboard_agent.py │ 分镜拆解，输出分镜列表（描述、时长、运镜） │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ image_agent.py      │ 为每个分镜生成首帧图像                     │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ video_agent.py      │ 为每个分镜生成视频                         │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ composer_agent.py   │ 视频拼接、音频合成、最终输出               │
  └─────────────────────┴────────────────────────────────────────────┘
  4.4 模型抽象层 (app/models/)
  ┌────────┬──────────────────────────────────────────────────────┐
  │  模块  │                         职责                         │
  ├────────┼──────────────────────────────────────────────────────┤
  │ llm/   │ LLM 抽象接口，支持多厂商（OpenAI、Claude、DeepSeek） │
  ├────────┼──────────────────────────────────────────────────────┤
  │ image/ │ 图像生成抽象接口（DALL-E、SD、Midjourney）           │
  ├────────┼──────────────────────────────────────────────────────┤
  │ video/ │ 视频生成抽象接口（Runway、Pika、Stable Video）       │
  └────────┴──────────────────────────────────────────────────────┘
  4.5 任务调度层 (app/scheduler/)
  ┌───────────────┬──────────────────────────────────────┐
  │     模块      │                 职责                 │
  ├───────────────┼──────────────────────────────────────┤
  │ celery_app.py │ Celery 应用配置、Broker/Backend 连接 │
  ├───────────────┼──────────────────────────────────────┤
  │ tasks.py      │ 异步任务定义、重试策略、任务链配置   │
  └───────────────┴──────────────────────────────────────┘
  4.6 基础服务层 (app/services/)
  ┌────────────────────┬─────────────────────────────────────────┐
  │        模块        │                  职责                   │
  ├────────────────────┼─────────────────────────────────────────┤
  │ storage.py         │ 文件上传/下载、URL 签名、元数据管理     │
  ├────────────────────┼─────────────────────────────────────────┤
  │ video_processor.py │ FFmpeg 封装：视频拼接、转码、缩略图生成 │
  ├────────────────────┼─────────────────────────────────────────┤
  │ cache.py           │ Redis 缓存操作、分布式锁                │
  └────────────────────┴─────────────────────────────────────────┘
  4.7 数据层 (app/database/, app/entities/)
  ┌─────────────┬───────────────────────────┐
  │    模块     │           职责            │
  ├─────────────┼───────────────────────────┤
  │ session.py  │ 数据库连接池、会话管理    │
  ├─────────────┼───────────────────────────┤
  │ base.py     │ SQLAlchemy 基类、通用字段 │
  ├─────────────┼───────────────────────────┤
  │ migrations/ │ 数据库版本管理            │
  ├─────────────┼───────────────────────────┤
  │ entities/   │ ORM 实体定义              │
  └─────────────┴───────────────────────────┘
  5. 核心数据模型设计

  5.1 任务实体 (app/entities/task.py)

  from enum import Enum
  from datetime import datetime
  from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float
  from sqlalchemy.dialects.postgresql import UUID
  import uuid

  class TaskStatus(str, Enum):
      PENDING = "pending"              # 待处理
      STYLE_DETECTION = "style_detection"  # 风格识别中
      STORY_GENERATION = "story_generation"  # 剧本生成中
      STORYBOARD_BREAKDOWN = "storyboard_breakdown"  # 分镜拆解中
      IMAGE_GENERATION = "image_generation"  # 首帧生成中
      VIDEO_GENERATION = "video_generation"  # 视频生成中
      COMPOSING = "composing"          # 视频合成中
      COMPLETED = "completed"          # 已完成
      FAILED = "failed"                # 失败
      CANCELLED = "cancelled"          # 已取消
      RETRYING = "retrying"            # 重试中

  class TaskPriority(str, Enum):
      LOW = "low"
      NORMAL = "normal"
      HIGH = "high"
      URGENT = "urgent"

  class Task(Base):
      __tablename__ = "tasks"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id = Column(String(100), nullable=False, index=True)

      # 输入
      topic = Column(Text, nullable=False)
      style = Column(String(100))  # 可指定风格或由 Agent 识别
      options = Column(JSON, default={})  # 额外配置项

      # 状态管理
      status = Column(String(50), default=TaskStatus.PENDING, index=True)
      priority = Column(String(20), default=TaskPriority.NORMAL)
      retry_count = Column(Integer, default=0)
      max_retries = Column(Integer, default=3)

      # 进度追踪
      current_agent = Column(String(100))
      progress = Column(Float, default=0.0)
      estimated_duration = Column(Integer)  # 预估秒数
      elapsed_duration = Column(Integer, default=0)

      # 错误处理
      error_message = Column(Text)
      error_code = Column(String(50))
      failed_step = Column(String(100))

      # 输出
      output_video_url = Column(String(500))
      output_video_path = Column(String(500))
      output_metadata = Column(JSON, default={})

      # 时间戳
      created_at = Column(DateTime, default=datetime.utcnow)
      started_at = Column(DateTime)
      completed_at = Column(DateTime)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  5.2 剧本实体 (app/entities/script.py)

  class Script(Base):
      __tablename__ = "scripts"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)

      # 剧本内容
      title = Column(String(500))
      synopsis = Column(Text)
      content = Column(Text, nullable=False)  # 完整剧本文本
      structured_content = Column(JSON, default={})  # 结构化剧本（场景、台词等）

      # 风格信息
      style_tags = Column(JSON, default=[])
      visual_style = Column(String(200))
      mood = Column(String(100))

      # 元数据
      total_duration = Column(Integer)  # 预计总时长（秒）
      scene_count = Column(Integer)  # 场景数量

      # 模型信息
      llm_model = Column(String(100))
      llm_tokens_used = Column(Integer)

      created_at = Column(DateTime, default=datetime.utcnow)

  5.3 分镜实体 (app/entities/storyboard.py)

  class Storyboard(Base):
      __tablename__ = "storyboards"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
      script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=False)

      # 分镜信息
      sequence_number = Column(Integer, nullable=False)  # 序号
      title = Column(String(200))
      description = Column(Text, nullable=False)  # 画面描述
      dialogue = Column(Text)  # 台词

      # 视觉信息
      camera_movement = Column(String(100))  # 运镜方式（pan, zoom, static, tracking等）
      shot_type = Column(String(100))  # 镜头类型（wide, medium, close-up等）
      duration = Column(Float, default=3.0)  # 时长（秒）

      # 生成状态
      first_frame_image_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"))
      video_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"))
      generation_status = Column(String(50), default="pending")

      # 增强信息
      composition_notes = Column(Text)
      lighting = Column(String(100))
      color_palette = Column(JSON, default=[])

      created_at = Column(DateTime, default=datetime.utcnow)
      generated_at = Column(DateTime)

  5.4 资源实体 (app/entities/resource.py)

  class ResourceType(str, Enum):
      IMAGE = "image"
      VIDEO = "video"
      AUDIO = "audio"
      THUMBNAIL = "thumbnail"

  class Resource(Base):
      __tablename__ = "resources"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)

      # 资源信息
      resource_type = Column(String(20), nullable=False)
      file_name = Column(String(255))
      file_path = Column(String(500), nullable=False)
      file_size = Column(Integer)  # 字节
      mime_type = Column(String(100))

      # 存储
      storage_provider = Column(String(50), default="local")  # local, oss, s3
      storage_key = Column(String(500))
      public_url = Column(String(500))
      signed_url = Column(String(500))  # 临时访问 URL
      signed_url_expires_at = Column(DateTime)

      # 媒体元数据
      width = Column(Integer)
      height = Column(Integer)
      duration = Column(Float)  # 视频/音频时长
      fps = Column(Float)  # 视频帧率
      codec = Column(String(50))

      # 生成信息
      generation_model = Column(String(100))
      generation_prompt = Column(Text)
      generation_parameters = Column(JSON, default={})

      created_at = Column(DateTime, default=datetime.utcnow)
      expires_at = Column(DateTime)  # 资源过期时间

  6. API 设计草案

  6.1 任务相关 API

  创建视频生成任务

  POST /api/v1/tasks

  请求体：
  {
    "topic": "一个关于AI技术发展的纪录片风格视频，时长约60秒",
    "style": "documentary",  // 可选，不填则自动识别
    "options": {
      "duration": 60,
      "resolution": "1080p",
      "include_audio": true,
      "voice_type": "male-professional"
    }
  }

  响应：
  {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "estimated_duration": 300,
    "created_at": "2026-01-21T10:00:00Z",
    "webhook_url": "https://your-domain.com/callback"
  }

  查询任务状态

  GET /api/v1/tasks/{task_id}

  响应：
  {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "video_generation",
    "progress": 0.65,
    "current_step": "生成分镜视频 (3/5)",
    "created_at": "2026-01-21T10:00:00Z",
    "started_at": "2026-01-21T10:00:05Z",
    "elapsed": 120,
    "estimated_remaining": 60,
    "storyboard": {
      "total": 5,
      "completed": 3,
      "current": 4
    }
  }

  取消任务

  POST /api/v1/tasks/{task_id}/cancel

  重试失败任务

  POST /api/v1/tasks/{task_id}/retry

  获取任务列表

  GET /api/v1/tasks?status=completed&page=1&page_size=20

  6.2 视频相关 API

  下载生成的视频

  GET /api/v1/tasks/{task_id}/video

  返回视频流或重定向到临时签名 URL

  获取视频元数据

  GET /api/v1/tasks/{task_id}/video/metadata

  响应：
  {
    "duration": 59.8,
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "codec": "h264",
    "bitrate": 5000000,
    "file_size": 24500000,
    "format": "mp4"
  }

  获取视频缩略图

  GET /api/v1/tasks/{task_id}/thumbnail?time=30

  6.3 WebSocket 实时推送

  WS /api/v1/ws/tasks/{task_id}

  消息格式：
  {
    "event": "progress_update",
    "data": {
      "status": "video_generation",
      "progress": 0.6,
      "message": "正在生成分镜 3/5 的视频",
      "current_agent": "video_agent"
    },
    "timestamp": "2026-01-21T10:02:30Z"
  }

  支持事件类型：
  - task_created
  - status_changed
  - progress_update
  - error_occurred
  - task_completed
  - task_failed

  6.4 Webhook 回调

  系统在任务完成或失败时，向用户配置的 webhook URL 发送通知。

  请求体：
  {
    "event": "task.completed",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "output": {
      "video_url": "https://storage.example.com/videos/task_xxx.mp4",
      "thumbnail_url": "https://storage.example.com/thumbnails/task_xxx.jpg",
      "metadata": {
        "duration": 59.8,
        "resolution": "1920x1080"
      }
    },
    "timestamp": "2026-01-21T10:05:00Z",
    "signature": "sha256=abc123..."
  }

  7. Agent 调度流程设计

  7.1 整体流程图

  用户请求
      ↓
  [Task Manager] 创建任务，状态：PENDING
      ↓
  [Task Scheduler] 提交异步任务到队列
      ↓
  [Celery Worker] 执行主任务
      ↓
  ┌─────────────────────────────────────────────────────────────┐
  │                    Agent Orchestrator                        │
  ├─────────────────────────────────────────────────────────────┤
  │                                                             │
  │  ┌──────────────────┐                                       │
  │  │  Style Agent     │ ← 风格识别/选择                       │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │  ┌──────────────────┐                                       │
  │  │  Story Agent     │ ← 剧本生成                           │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │  ┌──────────────────┐                                       │
  │  │ Storyboard Agent │ ← 分镜拆解                           │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │  ┌──────────────────┐                                       │
  │  │  Image Agent    │ ← 首帧生成 (并发)                    │
  │  │  (并行 N 个)    │                                       │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │  ┌──────────────────┐                                       │
  │  │  Video Agent    │ ← 视频生成 (并发)                     │
  │  │  (并行 N 个)    │                                       │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │  ┌──────────────────┐                                       │
  │  │ Composer Agent  │ ← 视频拼接合成                        │
  │  └────────┬─────────┘                                       │
  │           ↓                                                 │
  │      [任务完成]                                             │
  └─────────────────────────────────────────────────────────────┘

  7.2 Agent 基类设计

  # app/agents/base.py
  from abc import ABC, abstractmethod
  from typing import Any, Dict, Optional
  from app.core.context import AgentContext
  from app.entities.task import Task

  class BaseAgent(ABC):
      """Agent 基类，定义标准接口"""

      agent_name: str
      retry_times: int = 3
      timeout: int = 300

      def __init__(self, context: AgentContext):
          self.context = context

      @abstractmethod
      async def execute(self, task: Task) -> Dict[str, Any]:
          """执行 Agent 逻辑"""
          pass

      async def execute_with_retry(self, task: Task) -> Dict[str, Any]:
          """带重试的执行"""
          last_error = None
          for attempt in range(self.retry_times):
              try:
                  self.context.log(f"{self.agent_name} 执行中... (尝试 {attempt + 1}/{self.retry_times})")
                  return await self.execute(task)
              except Exception as e:
                  last_error = e
                  self.context.log(f"{self.agent_name} 失败: {str(e)}")
                  if attempt < self.retry_times - 1:
                      await self._backoff(attempt)

          raise Exception(f"{self.agent_name} 执行失败: {str(last_error)}")

      async def _backoff(self, attempt: int):
          """退避策略"""
          import asyncio
          delay = 2 ** attempt  # 指数退避
          await asyncio.sleep(delay)

  7.3 Agent 编排逻辑

  # app/core/task_manager.py
  from typing import Dict, Any
  from app.agents.style_agent import StyleAgent
  from app.agents.story_agent import StoryAgent
  from app.agents.storyboard_agent import StoryboardAgent
  from app.agents.image_agent import ImageAgent
  from app.agents.video_agent import VideoAgent
  from app.agents.composer_agent import ComposerAgent

  class TaskManager:
      """任务管理器，编排 Agent 执行流程"""

      def __init__(self, context: AgentContext):
          self.context = context
          self.agents = {
              "style": StyleAgent,
              "story": StoryAgent,
              "storyboard": StoryboardAgent,
              "image": ImageAgent,
              "video": VideoAgent,
              "composer": ComposerAgent,
          }

      async def run_pipeline(self, task: Task) -> Dict[str, Any]:
          """运行完整的 Agent 流水线"""
          pipeline = [
              ("style", TaskStatus.STYLE_DETECTION),
              ("story", TaskStatus.STORY_GENERATION),
              ("storyboard", TaskStatus.STORYBOARD_BREAKDOWN),
              ("image", TaskStatus.IMAGE_GENERATION),
              ("video", TaskStatus.VIDEO_GENERATION),
              ("composer", TaskStatus.COMPOSING),
          ]

          result = {}

          for agent_name, status in pipeline:
              # 更新任务状态
              await self.context.update_task_status(task.id, status, agent_name)

              # 执行 Agent
              agent_class = self.agents[agent_name]
              agent = agent_class(self.context)

              step_result = await agent.execute_with_retry(task)
              result[agent_name] = step_result

              # 计算进度
              progress = self._calculate_progress(pipeline, agent_name)
              await self.context.update_task_progress(task.id, progress)

          # 标记任务完成
          await self.context.update_task_status(task.id, TaskStatus.COMPLETED)
          await self.context.update_task_output(task.id, result["composer"])

          return result

      def _calculate_progress(self, pipeline: list, current_agent: str) -> float:
          """计算当前进度百分比"""
          total_steps = len(pipeline)
          current_step = next(
              (i for i, (name, _) in enumerate(pipeline) if name == current_agent),
              0
          )
          return (current_step + 1) / total_steps

  7.4 并发处理设计

  # app/agents/image_agent.py (并发示例)
  import asyncio
  from typing import List, Dict
  from app.entities.storyboard import Storyboard

  class ImageAgent(BaseAgent):
      agent_name = "Image Agent"

      async def execute(self, task: Task) -> Dict[str, Any]:
          # 获取分镜列表
          storyboards = await self.context.get_storyboards(task.id)

          # 并发生成首帧
          semaphore = asyncio.Semaphore(3)  # 限制并发数

          async def generate_image(sb: Storyboard):
              async with semaphore:
                  return await self._generate_single_image(sb)

          results = await asyncio.gather(
              *[generate_image(sb) for sb in storyboards],
              return_exceptions=True
          )

          # 处理结果
          success_count = 0
          for sb, result in zip(storyboards, results):
              if isinstance(result, Exception):
                  await self.context.log(f"分镜 {sb.sequence_number} 首帧生成失败: {result}")
              else:
                  await self.context.save_image_resource(sb, result)
                  success_count += 1

          return {"generated_count": success_count, "total_count": len(storyboards)}

  8. 任务状态机设计

  8.1 状态转换图

                      ┌──────────────┐
                      │   PENDING    │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │STYLE_DETECTION│
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ STORY_GENER- │
                      │    ATION     │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │STORYBOARD_   │
                      │  BREAKDOWN   │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ IMAGE_GENER- │
                      │   ATION      │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ VIDEO_GENER- │
                      │   ATION      │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  COMPOSING   │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  COMPLETED   │
                      └──────────────┘

          任何状态 ──[取消操作]──▶ CANCELLED
          任何状态 ──[失败]──▶ FAILED
          FAILED ──[重试]──▶ RETRYING ──[重置步骤]──▶ 失败步骤的状态

  8.2 状态机实现

  # app/core/state_machine.py
  from enum import Enum
  from typing import Dict, Set, Optional, Callable

  class TaskState:
      """任务状态定义"""
      PENDING = "pending"
      STYLE_DETECTION = "style_detection"
      STORY_GENERATION = "story_generation"
      STORYBOARD_BREAKDOWN = "storyboard_breakdown"
      IMAGE_GENERATION = "image_generation"
      VIDEO_GENERATION = "video_generation"
      COMPOSING = "composing"
      COMPLETED = "completed"
      FAILED = "failed"
      CANCELLED = "cancelled"
      RETRYING = "retrying"

  class StateTransitionError(Exception):
      """状态转换错误"""
      pass

  class TaskStateMachine:
      """任务状态机"""

      # 定义状态转换规则
      TRANSITIONS: Dict[str, Set[str]] = {
          TaskState.PENDING: {TaskState.STYLE_DETECTION, TaskState.CANCELLED},
          TaskState.STYLE_DETECTION: {
              TaskState.STORY_GENERATION,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.STORY_GENERATION: {
              TaskState.STORYBOARD_BREAKDOWN,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.STORYBOARD_BREAKDOWN: {
              TaskState.IMAGE_GENERATION,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.IMAGE_GENERATION: {
              TaskState.VIDEO_GENERATION,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.VIDEO_GENERATION: {
              TaskState.COMPOSING,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.COMPOSING: {
              TaskState.COMPLETED,
              TaskState.FAILED,
              TaskState.CANCELLED
          },
          TaskState.FAILED: {TaskState.RETRYING},
          TaskState.RETRYING: {
              TaskState.STYLE_DETECTION,
              TaskState.STORY_GENERATION,
              TaskState.STORYBOARD_BREAKDOWN,
              TaskState.IMAGE_GENERATION,
              TaskState.VIDEO_GENERATION,
              TaskState.COMPOSING
          },
          TaskState.COMPLETED: set(),  # 终态
          TaskState.CANCELLED: set(),  # 终态
      }

      # 终态集合
      TERMINAL_STATES = {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}

      # 可重试状态
      RETRYABLE_STATES = {
          TaskState.STYLE_DETECTION,
          TaskState.STORY_GENERATION,
          TaskState.STORYBOARD_BREAKDOWN,
          TaskState.IMAGE_GENERATION,
          TaskState.VIDEO_GENERATION,
          TaskState.COMPOSING
      }

      @classmethod
      def can_transition(cls, from_state: str, to_state: str) -> bool:
          """检查状态转换是否合法"""
          if from_state not in cls.TRANSITIONS:
              return False
          return to_state in cls.TRANSITIONS[from_state]

      @classmethod
      def validate_transition(cls, from_state: str, to_state: str) -> None:
          """验证状态转换，不合法则抛出异常"""
          if not cls.can_transition(from_state, to_state):
              raise StateTransitionError(
                  f"Invalid state transition: {from_state} -> {to_state}"
              )

      @classmethod
      def is_terminal(cls, state: str) -> bool:
          """检查是否为终态"""
          return state in cls.TERMINAL_STATES

      @classmethod
      def get_retry_state(cls, failed_step: str) -> str:
          """根据失败步骤获取重试后的起始状态"""
          retry_map = {
              "style_agent": TaskState.STYLE_DETECTION,
              "story_agent": TaskState.STORY_GENERATION,
              "storyboard_agent": TaskState.STORYBOARD_BREAKDOWN,
              "image_agent": TaskState.IMAGE_GENERATION,
              "video_agent": TaskState.VIDEO_GENERATION,
              "composer_agent": TaskState.COMPOSING,
          }
          return retry_map.get(failed_step, TaskState.PENDING)

      @classmethod
      def get_next_state(cls, current_state: str) -> Optional[str]:
          """获取下一个状态（用于正常流程）"""
          normal_flow = [
              TaskState.PENDING,
              TaskState.STYLE_DETECTION,
              TaskState.STORY_GENERATION,
              TaskState.STORYBOARD_BREAKDOWN,
              TaskState.IMAGE_GENERATION,
              TaskState.VIDEO_GENERATION,
              TaskState.COMPOSING,
              TaskState.COMPLETED,
          ]
          try:
              index = normal_flow.index(current_state)
              return normal_flow[index + 1] if index + 1 < len(normal_flow) else None
          except ValueError:
              return None

  8.3 状态转换事件钩子

  from typing import Callable

  class StateMachineWithHooks(TaskStateMachine):
      """带钩子的状态机"""

      _hooks: Dict[str, Callable] = {}

      @classmethod
      def register_hook(cls, state: str, callback: Callable):
          """注册状态转换钩子"""
          cls._hooks[state] = callback

      @classmethod
      async def trigger_hook(cls, state: str, *args, **kwargs):
          """触发状态钩子"""
          if state in cls._hooks:
              await cls._hooks[state](*args, **kwargs)

  # 使用示例
  async def on_task_completed(task_id: str, result: dict):
      """任务完成钩子"""
      # 发送通知
      await send_notification(task_id, "任务完成")
      # 清理临时资源
      await cleanup_temp_resources(task_id)

  StateMachineWithHooks.register_hook(TaskState.COMPLETED, on_task_completed)

  9. MVP 开发里程碑计划（按周拆解）

  第 1 周：项目初始化与基础架构搭建

  目标：建立可运行的项目骨架

  任务清单：
  - 创建项目目录结构
  - 配置 FastAPI 应用基础框架
  - 配置 PostgreSQL 数据库连接
  - 创建数据库实体模型（Task, Script, Storyboard, Resource）
  - 配置 Alembic 数据库迁移
  - 配置 Redis 连接
  - 配置 Celery 基础设置
  - 实现基础的健康检查接口
  - 编写基本的日志系统
  - 编写第一个集成测试

  交付物：
  - 可启动的 FastAPI 应用
  - 数据库 schema 初始化
  - 健康检查接口可访问

  ---
  第 2 周：核心 Agent 基类与模型抽象层

  目标：建立 Agent 框架和模型抽象

  任务清单：
  - 实现 BaseAgent 抽象类
  - 实现模型抽象基类（LLM, Image, Video）
  - 实现 OpenAI LLM Provider
  - 实现 OpenAI Image Provider (DALL-E)
  - 实现 Runway Video Provider（或使用 Mock）
  - 实现模型路由逻辑
  - 编写 Agent 上下文管理
  - 编写模型调用的单元测试
  - 添加 API 密钥管理机制

  交付物：
  - Agent 基类框架
  - 至少一个 LLM 和图像生成模型可用
  - 模型调用单元测试通过

  ---
  第 3 周：任务管理与调度系统

  目标：实现任务创建和调度功能

  任务清单：
  - 实现任务状态机
  - 实现任务管理器基础功能
  - 实现任务创建 API
  - 实现 Celery 异步任务框架
  - 实现任务队列优先级管理
  - 实现基础的重试机制
  - 实现任务状态查询 API
  - 添加任务持久化逻辑
  - 编写任务调度集成测试

  交付物：
  - 任务可创建并提交到队列
  - 任务状态可查询
  - Celery Worker 可执行任务

  ---
  第 4 周：Style Agent 与 Story Agent

  目标：实现风格识别和剧本生成

  任务清单：
  - 实现 Style Agent
  - 设计并测试风格识别 Prompt
  - 实现 Story Agent
  - 设计剧本生成 Prompt
  - 实现剧本结构化输出解析
  - 实现 Script 实体保存
  - 添加风格识别单元测试
  - 添加剧本生成单元测试
  - 端到端测试：从主题到剧本

  交付物：
  - 输入主题 → 输出风格和完整剧本
  - 单元测试覆盖率 > 80%

  ---
  第 5 周：Storyboard Agent 与分镜拆解

  目标：实现分镜拆解功能

  任务清单：
  - 实现 Storyboard Agent
  - 设计分镜拆解 Prompt
  - 实现分镜数据解析
  - 实现 Storyboard 实体保存
  - 支持分镜元数据（运镜、镜头类型、时长）
  - 添加分镜拆解单元测试
  - 实现分镜可视化输出（可选）
  - 集成测试：从剧本到分镜列表

  交付物：
  - 输入剧本 → 输出结构化分镜列表
  - 支持自定义分镜参数

  ---
  第 6 周：Image Agent 首帧生成

  目标：实现首帧图像生成

  任务清单：
  - 实现 Image Agent
  - 设计首帧生成 Prompt 模板
  - 实现图像生成接口调用
  - 实现并发图像生成（控制并发数）
  - 实现图像资源保存
  - 添加图像生成进度追踪
  - 实现图像生成失败重试
  - 编写并发处理单元测试

  交付物：
  - 为每个分镜生成首帧图像
  - 支持并发加速
  - 图像存储到 OSS/本地

  ---
  第 7 周：Video Agent 视频生成

  目标：实现分镜视频生成

  任务清单：
  - 实现 Video Agent
  - 实现视频生成 API 调用
  - 设计视频生成 Prompt（基于首帧）
  - 实现并发视频生成
  - 实现视频资源保存
  - 添加视频生成进度追踪
  - 实现视频生成超时处理
  - 添加视频生成重试机制
  - 编写视频生成单元测试

  交付物：
  - 为每个分镜生成视频
  - 支持基于首帧的视频生成
  - 进度实时更新

  ---
  第 8 周：Composer Agent 与 FFmpeg 集成

  目标：实现视频拼接和合成

  任务清单：
  - 实现 Composer Agent
  - 集成 FFmpeg Python 封装
  - 实现视频拼接功能
  - 实现转场效果（可选）
  - 添加音频轨道支持
  - 实现视频编码设置（分辨率、码率）
  - 生成最终输出视频
  - 生成视频缩略图
  - 编写视频合成集成测试

  交付物：
  - 完整视频输出
  - 视频元数据正确
  - 缩略图生成

  ---
  第 9 周：任务编排与错误处理

  目标：完善 Agent 编排流程

  任务清单：
  - 实现 Agent Orchestrator
  - 完善任务完整流水线
  - 实现跨 Agent 上下文传递
  - 实现优雅的错误处理
  - 实现任务失败回滚机制
  - 实现任务取消功能
  - 添加详细的任务日志
  - 端到端集成测试

  交付物：
  - 完整的 Agent 流水线可运行
  - 错误处理机制完善
  - 日志清晰可追踪

  ---
  第 10 周：WebSocket 实时推送与状态追踪

  目标：实现实时进度推送

  任务清单：
  - 实现 WebSocket 连接管理
  - 实现任务进度实时推送
  - 定义 WebSocket 消息格式
  - 实现连接认证
  - 实现连接断开处理
  - 添加前端 WebSocket 客户端示例
  - 编写 WebSocket 集成测试

  交付物：
  - WebSocket 接口可用
  - 实时进度推送正常
  - 连接管理稳定

  ---
  第 11 周：API 完善与文档

  目标：完善 API 接口和文档

  任务清单：
  - 实现视频下载接口
  - 实现视频元数据查询接口
  - 实现缩略图获取接口
  - 实现任务列表查询（分页、过滤）
  - 实现 Webhook 回调功能
  - 完善 API 错误响应格式
  - 添加 API 请求验证
  - 生成完整的 API 文档（Swagger）
  - 编写 API 使用示例

  交付物：
  - 完整的 REST API
  - API 文档完整
  - Webhook 功能可用

  ---
  第 12 周：性能优化与压力测试

  目标：系统性能优化

  任务清单：
  - 数据库查询优化（添加索引）
  - 缓存热点数据（Redis）
  - 优化 Celery 任务并发配置
  - 实现资源清理策略
  - 添加请求限流机制
  - 性能基准测试
  - 压力测试（模拟并发任务）
  - 识别并修复性能瓶颈
  - 优化内存使用

  交付物：
  - 性能测试报告
  - 性能优化完成
  - 支持并发任务数 > 10

  ---
  第 13 周：监控告警与日志

  目标：完善运维体系

  任务清单：
  - 集成 Prometheus 监控
  - 定义关键监控指标
  - 实现 Grafana 仪表盘
  - 配置告警规则
  - 实现错误日志聚合
  - 添加性能指标追踪
  - 实现任务执行时间统计
  - 配置日志保留策略

  交付物：
  - 监控系统可用
  - 告警规则配置
  - Grafana 仪表盘

  ---
  第 14 周：Docker 化与部署

  目标：容器化部署

  任务清单：
  - 编写 Dockerfile
  - 编写 docker-compose.yml
  - 配置多阶段构建优化镜像大小
  - 编写部署文档
  - 配置环境变量管理
  - 实现数据库迁移自动化
  - 配置健康检查
  - 测试容器化部署

  交付物：
  - Docker 镜像可构建
  - docker-compose 可一键启动
  - 部署文档完整

  ---
  第 15 周：CI/CD 与自动化测试

  目标：建立持续集成流程

  任务清单：
  - 配置 GitHub Actions CI
  - 实现代码自动检查（linting）
  - 实现自动单元测试
  - 实现自动集成测试
  - 配置代码覆盖率报告
  - 配置自动 Docker 镜像构建
  - 添加安全扫描
  - 编写开发者文档

  交付物：
  - CI/CD 流程可用
  - 自动测试通过
  - 开发者文档完整

  ---
  第 16 周：生产环境准备与上线

  目标：生产就绪

  任务清单：
  - 生产环境配置清单
  - 安全加固（API 认证、HTTPS）
  - 配置备份策略
  - 配置灾难恢复计划
  - 生产环境部署测试
  - 性能基准验证
  - 用户手册编写
  - 运维手册编写
  - 上线准备检查

  交付物：
  - 生产环境可部署
  - 文档完整
  - 系统可上线

  ---
  MVP 里程碑总结
  ┌────────────┬───────┬────────────────────────────────────────┐
  │    阶段    │ 周次  │               主要交付物               │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 基础架构   │ 1-3   │ 项目骨架、Agent 框架、任务调度         │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 核心 Agent │ 4-7   │ Style、Story、Storyboard、Image、Video │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 视频合成   │ 8     │ Composer Agent、FFmpeg 集成            │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 系统完善   │ 9-11  │ 编排、错误处理、API、WebSocket         │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 优化运维   │ 12-13 │ 性能优化、监控告警                     │
  ├────────────┼───────┼────────────────────────────────────────┤
  │ 部署上线   │ 14-16 │ Docker、CI/CD、生产环境                │
  └────────────┴───────┴────────────────────────────────────────┘
  10. 风险点与优化建议

  10.1 技术风险点

  1. 模型 API 不稳定性

  风险描述：
  - 模型 API 可能超时、限流、服务中断
  - 不同模型输出格式不一致
  - API 响应时间不可预测

  应对策略：
  # 多模型冗余 + 降级策略
  class ModelManager:
      PRIMARY_MODEL = "openai"
      BACKUP_MODELS = ["claude", "deepseek"]

      async def call_with_fallback(self, prompt: str):
          for model in [self.PRIMARY_MODEL] + self.BACKUP_MODELS:
              try:
                  return await self._call_model(model, prompt)
              except Exception as e:
                  self.logger.warning(f"Model {model} failed: {e}")
                  continue
          raise Exception("All models failed")

  优化建议：
  - 实现多厂商模型备选方案
  - 实现本地缓存机制，相同 prompt 缓存结果
  - 设置合理的超时时间和重试策略
  - 监控模型 API 调用成功率

  ---
  2. 视频生成时间长

  风险描述：
  - 单个视频生成可能需要数分钟
  - 多个分镜串行生成会导致总时间过长
  - 用户体验差

  应对策略：
  # 并发生成 + 进度推送
  import asyncio

  async def generate_videos_parallel(storyboards: List[Storyboard]):
      semaphore = asyncio.Semaphore(5)  # 限制并发数
      tasks = []

      for sb in storyboards:
          task = generate_video_with_semaphore(sb, semaphore)
          tasks.append(task)

      results = await asyncio.gather(*tasks, return_exceptions=True)
      return results

  async def generate_video_with_semaphore(sb: Storyboard, semaphore):
      async with semaphore:
          # 发送进度更新
          await publish_progress(f"开始生成分镜 {sb.sequence_number}")
          video = await video_model.generate(sb.prompt)
          await publish_progress(f"分镜 {sb.sequence_number} 完成")
          return video

  优化建议：
  - 实现智能并发控制，根据 API 限流调整
  - 提供实时进度推送（WebSocket）
  - 实现任务优先级队列
  - 考虑视频生成预加载（提前开始下一批次）

  ---
  3. FFmpeg 视频合成失败

  风险描述：
  - 分镜视频编码格式不一致
  - 分辨率、帧率不匹配
  - 内存不足导致崩溃

  应对策略：
  # 统一编码 + 分片处理
  class VideoComposer:
      def __init__(self):
          self.output_codec = "h264"
          self.output_fps = 30
          self.output_resolution = (1920, 1080)

      async def compose_video(self, segments: List[str], output_path: str):
          # 预处理：统一编码
          normalized_segments = []
          for seg in segments:
              normalized = await self._normalize_video(seg)
              normalized_segments.append(normalized)

          # 合成
          await self._ffmpeg_concat(normalized_segments, output_path)

      async def _normalize_video(self, input_path: str) -> str:
          """统一视频编码格式"""
          output_path = f"{input_path}_normalized.mp4"
          cmd = [
              "ffmpeg", "-i", input_path,
              "-c:v", self.output_codec,
              "-r", str(self.output_fps),
              "-vf", f"scale={self.output_resolution[0]}:{self.output_resolution[1]}",
              "-y", output_path
          ]
          await self._run_ffmpeg(cmd)
          return output_path

  优化建议：
  - 统一所有视频的编码参数
  - 实现分片合成，避免内存溢出
  - 添加详细的错误日志，定位合成失败原因
  - 实现合成前的格式校验

  ---
  4. 存储成本与空间管理

  风险描述：
  - 中间资源（首帧、分镜视频）占用大量存储
  - 临时资源未及时清理
  - 存储成本随用户增长线性增加

  应对策略：
  # 自动清理 + 生命周期管理
  class StorageManager:
      TEMP_RESOURCE_TTL = 86400  # 24小时
      FINAL_RESOURCE_TTL = 2592000  # 30天

      async def save_temp_resource(self, file_data: bytes) -> str:
          url = await self.storage.put(file_data)
          await self.cache.set(
              f"temp_resource:{url}",
              "1",
              expire=self.TEMP_RESOURCE_TTL
          )
          return url

      async def cleanup_expired_resources(self):
          """定时清理过期资源"""
          expired = await self.db.query(
              Resource,
              Resource.expires_at < datetime.utcnow()
          )
          for resource in expired:
              await self.storage.delete(resource.storage_key)
              await self.db.delete(resource)

      async def on_task_completed(self, task_id: str):
          """任务完成后清理中间资源"""
          temp_resources = await self.db.query(
              Resource,
              Resource.task_id == task_id,
              Resource.resource_type.in_(["temp_image", "temp_video"])
          )
          for res in temp_resources:
              await self.storage.delete(res.storage_key)
              await self.db.delete(res)

  优化建议：
  - 区分临时资源和最终资源
  - 实现自动清理定时任务
  - 设置合理的资源过期时间
  - 使用对象存储（OSS/S3）而非本地存储

  ---
  5. 任务积压与队列阻塞

  风险描述：
  - 高峰期任务大量积压
  - 长时间任务阻塞队列
  - 任务超时导致重复提交

  应对策略：
  # 优先级队列 + 任务分片
  from celery import Celery

  app = Celery('tasks', broker='redis://localhost')

  @app.task(bind=True, max_retries=3)
  def generate_video_task(self, storyboard_id: str):
      try:
          # 设置超时
          self.request.timelimit = (300, 300)
          return video_agent.generate(storyboard_id)
      except Exception as exc:
          # 指数退避重试
          raise self.retry(exc=exc, countdown=2 ** self.request.retries)

  # 按优先级路由
  app.conf.task_routes = {
      'tasks.urgent_video_task': {'queue': 'high_priority'},
      'tasks.generate_video_task': {'queue': 'normal'},
  }

  优化建议：
  - 实现任务优先级队列
  - 设置合理的任务超时时间
  - 实现任务去重机制（相同 topic + style）
  - 监控队列积压情况，动态扩缩容 Worker

  ---
  10.2 业务风险点

  1. 成本控制困难

  风险描述：
  - 模型 API 调用成本不可控
  - 失败重试导致额外成本
  - 用户恶意消耗资源

  应对策略：
  # 成本预算 + 限流
  class CostController:
      MAX_DAILY_COST_PER_USER = 50.0  # 每日最大成本 $50

      async def check_budget(self, user_id: str, estimated_cost: float) -> bool:
          daily_cost = await self.get_daily_cost(user_id)
          if daily_cost + estimated_cost > self.MAX_DAILY_COST_PER_USER:
              raise Exception("超出每日预算限制")
          return True

      async def record_cost(self, task_id: str, cost: float):
          await self.db.create(
              CostRecord(task_id=task_id, amount=cost)
          )

  # Agent 执行前检查
  class StyleAgent(BaseAgent):
      async def execute(self, task: Task):
          estimated_cost = self._estimate_cost(task.topic)
          await self.cost_controller.check_budget(task.user_id, estimated_cost)

          # 执行...
          actual_cost = await self._calculate_actual_cost()
          await self.cost_controller.record_cost(task.id, actual_cost)

  优化建议：
  - 为每个用户设置预算上限
  - 实现任务成本预估
  - 失败任务减少重试次数
  - 提供成本监控面板

  ---
  2. 生成质量不稳定

  风险描述：
  - 不同模型质量差异大
  - 同一模型输出质量不稳定
  - 用户期望与实际输出差距大

  应对策略：
  # 质量检查 + 多模型投票
  class QualityChecker:
      async def check_video_quality(self, video_path: str) -> dict:
          """视频质量检查"""
          metrics = {
              "resolution": await self._check_resolution(video_path),
              "duration": await self._check_duration(video_path),
              "visual_quality": await self._assess_visual_quality(video_path),
              "motion_quality": await self._assess_motion(video_path)
          }
          score = self._calculate_quality_score(metrics)
          return {"score": score, "metrics": metrics}

  # 多模型生成，选择最优
  class ImageAgent(BaseAgent):
      async def execute(self, task: Task):
          # 使用 2 个模型生成
          results = await asyncio.gather(
              self._generate_with_model(task, "dalle"),
              self._generate_with_model(task, "sd")
          )

          # 选择质量最高的
          best = max(results, key=lambda r: r["quality_score"])
          return best

  优化建议：
  - 实现自动化质量评估
  - 对失败/低质量结果自动重试
  - 提供质量分数供用户参考
  - 持续收集用户反馈，优化 Prompt

  ---
  10.3 扩展性优化建议

  1. 插件化 Agent 架构

  # 支持 Agent 插件动态加载
  class AgentPluginManager:
      def __init__(self):
          self.plugins: Dict[str, Type[BaseAgent]] = {}

      def register_plugin(self, name: str, agent_class: Type[BaseAgent]):
          self.plugins[name] = agent_class

      def load_from_directory(self, directory: str):
          """从目录加载 Agent 插件"""
          for file in os.listdir(directory):
              if file.endswith("_agent.py"):
                  module = importlib.import_module(f"agents.{file[:-3]}")
                  for attr in dir(module):
                      if isinstance(getattr(module, attr), type) and \
                         issubclass(getattr(module, attr), BaseAgent):
                          self.register_plugin(attr, getattr(module, attr))

  # 支持自定义 Agent
  @AgentPluginManager.register("custom_style")
  class CustomStyleAgent(BaseAgent):
      async def execute(self, task: Task):
          # 自定义风格识别逻辑
          pass

  2. 模型路由策略

  # 智能模型路由
  class ModelRouter:
      ROUTING_STRATEGY = {
          "style": "claude",      # 风格识别用 Claude
          "story": "gpt-4",       # 剧本生成用 GPT-4
          "storyboard": "gpt-4",  # 分镜用 GPT-4
          "image": "dalle-3",     # 图像用 DALL-E 3
          "video": "runway",      # 视频用 Runway
      }

      async def route(self, task_type: str, priority: str):
          """根据任务类型和优先级路由到合适的模型"""
          base_model = self.ROUTING_STRATEGY.get(task_type)

          if priority == "high":
              # 高优先级使用更好的模型
              return self._get_premium_model(base_model)
          else:
              return base_model

  3. 分布式任务执行

  # 支持分布式 Worker 扩展
  # docker-compose.yml
  services:
    api:
      build: .
      ports: ["8000:8000"]

    worker-1:
      build: .
      command: celery -A app.scheduler worker --loglevel=info -Q normal

    worker-2:
      build: .
      command: celery -A app.scheduler worker --loglevel=info -Q high_priority

    worker-3:
      build: .
      command: celery -A app.scheduler worker --loglevel=info -Q normal

    redis:
      image: redis:7-alpine

    db:
      image: postgres:15-alpine

  4. 多语言支持

  # 国际化 Prompt 模板
  class PromptTemplateManager:
      TEMPLATES = {
          "style": {
              "zh": "识别以下视频风格：{topic}",
              "en": "Identify the video style: {topic}",
              "ja": "次のビデオスタイルを識別：{topic}",
          },
          "story": {
              "zh": "根据主题生成剧本：{topic}，风格：{style}",
              "en": "Generate script for: {topic}, style: {style}",
          }
      }

      def get_template(self, name: str, lang: str) -> str:
          return self.TEMPLATES.get(name, {}).get(lang, self.TEMPLATES[name]["en"])

  ---
  10.4 安全性建议

  1. API 密钥管理

  # 使用 Vault 或环境变量管理密钥
  from pydantic import BaseSettings

  class Settings(BaseSettings):
      openai_api_key: str
      claude_api_key: str
      runway_api_key: str

      class Config:
          env_file = ".env"
          secrets_dir = "/run/secrets"  # Kubernetes secrets

  2. 输入过滤

  from pydantic import validator

  class TaskRequest(BaseModel):
      topic: str

      @validator('topic')
      def sanitize_topic(cls, v):
          # 过滤敏感词
          forbidden_words = ["暴力", "色情"]
          if any(word in v for word in forbidden_words):
              raise ValueError("输入包含敏感内容")
          return v

  3. 资源访问控制

  # 基于签名的临时 URL
  class ResourceAccessController:
      def generate_signed_url(self, resource_id: str, user_id: str, ttl: int = 3600):
          """生成带签名的临时访问 URL"""
          token = jwt.encode(
              {"resource_id": resource_id, "user_id": user_id, "exp": time.time() + ttl},
              self.secret_key
          )
          return f"{self.base_url}/resources/{resource_id}?token={token}"

      def verify_signed_url(self, token: str, resource_id: str, user_id: str):
          """验证签名"""
          try:
              payload = jwt.decode(token, self.secret_key)
              return payload["resource_id"] == resource_id and payload["user_id"] == user_id
          except:
              return False

  ---
  10.5 运维建议

  1. 监控指标

  # 关键监控指标
  METRICS = {
      "task_created_total": Counter("tasks_created_total", "Total tasks created"),
      "task_completed_total": Counter("tasks_completed_total", "Total tasks completed"),
      "task_failed_total": Counter("tasks_failed_total", "Total tasks failed"),
      "task_duration_seconds": Histogram("task_duration_seconds", "Task duration"),
      "model_api_calls_total": Counter("model_api_calls_total", "Model API calls", ["model"]),
      "model_api_latency_seconds": Histogram("model_api_latency_seconds", "Model API latency", ["model"]),
      "queue_length": Gauge("queue_length", "Queue length", ["queue_name"]),
  }

  2. 告警规则

  # Prometheus 告警规则示例
  groups:
    - name: video_agent_alerts
      rules:
        - alert: HighFailureRate
          expr: rate(tasks_failed_total[5m]) / rate(tasks_completed_total[5m]) > 0.1
          for: 5m
          annotations:
            summary: "任务失败率过高"

        - alert: LongRunningTask
          expr: task_duration_seconds > 1800
          annotations:
            summary: "任务运行超过 30 分钟"

        - alert: QueueBacklog
          expr: queue_length > 100
          for: 5m
          annotations:
            summary: "任务队列积压"

  3. 备份策略

  # 数据库备份脚本
  #!/bin/bash
  DATE=$(date +%Y%m%d_%H%M%S)
  BACKUP_DIR="/backups"
  DB_NAME="video_agent"

  # 备份数据库
  pg_dump -h localhost -U user -d $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

  # 保留最近 7 天的备份
  find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

  # 上传到 OSS
  aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://backups/video_agent/

  ---
  总结

  本设计文档提供了一套完整的生产级 Video Agent 系统架构方案，涵盖：

  1. 分层架构设计：清晰的 API、Agent、模型、数据层划分
  2. 模块化设计：职责明确的模块拆分，易于维护和扩展
  3. 完善的状态管理：状态机驱动，支持复杂的任务流转
  4. 可扩展性：支持多模型、多 Agent 插件化、分布式部署
  5. 生产就绪：监控、告警、备份、安全等运维考虑

  按照 16 周 MVP 计划执行，可以快速迭代上线，同时保持代码质量和系统稳定性。

✻ Worked for 9m 24s

❯ --continue

● 补充内容：详细实现示例

  11. 核心代码实现示例

  11.1 配置管理 (app/config.py)

  from pydantic_settings import BaseSettings
  from typing import Optional
  import os

  class Settings(BaseSettings):
      """应用配置"""

      # 应用基础配置
      APP_NAME: str = "Video Agent API"
      APP_VERSION: str = "1.0.0"
      DEBUG: bool = False
      ENV: str = "production"  # development, staging, production

      # 服务器配置
      HOST: str = "0.0.0.0"
      PORT: int = 8000

      # 数据库配置
      DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/video_agent"
      DB_POOL_SIZE: int = 20
      DB_MAX_OVERFLOW: int = 10

      # Redis 配置
      REDIS_URL: str = "redis://localhost:6379/0"
      REDIS_CACHE_TTL: int = 3600  # 1小时

      # Celery 配置
      CELERY_BROKER_URL: str = "redis://localhost:6379/0"
      CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
      CELERY_TASK_SOFT_TIME_LIMIT: int = 600  # 10分钟
      CELERY_TASK_TIME_LIMIT: int = 660  # 11分钟

      # 模型 API 配置
      OPENAI_API_KEY: str
      ANTHROPIC_API_KEY: str
      RUNWAY_API_KEY: Optional[str] = None
      STABILITY_API_KEY: Optional[str] = None

      # 模型配置
      DEFAULT_LLM_MODEL: str = "gpt-4"
      DEFAULT_IMAGE_MODEL: str = "dall-e-3"
      DEFAULT_VIDEO_MODEL: str = "runway-gen3"

      # 存储配置
      STORAGE_PROVIDER: str = "local"  # local, oss, s3
      LOCAL_STORAGE_PATH: str = "./storage"
      OSS_ACCESS_KEY_ID: Optional[str] = None
      OSS_ACCESS_KEY_SECRET: Optional[str] = None
      OSS_BUCKET: Optional[str] = None
      OSS_ENDPOINT: Optional[str] = None

      # 文件配置
      MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
      ALLOWED_VIDEO_FORMATS: list = ["mp4", "webm", "mov"]
      ALLOWED_IMAGE_FORMATS: list = ["jpg", "jpeg", "png", "webp"]

      # FFmpeg 配置
      FFMPEG_PATH: str = "ffmpeg"
      FFPROBE_PATH: str = "ffprobe"
      OUTPUT_VIDEO_CODEC: str = "libx264"
      OUTPUT_AUDIO_CODEC: str = "aac"
      OUTPUT_VIDEO_BITRATE: str = "5M"
      OUTPUT_AUDIO_BITRATE: str = "192k"
      OUTPUT_FPS: int = 30
      OUTPUT_RESOLUTION: str = "1920:1080"

      # 任务配置
      MAX_RETRY_TIMES: int = 3
      TASK_TIMEOUT: int = 1800  # 30分钟
      MAX_CONCURRENT_TASKS_PER_USER: int = 5
      MAX_CONCURRENT_GENERATIONS: int = 5  # 并发生成数

      # 成本控制
      COST_CURRENCY: str = "USD"
      DEFAULT_DAILY_BUDGET: float = 50.0

      # Webhook 配置
      WEBHOOK_TIMEOUT: int = 10
      WEBHOOK_MAX_RETRIES: int = 3

      # 日志配置
      LOG_LEVEL: str = "INFO"
      LOG_FILE: str = "./logs/app.log"
      LOG_ROTATION: str = "10 MB"
      LOG_RETENTION: str = "30 days"

      # 监控配置
      PROMETHEUS_ENABLED: bool = True
      PROMETHEUS_PORT: int = 9090

      # 安全配置
      SECRET_KEY: str
      JWT_SECRET_KEY: str
      JWT_ALGORITHM: str = "HS256"
      JWT_EXPIRATION_HOURS: int = 24

      class Config:
          env_file = ".env"
          case_sensitive = True
          extra = "allow"

  settings = Settings()

  11.2 FastAPI 应用入口 (app/main.py)

  from fastapi import FastAPI, Request, status
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi.middleware.gzip import GZipMiddleware
  from fastapi.responses import JSONResponse
  from fastapi.exceptions import RequestValidationError
  from contextlib import asynccontextmanager
  import prometheus_client as prom
  from prometheus_client import Counter, Histogram, Gauge
  import time

  from app.config import settings
  from app.api.routes import tasks, videos, health
  from app.database.session import engine, Base
  from app.utils.logger import setup_logger

  logger = setup_logger()

  # Prometheus Metrics
  REQUEST_COUNT = Counter(
      'http_requests_total',
      'Total HTTP requests',
      ['method', 'endpoint', 'status']
  )
  REQUEST_LATENCY = Histogram(
      'http_request_duration_seconds',
      'HTTP request latency',
      ['method', 'endpoint']
  )
  ACTIVE_TASKS = Gauge('active_tasks', 'Number of active tasks')

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      """应用生命周期管理"""
      # 启动时
      logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

      # 创建数据库表（开发环境）
      if settings.ENV == "development":
          async with engine.begin() as conn:
              await conn.run_sync(Base.metadata.create_all)

      yield

      # 关闭时
      logger.info("Shutting down application...")

  app = FastAPI(
      title=settings.APP_NAME,
      version=settings.APP_VERSION,
      description="AI Video Generation Agent System",
      docs_url="/api/docs" if settings.DEBUG else None,
      redoc_url="/api/redoc" if settings.DEBUG else None,
      lifespan=lifespan
  )

  # 中间件
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"] if settings.DEBUG else ["https://your-domain.com"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.add_middleware(GZipMiddleware, minimum_size=1000)

  # 请求追踪中间件
  @app.middleware("http")
  async def request_tracker(request: Request, call_next):
      """请求追踪和指标收集"""
      start_time = time.time()

      response = await call_next(request)

      # 记录指标
      duration = time.time() - start_time
      REQUEST_COUNT.labels(
          method=request.method,
          endpoint=request.url.path,
          status=response.status_code
      ).inc()
      REQUEST_LATENCY.labels(
          method=request.method,
          endpoint=request.url.path
      ).observe(duration)

      return response

  # 异常处理
  @app.exception_handler(RequestValidationError)
  async def validation_exception_handler(request: Request, exc: RequestValidationError):
      """请求验证异常处理"""
      return JSONResponse(
          status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
          content={
              "error": "Validation Error",
              "message": exc.errors(),
              "path": str(request.url)
          }
      )

  @app.exception_handler(Exception)
  async def global_exception_handler(request: Request, exc: Exception):
      """全局异常处理"""
      logger.error(f"Unhandled exception: {exc}", exc_info=True)
      return JSONResponse(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          content={
              "error": "Internal Server Error",
              "message": str(exc) if settings.DEBUG else "An error occurred",
              "path": str(request.url)
          }
      )

  # 路由注册
  app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
  app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
  app.include_router(videos.router, prefix="/api/v1/videos", tags=["Videos"])

  if settings.PROMETHEUS_ENABLED:
      from prometheus_fastapi_instrumentator import Instrumentator

      @app.on_event("startup")
      async def setup_prometheus():
          Instrumentator().instrument(app).expose(
              app,
              endpoint="/metrics",
              should_gzip=True
          )

  # 根路径
  @app.get("/")
  async def root():
      return {
          "name": settings.APP_NAME,
          "version": settings.APP_VERSION,
          "status": "running"
      }

  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(
          "app.main:app",
          host=settings.HOST,
          port=settings.PORT,
          reload=settings.DEBUG,
          log_level=settings.LOG_LEVEL.lower()
      )

  11.3 数据库会话管理 (app/database/session.py)

  from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
  from sqlalchemy.orm import declarative_base
  from app.config import settings
  from typing import Generator

  # 创建异步引擎
  engine = create_async_engine(
      settings.DATABASE_URL,
      echo=settings.DEBUG,
      pool_size=settings.DB_POOL_SIZE,
      max_overflow=settings.DB_MAX_OVERFLOW,
      pool_pre_ping=True,  # 连接健康检查
      pool_recycle=3600,   # 1小时回收连接
  )

  # 创建会话工厂
  AsyncSessionLocal = async_sessionmaker(
      engine,
      class_=AsyncSession,
      expire_on_commit=False,  # 不自动提交，避免延迟加载问题
      autoflush=False
  )

  # 基类
  Base = declarative_base()

  async def get_db() -> Generator[AsyncSession, None, None]:
      """
      数据库会话依赖注入
      使用方式: db: AsyncSession = Depends(get_db)
      """
      async with AsyncSessionLocal() as session:
          try:
              yield session
              await session.commit()
          except Exception:
              await session.rollback()
              raise
          finally:
              await session.close()

  async def init_db():
      """初始化数据库"""
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)

  async def close_db():
      """关闭数据库连接"""
      await engine.dispose()

  11.4 Agent 上下文管理 (app/core/context.py)

  from typing import Dict, Any, Optional, List
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, update
  from app.entities.task import Task, TaskStatus
  from app.entities.script import Script
  from app.entities.storyboard import Storyboard
  from app.entities.resource import Resource
  from app.utils.logger import get_logger
  from app.services.cache import CacheService
  from app.services.storage import StorageService
  import json

  logger = get_logger(__name__)

  class AgentContext:
      """
      Agent 上下文管理器
      负责跨 Agent 的数据共享、数据库操作、缓存等
      """

      def __init__(self, db: AsyncSession, task_id: str):
          self.db = db
          self.task_id = task_id
          self._cache = CacheService()
          self._storage = StorageService()
          self._shared_data: Dict[str, Any] = {}

      async def get_task(self) -> Optional[Task]:
          """获取任务信息"""
          result = await self.db.execute(select(Task).where(Task.id == self.task_id))
          return result.scalar_one_or_none()

      async def update_task_status(self, status: TaskStatus, current_agent: str = None):
          """更新任务状态"""
          await self.db.execute(
              update(Task)
              .where(Task.id == self.task_id)
              .values(
                  status=status,
                  current_agent=current_agent,
                  updated_at=datetime.utcnow()
              )
          )
          await self.db.commit()

          # 发布事件
          await self._publish_event("status_changed", {
              "task_id": self.task_id,
              "status": status,
              "current_agent": current_agent
          })

      async def update_task_progress(self, progress: float, message: str = None):
          """更新任务进度"""
          await self.db.execute(
              update(Task)
              .where(Task.id == self.task_id)
              .values(progress=progress, updated_at=datetime.utcnow())
          )
          await self.db.commit()

          # 发布进度事件
          await self._publish_event("progress_update", {
              "task_id": self.task_id,
              "progress": progress,
              "message": message
          })

      async def update_task_output(self, video_url: str, metadata: dict):
          """更新任务输出"""
          await self.db.execute(
              update(Task)
              .where(Task.id == self.task_id)
              .values(
                  output_video_url=video_url,
                  output_metadata=metadata,
                  status=TaskStatus.COMPLETED,
                  completed_at=datetime.utcnow()
              )
          )
          await self.db.commit()

      async def set_error(self, error_message: str, error_code: str = None, failed_step: str = None):
          """设置任务错误"""
          await self.db.execute(
              update(Task)
              .where(Task.id == self.task_id)
              .values(
                  status=TaskStatus.FAILED,
                  error_message=error_message,
                  error_code=error_code,
                  failed_step=failed_step,
                  updated_at=datetime.utcnow()
              )
          )
          await self.db.commit()

      def set_shared_data(self, key: str, value: Any):
          """设置共享数据（内存级）"""
          self._shared_data[key] = value

      def get_shared_data(self, key: str, default: Any = None) -> Any:
          """获取共享数据"""
          return self._shared_data.get(key, default)

      async def cache_get(self, key: str) -> Optional[Any]:
          """从缓存获取数据"""
          data = await self._cache.get(f"task:{self.task_id}:{key}")
          if data:
              return json.loads(data)
          return None

      async def cache_set(self, key: str, value: Any, ttl: int = 3600):
          """设置缓存"""
          await self._cache.set(
              f"task:{self.task_id}:{key}",
              json.dumps(value),
              ttl
          )

      async def save_script(self, script_data: dict) -> Script:
          """保存剧本"""
          script = Script(
              task_id=self.task_id,
              **script_data
          )
          self.db.add(script)
          await self.db.commit()
          await self.db.refresh(script)

          # 缓存剧本
          await self.cache_set("script", script_data)

          return script

      async def get_script(self) -> Optional[Script]:
          """获取剧本"""
          # 先查缓存
          cached = await self.cache_get("script")
          if cached:
              return Script(**cached)

          result = await self.db.execute(
              select(Script).where(Script.task_id == self.task_id)
          )
          return result.scalar_one_or_none()

      async def save_storyboards(self, storyboards: List[dict]) -> List[Storyboard]:
          """批量保存分镜"""
          entities = []
          for i, sb_data in enumerate(storyboards):
              sb = Storyboard(
                  task_id=self.task_id,
                  sequence_number=i + 1,
                  **sb_data
              )
              self.db.add(sb)
              entities.append(sb)

          await self.db.commit()
          for entity in entities:
              await self.db.refresh(entity)

          return entities

      async def get_storyboards(self) -> List[Storyboard]:
          """获取分镜列表"""
          result = await self.db.execute(
              select(Storyboard)
              .where(Storyboard.task_id == self.task_id)
              .order_by(Storyboard.sequence_number)
          )
          return list(result.scalars().all())

      async def save_image_resource(self, storyboard: Storyboard, image_data: dict) -> Resource:
          """保存图像资源"""
          resource = Resource(
              task_id=self.task_id,
              resource_type="image",
              **image_data
          )
          self.db.add(resource)
          await self.db.commit()
          await self.db.refresh(resource)

          # 更新分镜关联
          await self.db.execute(
              update(Storyboard)
              .where(Storyboard.id == storyboard.id)
              .values(first_frame_image_id=resource.id)
          )
          await self.db.commit()

          return resource

      async def save_video_resource(self, storyboard: Storyboard, video_data: dict) -> Resource:
          """保存视频资源"""
          resource = Resource(
              task_id=self.task_id,
              resource_type="video",
              **video_data
          )
          self.db.add(resource)
          await self.db.commit()
          await self.db.refresh(resource)

          # 更新分镜关联
          await self.db.execute(
              update(Storyboard)
              .where(Storyboard.id == storyboard.id)
              .values(
                  video_id=resource.id,
                  generation_status="completed"
              )
          )
          await self.db.commit()

          return resource

      async def upload_file(self, file_path: str, content: bytes, content_type: str = None) -> str:
          """上传文件到存储"""
          return await self._storage.upload(
              file_path=file_path,
              content=content,
              content_type=content_type
          )

      async def get_signed_url(self, storage_key: str, ttl: int = 3600) -> str:
          """获取临时签名 URL"""
          return await self._storage.get_signed_url(storage_key, ttl)

      async def log(self, message: str, level: str = "info"):
          """记录日志"""
          getattr(logger, level)(f"[{self.task_id}] {message}")

      async def _publish_event(self, event_type: str, data: dict):
          """发布事件（通过 Redis Pub/Sub 或 WebSocket）"""
          # 使用 Redis Pub/Sub
          import redis.asyncio as redis
          r = redis.from_url(settings.REDIS_URL)
          await r.publish(
              f"task:{self.task_id}",
              json.dumps({
                  "event": event_type,
                  "data": data,
                  "timestamp": datetime.utcnow().isoformat()
              })
          )
          await r.close()

  11.5 具体示例：Style Agent (app/agents/style_agent.py)

  from typing import Dict, Any, List
  from app.agents.base import BaseAgent
  from app.entities.task import Task
  from app.core.context import AgentContext
  from app.models.llm.openai import OpenAILLM
  from app.prompts.style import STYLE_PROMPT_TEMPLATE

  class StyleAgent(BaseAgent):
      """风格识别 Agent"""

      agent_name = "Style Agent"

      # 预定义风格列表
      AVAILABLE_STYLES = [
          "cinematic",      # 电影感
          "documentary",    # 纪录片
          "animated",       # 动画
          "minimalist",     # 极简主义
          "vintage",        # 复古
          "futuristic",     # 未来感
          "nature",         # 自然
          "urban",          # 城市生活
          "commercial",     # 商业广告
          "artistic",       # 艺术风格
          "scifi",          # 科幻
          "fantasy",        # 奇幻
      ]

      def __init__(self, context: AgentContext):
          super().__init__(context)
          self.llm = OpenAILLM()

      async def execute(self, task: Task) -> Dict[str, Any]:
          """
          识别或确认视频风格
          """
          await self.context.log("开始风格识别...")

          # 如果用户已指定风格，直接使用
          if task.style and task.style.lower() in self.AVAILABLE_STYLES:
              style = task.style.lower()
              await self.context.log(f"使用用户指定风格: {style}")

              # 获取风格详细信息
              style_details = self._get_style_details(style)

              return {
                  "style": style,
                  "style_tags": style_details["tags"],
                  "visual_style": style_details["visual"],
                  "mood": style_details["mood"],
                  "color_palette": style_details["colors"],
                  "source": "user_specified"
              }

          # 否则使用 LLM 识别风格
          await self.context.log("使用 LLM 识别风格...")

          prompt = STYLE_PROMPT_TEMPLATE.format(
              topic=task.topic,
              available_styles=", ".join(self.AVAILABLE_STYLES)
          )

          response = await self.llm.generate(
              prompt=prompt,
              model="gpt-4",
              response_format={"type": "json_object"},
              temperature=0.3
          )

          # 解析响应
          style_data = self._parse_style_response(response)

          # 保存到上下文
          self.context.set_shared_data("style", style_data["style"])
          self.context.set_shared_data("style_tags", style_data["style_tags"])
          self.context.set_shared_data("visual_style", style_data["visual_style"])

          await self.context.log(f"识别风格: {style_data['style']}")

          return style_data

      def _get_style_details(self, style: str) -> Dict[str, Any]:
          """获取风格详细信息"""
          style_database = {
              "cinematic": {
                  "tags": ["movie", "dramatic", "high-contrast", "film-grain"],
                  "visual": "High contrast, film grain, dramatic lighting",
                  "mood": "dramatic",
                  "colors": ["#1a1a2e", "#16213e", "#e94560", "#fcd34d"]
              },
              "documentary": {
                  "tags": ["realistic", "natural-lighting", "authentic", "journalistic"],
                  "visual": "Natural lighting, handheld camera movement, authentic",
                  "mood": "informative",
                  "colors": ["#374151", "#9ca3af", "#d1d5db", "#f3f4f6"]
              },
              "animated": {
                  "tags": ["colorful", "whimsical", "stylized", "smooth-motion"],
                  "visual": "Bright colors, smooth motion, stylized characters",
                  "mood": "playful",
                  "colors": ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"]
              },
              "minimalist": {
                  "tags": ["clean", "simple", "elegant", "negative-space"],
                  "visual": "Clean lines, plenty of negative space, simple compositions",
                  "mood": "calm",
                  "colors": ["#fafafa", "#f5f5f5", "#e5e5e5", "#737373"]
              },
              "vintage": {
                  "tags": ["retro", "sepia", "film-noir", "nostalgic"],
                  "visual": "Sepia tones, grain, vintage lighting",
                  "mood": "nostalgic",
                  "colors": ["#78350f", "#92400e", "#b45309", "#d97706"]
              },
              "futuristic": {
                  "tags": ["sci-fi", "neon", "cyberpunk", "high-tech"],
                  "visual": "Neon colors, holographic elements, metallic surfaces",
                  "mood": "innovative",
                  "colors": ["#00ffff", "#ff00ff", "#00ff00", "#ff0080"]
              },
              "nature": {
                  "tags": ["organic", "outdoor", "natural-light", "serene"],
                  "visual": "Natural lighting, organic shapes, earth tones",
                  "mood": "peaceful",
                  "colors": ["#065f46", "#047857", "#059669", "#10b981"]
              },
              "urban": {
                  "tags": ["city", "modern", "dynamic", "street"],
                  "visual": "Cityscape, dynamic angles, modern architecture",
                  "mood": "energetic",
                  "colors": ["#374151", "#6b7280", "#9ca3af", "#f59e0b"]
              },
              "commercial": {
                  "tags": ["polished", "bright", "professional", "high-production"],
                  "visual": "Bright lighting, polished look, professional quality",
                  "mood": "confident",
                  "colors": ["#ffffff", "#f3f4f6", "#1f2937", "#2563eb"]
              },
              "artistic": {
                  "tags": ["creative", "abstract", "experimental", "unique"],
                  "visual": "Creative compositions, artistic flair, experimental",
                  "mood": "inspiring",
                  "colors": ["#7c3aed", "#db2777", "#ea580c", "#0891b2"]
              }
          }

          return style_database.get(style, {
              "tags": ["generic"],
              "visual": "Standard quality",
              "mood": "neutral",
              "colors": ["#000000", "#ffffff"]
          })

      def _parse_style_response(self, response: str) -> Dict[str, Any]:
          """解析 LLM 响应"""
          import json

          try:
              data = json.loads(response)

              # 验证风格是否在预定义列表中
              style = data.get("style", "cinematic").lower()
              if style not in self.AVAILABLE_STYLES:
                  # 使用相似度匹配
                  style = self._find_closest_style(style)

              style_details = self._get_style_details(style)

              return {
                  "style": style,
                  "style_tags": data.get("style_tags", style_details["tags"]),
                  "visual_style": data.get("visual_style", style_details["visual"]),
                  "mood": data.get("mood", style_details["mood"]),
                  "color_palette": data.get("color_palette", style_details["colors"]),
                  "reasoning": data.get("reasoning", ""),
                  "source": "llm_detected"
              }
          except json.JSONDecodeError:
              # JSON 解析失败，使用默认
              await self.context.log("风格响应解析失败，使用默认风格", "warning")
              return {
                  "style": "cinematic",
                  **self._get_style_details("cinematic"),
                  "source": "fallback"
              }

      def _find_closest_style(self, style: str) -> str:
          """查找最接近的预定义风格"""
          from difflib import get_close_matches
          matches = get_close_matches(style, self.AVAILABLE_STYLES, n=1)
          return matches[0] if matches else "cinematic"

  11.6 Story Agent 完整实现 (app/agents/story_agent.py)

  from typing import Dict, Any, Optional
  from app.agents.base import BaseAgent
  from app.entities.task import Task
  from app.core.context import AgentContext
  from app.models.llm.openai import OpenAILLM
  from app.prompts.story import STORY_PROMPT_TEMPLATE

  class StoryAgent(BaseAgent):
      """剧本生成 Agent"""

      agent_name = "Story Agent"

      def __init__(self, context: AgentContext):
          super().__init__(context)
          self.llm = OpenAILLM()

      async def execute(self, task: Task) -> Dict[str, Any]:
          """生成完整剧本"""
          await self.context.log("开始生成剧本...")

          # 获取风格信息
          style = self.context.get_shared_data("style", "cinematic")
          style_tags = self.context.get_shared_data("style_tags", [])
          visual_style = self.context.get_shared_data("visual_style", "")

          # 计算剧本长度（基于用户输入的时长）
          estimated_duration = task.options.get("duration", 60) if task.options else 60
          scene_count = self._estimate_scene_count(estimated_duration)

          # 构建提示词
          prompt = STORY_PROMPT_TEMPLATE.format(
              topic=task.topic,
              style=style,
              visual_style=visual_style,
              estimated_duration=estimated_duration,
              scene_count=scene_count
          )

          # 调用 LLM
          response = await self.llm.generate(
              prompt=prompt,
              model="gpt-4",
              response_format={"type": "json_object"},
              temperature=0.7
          )

          # 解析剧本
          script_data = self._parse_script_response(response)
          script_data["total_duration"] = estimated_duration
          script_data["scene_count"] = len(script_data.get("scenes", []))
          script_data["style_tags"] = style_tags
          script_data["visual_style"] = visual_style

          # 保存剧本到数据库
          await self.context.save_script(script_data)

          await self.context.log(f"剧本生成完成，共 {script_data['scene_count']} 个场景")

          return script_data

      def _estimate_scene_count(self, duration: int) -> int:
          """估算场景数量"""
          # 平均每个场景 5-10 秒
          avg_scene_duration = 8
          return max(3, duration // avg_scene_duration)

      def _parse_script_response(self, response: str) -> Dict[str, Any]:
          """解析 LLM 响应"""
          import json

          try:
              data = json.loads(response)

              # 验证并标准化结构
              return {
                  "title": data.get("title", "Untitled Video"),
                  "synopsis": data.get("synopsis", ""),
                  "content": data.get("content", ""),  # 完整文本
                  "structured_content": self._normalize_structure(data.get("structure", {})),
                  "llm_model": "gpt-4",
                  "llm_tokens_used": data.get("tokens_used", 0)
              }
          except json.JSONDecodeError:
              await self.context.log("剧本响应解析失败", "error")
              raise Exception("Failed to parse script generation response")

      def _normalize_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
          """标准化剧本结构"""
          # 确保场景列表格式正确
          scenes = structure.get("scenes", [])
          normalized_scenes = []

          for i, scene in enumerate(scenes, 1):
              normalized_scenes.append({
                  "scene_number": i,
                  "title": scene.get("title", f"Scene {i}"),
                  "description": scene.get("description", ""),
                  "dialogue": scene.get("dialogue", ""),
                  "duration": scene.get("duration", 5),
                  "visual_notes": scene.get("visual_notes", ""),
                  "audio_notes": scene.get("audio_notes", "")
              })

          return {
              "scenes": normalized_scenes,
              "opening": structure.get("opening", ""),
              "closing": structure.get("closing", ""),
              "narrator": structure.get("narrator", "")
          }

  11.7 Image Agent 完整实现 (app/agents/image_agent.py)

  from typing import Dict, Any, List
  import asyncio
  from app.agents.base import BaseAgent
  from app.entities.task import Task
  from app.core.context import AgentContext
  from app.models.image.openai import OpenAIImageModel
  from app.prompts.image import IMAGE_PROMPT_TEMPLATE

  class ImageAgent(BaseAgent):
      """首帧生成 Agent"""

      agent_name = "Image Agent"

      def __init__(self, context: AgentContext):
          super().__init__(context)
          self.image_model = OpenAIImageModel()

      async def execute(self, task: Task) -> Dict[str, Any]:
          """为所有分镜生成首帧图像"""
          await self.context.log("开始生成分镜首帧...")

          # 获取分镜列表
          storyboards = await self.context.get_storyboards()
          total_count = len(storyboards)

          if total_count == 0:
              raise Exception("No storyboards found")

          await self.context.log(f"共 {total_count} 个分镜需要生成首帧")

          # 获取风格信息
          style = self.context.get_shared_data("style", "cinematic")
          visual_style = self.context.get_shared_data("visual_style", "")
          color_palette = self.context.get_shared_data("color_palette", [])

          # 并发生成（限制并发数）
          from app.config import settings
          semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_GENERATIONS)

          results = []
          for i, sb in enumerate(storyboards):
              # 更新进度
              progress = i / total_count
              await self.context.update_task_progress(
                  progress,
                  f"生成分镜 {sb.sequence_number}/{total_count} 首帧"
              )

              result = await self._generate_image_with_semaphore(
                  semaphore, sb, style, visual_style, color_palette
              )
              results.append(result)

          # 统计结果
          success_count = sum(1 for r in results if not r.get("error"))
          await self.context.log(f"首帧生成完成: {success_count}/{total_count} 成功")

          return {
              "total_count": total_count,
              "success_count": success_count,
              "failed_count": total_count - success_count,
              "results": results
          }

      async def _generate_image_with_semaphore(
          self,
          semaphore: asyncio.Semaphore,
          storyboard,
          style: str,
          visual_style: str,
          color_palette: List[str]
      ) -> Dict[str, Any]:
          """带信号量控制的图像生成"""
          async with semaphore:
              try:
                  return await self._generate_single_image(
                      storyboard, style, visual_style, color_palette
                  )
              except Exception as e:
                  await self.context.log(
                      f"分镜 {storyboard.sequence_number} 首帧生成失败: {str(e)}",
                      "error"
                  )
                  return {
                      "storyboard_id": str(storyboard.id),
                      "sequence_number": storyboard.sequence_number,
                      "error": str(e)
                  }

      async def _generate_single_image(
          self,
          storyboard,
          style: str,
          visual_style: str,
          color_palette: List[str]
      ) -> Dict[str, Any]:
          """生成单个分镜的首帧"""
          await self.context.log(f"正在生成分镜 {storyboard.sequence_number} 首帧...")

          # 构建图像生成提示词
          prompt = IMAGE_PROMPT_TEMPLATE.format(
              description=storyboard.description,
              camera_movement=storyboard.camera_movement or "static",
              shot_type=storyboard.shot_type or "medium",
              visual_style=visual_style,
              style=style,
              color_hint=f"Color palette: {', '.join(color_palette)}"
          )

          # 调用图像生成模型
          image_result = await self.image_model.generate(
              prompt=prompt,
              size="1024x1024",
              quality="hd",
              n=1
          )

          # 下载图像
          image_data = await self._download_image(image_result["url"])

          # 上传到存储
          storage_key = f"tasks/{self.context.task_id}/images/frame_{storyboard.sequence_number:03d}.png"
          public_url = await self.context.upload_file(
              file_path=storage_key,
              content=image_data,
              content_type="image/png"
          )

          # 保存资源记录
          resource = await self.context.save_image_resource(storyboard, {
              "file_name": f"frame_{storyboard.sequence_number:03d}.png",
              "file_path": storage_key,
              "public_url": public_url,
              "storage_provider": "local",
              "storage_key": storage_key,
              "file_size": len(image_data),
              "mime_type": "image/png",
              "width": 1024,
              "height": 1024,
              "generation_model": "dall-e-3",
              "generation_prompt": prompt
          })

          await self.context.log(f"分镜 {storyboard.sequence_number} 首帧生成完成")

          return {
              "storyboard_id": str(storyboard.id),
              "sequence_number": storyboard.sequence_number,
              "resource_id": str(resource.id),
              "public_url": public_url,
              "generation_prompt": prompt
          }

      async def _download_image(self, url: str) -> bytes:
          """下载图像"""
          import httpx
          async with httpx.AsyncClient(timeout=30.0) as client:
              response = await client.get(url)
              response.raise_for_status()
              return response.content

  ---
  12. Prompt 模板示例

  12.1 风格识别 Prompt (app/prompts/style.txt)

  你是一个专业的视频风格分析师。请分析以下视频主题，识别最适合的视频风格。

  ## 任务
  1. 阅读用户的视频主题描述
  2. 从以下预定义风格列表中选择最合适的风格（只能选择一个）
  3. 分析选择该风格的理由
  4. 提供该风格的详细特征描述

  ## 预定义风格列表
  - cinematic: 电影感，高对比度、电影颗粒感、戏剧性布光
  - documentary: 纪录片，自然光线、真实感、纪实风格
  - animated: 动画风格，色彩鲜艳、卡通化、流畅动作
  - minimalist: 极简主义，简洁线条、留白、干净构图
  - vintage: 复古风格，怀旧色调、胶片质感
  - futuristic: 未来感，霓虹色彩、科幻元素、金属质感
  - nature: 自然风格，有机形态、自然光线、大地色调
  - urban: 城市风格，现代建筑、动态角度、城市景观
  - commercial: 商业广告风格，精致、明亮、高质量
  - artistic: 艺术风格，创意构图、抽象元素、实验性
  - scifi: 科幻风格，科技感、未来科技
  - fantasy: 奇幻风格，魔法元素、梦幻场景

  ## 用户主题
  {topic}

  ## 输出格式（JSON）
  请以 JSON 格式输出，包含以下字段：
  ```json
  {{
    "style": "选择的风格名称",
    "style_tags": ["相关标签1", "相关标签2", "相关标签3"],
    "visual_style": "视觉风格的详细描述",
    "mood": "情感基调",
    "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
    "reasoning": "选择该风格的理由"
  }}

  注意事项

  - 只能从预定义列表中选择，不要创造新的风格
  - reasoning 应该简明扼要，解释为什么该风格适合用户的主题
  - color_palette 应该是该风格典型的配色方案（4个十六进制颜色）

  #### 12.2 剧本生成 Prompt (`app/prompts/story.txt`)

  你是一个专业的视频编剧。请根据以下信息创作一个视频剧本。

  任务

  1. 理解用户的视频主题
  2. 考虑指定的视频风格
  3. 创作一个完整的视频剧本
  4. 将剧本分解为多个场景

  输入信息

  - 视频主题: {topic}
  - 视频风格: {style}
  - 视觉风格描述: {visual_style}
  - 预估时长: {estimated_duration}秒
  - 预计场景数: {scene_count}个

  剧本结构要求

  1. 标题: 简洁有力的视频标题
  2. 简介: 2-3句话概括视频内容
  3. 完整剧本: 连续的剧本文本
  4. 结构化剧本: JSON 格式的详细场景信息

  场景结构

  每个场景应包含：
  - title: 场景标题
  - description: 画面描述（详细描述场景中的视觉元素）
  - dialogue: 台词或旁白（如有）
  - duration: 该场景的持续时长（秒）
  - visual_notes: 视觉提示（运镜、构图等）
  - audio_notes: 音频提示（背景音乐、音效等）

  输出格式（JSON）

  {{
    "title": "视频标题",
    "synopsis": "视频简介，2-3句话",
    "content": "完整的连续剧本文本，包含所有场景和台词",
    "structure": {{
      "opening": "开场白或旁白",
      "scenes": [
        {{
          "title": "场景标题",
          "description": "详细的画面描述",
          "dialogue": "台词或旁白",
          "duration": 5,
          "visual_notes": "视觉提示，如：缓慢推入镜头，聚焦于主角表情",
          "audio_notes": "音频提示，如：轻柔的背景音乐，逐渐增强"
        }}
      ],
      "closing": "结束语或旁白",
      "narrator": "旁白风格说明"
    }},
    "tokens_used": 实际使用的token数（可选）
  }}

  写作要求

  - 剧本要符合指定的视频风格
  - 场景之间的转换要流畅自然
  - 每个场景的描述要具体，便于后续生成视觉内容
  - 对话或旁白要简洁有力
  - 总时长控制在预估时长范围内（±10%）
  - 确保场景数接近预计场景数

  #### 12.3 分镜拆解 Prompt (`app/prompts/storyboard.txt`)

  你是一个专业的视频分镜师。请将以下剧本拆解为详细的分镜列表。

  任务

  1. 分析给定的剧本结构
  2. 将每个场景进一步拆分为多个镜头（分镜）
  3. 为每个分镜提供详细的视觉和运镜指导

  输入剧本

  剧本标题: {script_title}
  剧本内容: {script_content}

  视频风格

  - 风格: {style}
  - 视觉风格: {visual_style}
  - 配色方案: {color_palette}

  分镜设计原则

  1. 每个场景通常拆分为 1-3 个分镜
  2. 分镜之间要有视觉连贯性
  3. 运镜方式要服务于叙事目的
  4. 镜头类型要有变化，避免单调

  分镜信息要求

  每个分镜需要包含：
  - title: 分镜标题
  - description: 画面描述（用于图像/视频生成的详细描述）
  - dialogue: 该分镜的台词
  - camera_movement: 运镜方式（可选项：static, pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, tracking, dolly）
  - shot_type: 镜头类型（可选项：extreme_wide, wide, medium_wide, medium, medium_close, close_up, extreme_close）
  - duration: 该分镜的时长（秒）
  - composition_notes: 构图提示
  - lighting: 光线描述

  运镜方式说明

  - static: 固定镜头
  - pan_left: 向左平移
  - pan_right: 向右平移
  - tilt_up: 向上仰视
  - tilt_down: 向下俯视
  - zoom_in: 推进镜头
  - zoom_out: 拉开镜头
  - tracking: 跟随镜头
  - dolly: 推拉镜头

  镜头类型说明

  - extreme_wide: 极远景（大场景、环境）
  - wide: 远景（全貌）
  - medium_wide: 中远景
  - medium: 中景（半身）
  - medium_close: 中近景
  - close_up: 近景（面部特写）
  - extreme_close: 极特写（细节）

  输出格式（JSON）

  {{
    "storyboards": [
      {{
        "scene_number": 1,
        "title": "分镜标题",
        "description": "详细的画面描述，用于生成图像/视频",
        "dialogue": "台词内容",
        "camera_movement": "运镜方式",
        "shot_type": "镜头类型",
        "duration": 3.5,
        "composition_notes": "构图提示，如：三分法构图，主体位于左侧三分线",
        "lighting": "光线描述，如：侧逆光，营造戏剧效果",
        "color_palette": ["#hex1", "#hex2", "#hex3"]
      }}
    ]
  }}

  注意事项

  - 所有分镜的总时长应与原剧本场景时长接近
  - description 要足够详细，能够直接用于 AI 图像/视频生成
  - 运镜方式要自然流畅，避免过于复杂
  - 保持视觉风格的一致性

  #### 12.4 图像生成 Prompt (`app/prompts/image.txt`)

  你是一个专业的 AI 图像提示词专家。请将以下分镜描述转换为高质量的图像生成提示词。

  分镜信息

  - 分镜描述: {description}
  - 运镜方式: {camera_movement}
  - 镜头类型: {shot_type}
  - 视频风格: {visual_style}
  - 整体风格: {style}

  额外提示

  {color_hint}

  图像生成要求

  1. 创建一个静态帧，捕捉分镜的关键瞬间
  2. 图像应该是高质量、照片级的
  3. 充分体现指定的视频风格
  4. 包含分镜描述中的所有关键元素
  5. 考虑运镜方式，设置合适的构图

  运镜到静态帧的转换

  - static: 直接使用场景描述
  - pan/tilt: 选择平移或倾斜过程中的关键帧，通常是平移/倾斜结束时的画面
  - zoom_in: 选择拉近前的画面，展现场景全貌
  - zoom_out: 选择拉开前的特写画面
  - tracking/dolly: 选择运动过程中最有代表性的瞬间

  输出

  直接输出适合 DALL-E 或 Stable Diffusion 的提示词，格式为：
  A [shot_type] shot of [description]. [camera_movement] effect. [visual_style] style. [additional_details]

  示例：
  A medium shot of a futuristic cityscape at sunset, with holographic advertisements floating in the air. Pan left movement reveals more of the city. Cinematic style with neon color palette, high contrast, dramatic lighting.

  请根据上述要求生成提示词：

  ---

  ### 13. 测试示例

  #### 13.1 集成测试示例 (`tests/integration/test_full_pipeline.py`)

  ```python
  import pytest
  import asyncio
  from httpx import AsyncClient
  from app.main import app
  from app.database.session import init_db, close_db
  from app.entities.task import Task, TaskStatus
  from sqlalchemy.ext.asyncio import AsyncSession

  @pytest.fixture(scope="session")
  async def db():
      """数据库测试fixture"""
      await init_db()
      yield
      await close_db()

  @pytest.fixture
  async def client():
      """HTTP客户端测试fixture"""
      async with AsyncClient(app=app, base_url="http://test") as ac:
          yield ac

  @pytest.mark.asyncio
  async def test_full_pipeline(client):
      """测试完整的视频生成流程"""

      # 1. 创建任务
      create_response = await client.post(
          "/api/v1/tasks",
          json={
              "topic": "A futuristic cityscape with flying cars",
              "style": "futuristic",
              "options": {
                  "duration": 30,
                  "resolution": "1080p"
              }
          }
      )
      assert create_response.status_code == 200
      task_data = create_response.json()
      task_id = task_data["task_id"]

      # 2. 轮询任务状态
      max_attempts = 60  # 最多等待60次
      for i in range(max_attempts):
          status_response = await client.get(f"/api/v1/tasks/{task_id}")
          assert status_response.status_code == 200
          status_data = status_response.json()

          if status_data["status"] == TaskStatus.COMPLETED:
              break

          if status_data["status"] == TaskStatus.FAILED:
              pytest.fail(f"Task failed: {status_data.get('error_message')}")

          # 等待5秒后再检查
          await asyncio.sleep(5)
      else:
          pytest.fail("Task timeout")

      # 3. 验证输出
      final_status = await client.get(f"/api/v1/tasks/{task_id}")
      final_data = final_status.json()

      assert final_data["status"] == TaskStatus.COMPLETED
      assert final_data["output_video_url"] is not None
      assert final_data["progress"] == 1.0

      # 4. 检查视频元数据
      metadata_response = await client.get(f"/api/v1/tasks/{task_id}/video/metadata")
      assert metadata_response.status_code == 200
      metadata = metadata_response.json()

      assert metadata["duration"] > 0
      assert metadata["width"] == 1920
      assert metadata["height"] == 1080

  @pytest.mark.asyncio
  async def test_task_cancellation(client):
      """测试任务取消功能"""

      # 创建任务
      create_response = await client.post(
          "/api/v1/tasks",
          json={
              "topic": "A long documentary about space",
              "options": {"duration": 120}
          }
      )
      task_id = create_response.json()["task_id"]

      # 等待几秒
      await asyncio.sleep(3)

      # 取消任务
      cancel_response = await client.post(f"/api/v1/tasks/{task_id}/cancel")
      assert cancel_response.status_code == 200

      # 验证状态
      status_response = await client.get(f"/api/v1/tasks/{task_id}")
      assert status_response.json()["status"] == TaskStatus.CANCELLED

  @pytest.mark.asyncio
  async def test_style_detection(client):
      """测试风格识别"""

      response = await client.post(
          "/api/v1/tasks",
          json={
              "topic": "A documentary about wildlife in Africa",
              # 不指定风格，让系统自动识别
          }
      )
      task_id = response.json()["task_id"]

      # 等待风格识别完成
      await asyncio.sleep(10)

      # 检查任务状态，应该识别出 documentary 风格
      status_response = await client.get(f"/api/v1/tasks/{task_id}")
      status_data = status_response.json()

      assert status_data["status"] in [TaskStatus.STORY_GENERATION, TaskStatus.STORYBOARD_BREAKDOWN, TaskStatus.COMPLETED]
      # 通过后续步骤可以验证风格

  13.2 单元测试示例 (tests/agents/test_style_agent.py)

  import pytest
  from unittest.mock import Mock, AsyncMock
  from app.agents.style_agent import StyleAgent
  from app.core.context import AgentContext
  from app.entities.task import Task

  @pytest.fixture
  def mock_context():
      """模拟上下文"""
      context = Mock(spec=AgentContext)
      context.log = AsyncMock()
      context.set_shared_data = Mock()
      return context

  @pytest.fixture
  def sample_task():
      """示例任务"""
      return Task(
          id="123",
          user_id="user1",
          topic="A futuristic cityscape",
          style=None,  # 不指定风格，让系统识别
          options={}
      )

  @pytest.mark.asyncio
  async def test_style_agent_with_user_specified_style(mock_context, sample_task):
      """测试用户指定风格的情况"""
      sample_task.style = "futuristic"

      agent = StyleAgent(mock_context)

      # Mock LLM
      agent.llm.generate = AsyncMock(return_value='{"style": "futuristic"}')

      result = await agent.execute(sample_task)

      assert result["style"] == "futuristic"
      assert result["source"] == "user_specified"
      mock_context.log.assert_called_with("使用用户指定风格: futuristic")

  @pytest.mark.asyncio
  async def test_style_agent_llm_detection(mock_context, sample_task):
      """测试LLM风格识别"""
      agent = StyleAgent(mock_context)

      # Mock LLM 响应
      mock_response = '''{
          "style": "futuristic",
          "style_tags": ["sci-fi", "neon", "cyberpunk"],
          "visual_style": "Neon colors, holographic elements",
          "mood": "innovative",
          "color_palette": ["#00ffff", "#ff00ff", "#00ff00"],
          "reasoning": "Topic mentions futuristic cityscape"
      }'''

      agent.llm.generate = AsyncMock(return_value=mock_response)

      result = await agent.execute(sample_task)

      assert result["style"] == "futuristic"
      assert result["source"] == "llm_detected"
      assert "neon" in result["style_tags"]
      assert "#00ffff" in result["color_palette"]

      # 验证共享数据已设置
      mock_context.set_shared_data.assert_any_call("style", "futuristic")
      mock_context.set_shared_data.assert_any_call("style_tags", ["sci-fi", "neon", "cyberpunk"])

  @pytest.mark.asyncio
  async def test_style_agent_invalid_style_fallback(mock_context, sample_task):
      """测试无效风格的降级处理"""
      sample_task.style = "invalid_style"

      agent = StyleAgent(mock_context)
      agent.llm.generate = AsyncMock(return_value='{"style": "nonexistent"}')

      result = await agent.execute(sample_task)

      # 应该降级到默认风格
      assert result["style"] in StyleAgent.AVAILABLE_STYLES
      assert "source" in result

  ---
  14. Docker 部署配置

  14.1 Dockerfile

  # 多阶段构建 - 构建阶段
  FROM python:3.11-slim as builder

  WORKDIR /app

  # 安装构建依赖
  RUN apt-get update && apt-get install -y \
      gcc \
      g++ \
      libpq-dev \
      && rm -rf /var/lib/apt/lists/*

  # 复制依赖文件
  COPY requirements.txt .
  COPY requirements-dev.txt .

  # 安装 Python 依赖
  RUN pip install --no-cache-dir --upgrade pip && \
      pip install --no-cache-dir -r requirements.txt

  # 生产镜像
  FROM python:3.11-slim

  WORKDIR /app

  # 安装运行时依赖
  RUN apt-get update && apt-get install -y \
      ffmpeg \
      libpq5 \
      && rm -rf /var/lib/apt/lists/*

  # 从构建阶段复制虚拟环境
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin

  # 复制应用代码
  COPY app/ ./app/
  COPY pyproject.toml .

  # 创建存储目录
  RUN mkdir -p /app/storage /app/logs

  # 设置环境变量
  ENV PYTHONUNBUFFERED=1
  ENV PYTHONDONTWRITEBYTECODE=1

  # 暴露端口
  EXPOSE 8000

  # 健康检查
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
      CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

  # 启动命令
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

  14.2 Worker Dockerfile

  # 基础镜像与主应用相同
  FROM python:3.11-slim

  WORKDIR /app

  RUN apt-get update && apt-get install -y \
      ffmpeg \
      libpq5 \
      && rm -rf /var/lib/apt/lists/*

  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin

  COPY app/ ./app/
  COPY pyproject.toml .

  ENV PYTHONUNBUFFERED=1
  ENV PYTHONDONTWRITEBYTECODE=1

  # 启动 Celery Worker
  CMD ["celery", "-A", "app.scheduler.celery_app", "worker", "--loglevel=info", "--concurrency=4"]

  14.3 docker-compose.yml

  version: '3.8'

  services:
    # PostgreSQL 数据库
    db:
      image: postgres:15-alpine
      container_name: video_agent_db
      environment:
        POSTGRES_DB: video_agent
        POSTGRES_USER: videoagent
        POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      ports:
        - "5432:5432"
      volumes:
        - postgres_data:/var/lib/postgresql/data
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U videoagent"]
        interval: 10s
        timeout: 5s
        retries: 5

    # Redis
    redis:
      image: redis:7-alpine
      container_name: video_agent_redis
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data
      healthcheck:
        test: ["CMD", "redis-cli", "ping"]
        interval: 10s
        timeout: 5s
        retries: 5

    # FastAPI 应用
    api:
      build:
        context: .
        dockerfile: Dockerfile
      container_name: video_agent_api
      environment:
        - DATABASE_URL=postgresql+asyncpg://videoagent:${DB_PASSWORD:-changeme}@db:5432/video_agent
        - REDIS_URL=redis://redis:6379/0
        - CELERY_BROKER_URL=redis://redis:6379/0
        - CELERY_RESULT_BACKEND=redis://redis:6379/1
        - OPENAI_API_KEY=${OPENAI_API_KEY}
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
        - DEBUG=${DEBUG:-False}
      ports:
        - "8000:8000"
        - "9090:9090"  # Prometheus metrics
      volumes:
        - ./storage:/app/storage
        - ./logs:/app/logs
      depends_on:
        db:
          condition: service_healthy
        redis:
          condition: service_healthy
      restart: unless-stopped

    # Celery Worker
    worker:
      build:
        context: .
        dockerfile: Dockerfile
      container_name: video_agent_worker
      environment:
        - DATABASE_URL=postgresql+asyncpg://videoagent:${DB_PASSWORD:-changeme}@db:5432/video_agent
        - REDIS_URL=redis://redis:6379/0
        - CELERY_BROKER_URL=redis://redis:6379/0
        - CELERY_RESULT_BACKEND=redis://redis:6379/1
        - OPENAI_API_KEY=${OPENAI_API_KEY}
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      volumes:
        - ./storage:/app/storage
        - ./logs:/app/logs
      depends_on:
        db:
          condition: service_healthy
        redis:
          condition: service_healthy
      restart: unless-stopped
      command: celery -A app.scheduler.celery_app worker --loglevel=info --concurrency=4

    # Celery Beat (定时任务)
    beat:
      build:
        context: .
        dockerfile: Dockerfile
      container_name: video_agent_beat
      environment:
        - CELERY_BROKER_URL=redis://redis:6379/0
        - CELERY_RESULT_BACKEND=redis://redis:6379/1
      depends_on:
        - redis
      restart: unless-stopped
      command: celery -A app.scheduler.celery_app beat --loglevel=info

    # Prometheus (监控)
    prometheus:
      image: prom/prometheus:latest
      container_name: video_agent_prometheus
      ports:
        - "9091:9090"
      volumes:
        - ./prometheus.yml:/etc/prometheus/prometheus.yml
        - prometheus_data:/prometheus
      command:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
      restart: unless-stopped

    # Grafana (可视化)
    grafana:
      image: grafana/grafana:latest
      container_name: video_agent_grafana
      ports:
        - "3000:3000"
      environment:
        - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      volumes:
        - grafana_data:/var/lib/grafana
      depends_on:
        - prometheus
      restart: unless-stopped

  volumes:
    postgres_data:
    redis_data:
    prometheus_data:
    grafana_data:

  14.4 Prometheus 配置

  # prometheus.yml
  global:
    scrape_interval: 15s
    evaluation_interval: 15s

  scrape_configs:
    - job_name: 'video_agent_api'
      static_configs:
        - targets: ['api:9090']
      metrics_path: '/metrics'

    - job_name: 'prometheus'
      static_configs:
        - targets: ['localhost:9090']

  ---
  15. 部署指南

  15.1 本地开发环境

  # 1. 克隆仓库
  git clone https://github.com/your-org/video-agent.git
  cd video-agent

  # 2. 创建虚拟环境
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate

  # 3. 安装依赖
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

  # 4. 配置环境变量
  cp .env.example .env
  # 编辑 .env 文件，填入必要的配置

  # 5. 初始化数据库
  python scripts/init_db.py

  # 6. 启动 Redis (使用 Docker)
  docker run -d -p 6379:6379 redis:7-alpine

  # 7. 启动 PostgreSQL (使用 Docker)
  docker run -d \
    -p 5432:5432 \
    -e POSTGRES_DB=video_agent \
    -e POSTGRES_USER=videoagent \
    -e POSTGRES_PASSWORD=changeme \
    postgres:15-alpine

  # 8. 运行数据库迁移
  alembic upgrade head

  # 9. 启动 API 服务
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  # 10. 新开终端，启动 Celery Worker
  celery -A app.scheduler.celery_app worker --loglevel=info

  # 11. 新开终端，启动 Celery Beat (可选)
  celery -A app.scheduler.celery_app beat --loglevel=info

  15.2 Docker 部署

  # 1. 构建镜像
  docker-compose build

  # 2. 启动所有服务
  docker-compose up -d

  # 3. 查看日志
  docker-compose logs -f api
  docker-compose logs -f worker

  # 4. 停止服务
  docker-compose down

  # 5. 清理数据（谨慎使用）
  docker-compose down -v

  15.3 Kubernetes 部署

  # k8s/deployment.yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: video-agent-api
  spec:
    replicas: 3
    selector:
      matchLabels:
        app: video-agent-api
    template:
      metadata:
        labels:
          app: video-agent-api
      spec:
        containers:
        - name: api
          image: video-agent:latest
          ports:
          - containerPort: 8000
          env:
          - name: DATABASE_URL
            valueFrom:
              secretKeyRef:
                name: video-agent-secrets
                key: database-url
          - name: OPENAI_API_KEY
            valueFrom:
              secretKeyRef:
                name: video-agent-secrets
                key: openai-api-key
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5

  ---
  apiVersion: v1
  kind: Service
  metadata:
    name: video-agent-api
  spec:
    selector:
      app: video-agent-api
    ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
    type: LoadBalancer

  ---
  16. 环境变量示例

  # .env.example

  # 应用配置
  APP_NAME=Video Agent API
  APP_VERSION=1.0.0
  DEBUG=False
  ENV=production

  # 数据库配置
  DATABASE_URL=postgresql+asyncpg://videoagent:changeme@localhost:5432/video_agent
  DB_POOL_SIZE=20
  DB_MAX_OVERFLOW=10

  # Redis 配置
  REDIS_URL=redis://localhost:6379/0

  # Celery 配置
  CELERY_BROKER_URL=redis://localhost:6379/0
  CELERY_RESULT_BACKEND=redis://localhost:6379/1
  CELERY_TASK_SOFT_TIME_LIMIT=600
  CELERY_TASK_TIME_LIMIT=660

  # 模型 API 配置
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  RUNWAY_API_KEY=your-runway-key
  STABILITY_API_KEY=your-stability-key

  # 模型配置
  DEFAULT_LLM_MODEL=gpt-4
  DEFAULT_IMAGE_MODEL=dall-e-3
  DEFAULT_VIDEO_MODEL=runway-gen3

  # 存储配置
  STORAGE_PROVIDER=local
  LOCAL_STORAGE_PATH=./storage

  # OSS 配置 (如果使用 OSS)
  OSS_ACCESS_KEY_ID=your-access-key-id
  OSS_ACCESS_KEY_SECRET=your-access-key-secret
  OSS_BUCKET=your-bucket-name
  OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com

  # 任务配置
  MAX_RETRY_TIMES=3
  TASK_TIMEOUT=1800
  MAX_CONCURRENT_TASKS_PER_USER=5
  MAX_CONCURRENT_GENERATIONS=5

  # 成本控制
  DEFAULT_DAILY_BUDGET=50.0

  # Webhook 配置
  WEBHOOK_TIMEOUT=10
  WEBHOOK_MAX_RETRIES=3

  # 日志配置
  LOG_LEVEL=INFO
  LOG_FILE=./logs/app.log
  LOG_ROTATION=10 MB
  LOG_RETENTION=30 days

  # 监控配置
  PROMETHEUS_ENABLED=True
  PROMETHEUS_PORT=9090

  # 安全配置
  SECRET_KEY=your-secret-key-change-this-in-production
  JWT_SECRET_KEY=your-jwt-secret-key
  JWT_ALGORITHM=HS256
  JWT_EXPIRATION_HOURS=24

  ---
  总结

  这份完整的架构设计文档涵盖了：

  1. 系统架构设计：分层架构图、模块划分
  2. 技术选型：每个组件的选择理由
  3. 项目结构：清晰的目录组织
  4. 数据模型：核心实体设计
  5. API 设计：RESTful 接口规范
  6. Agent 调度：完整的编排流程
  7. 状态机：任务生命周期管理
  8. MVP 计划：16 周详细拆解
  9. 风险与优化：全面的风险分析和解决方案
  10. 实现示例：核心代码、Prompt 模板、测试、部署配置

  该设计可以直接用于开发生产级的 Video Agent 系统，具备良好的可扩展性、可维护性和可靠性。