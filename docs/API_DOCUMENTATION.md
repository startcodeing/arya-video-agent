# API Documentation

## 概述

本文档提供Arya Video Agent系统的完整API文档，包括所有端点的请求/响应示例、错误码说明、速率限制和最佳实践。

## 版本信息

- **API版本**: v1.0.0
- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 认证

### 获取认证Token

**端点**: `POST /auth/token`

**请求示例**:
```json
{
  "username": "user@example.com",
  "password": "secure_password_123"
}
```

**响应示例** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MjU0ODU0MjIsInN1YiI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNTE4NTkzNDAsImlzcyI6InN1YiIsImp1YiI6InN1YiIsInVzZXIiOiJ1c2VyQG9hcGkuY29tIn0.k1f1Hk7V9f1Hk7V9f1Hk7V9f1Hk7V9f1Hk7V9f1Hk7V9f1Hk7V9",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "email": "user@example.com"
  }
}
```

**使用Token**:
在请求头中添加：
```
Authorization: Bearer {access_token}
```

## 任务管理

### 1. 创建任务

**端点**: `POST /tasks`

**认证**: 需要

**请求头**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**请求示例**:
```json
{
  "topic": "Create a promotional video for a new coffee brand",
  "style": "modern, minimalist, warm tones",
  "options": {
    "duration": 60,
    "resolution": "1080p",
    "format": "mp4"
  }
}
```

**响应示例** (201 Created):
```json
{
  "id": "task_123",
  "user_id": "user_123",
  "topic": "Create a promotional video for a new coffee brand",
  "style": "modern, minimalist, warm tones",
  "options": {
    "duration": 60,
    "resolution": "1080p",
    "format": "mp4"
  },
  "status": "pending",
  "priority": "normal",
  "progress": 0.0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**错误响应** (400 Bad Request):
```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": {
    "topic": "Topic is required and must be at least 10 characters",
    "options.duration": "Duration must be between 15 and 600 seconds"
  }
}
```

### 2. 获取任务列表

**端点**: `GET /tasks`

**认证**: 需要

**查询参数**:
- `user_id` (string, 可选): 用户ID
- `status` (string, 可选): 任务状态（pending, processing, completed, failed）
- `priority` (string, 可选): 任务优先级（low, normal, high, urgent）
- `limit` (integer, 可选): 每页返回的任务数（默认：20）
- `offset` (integer, 可选): 跳过的任务数（默认：0）
- `sort_by` (string, 可选): 排序字段（created_at, updated_at, priority, status）
- `order` (string, 可选): 排序方向（asc, desc，默认：desc）

**请求示例**:
```
GET /tasks?user_id=user_123&status=pending&priority=high&limit=10&offset=0&sort_by=created_at&order=desc
```

**响应示例** (200 OK):
```json
{
  "tasks": [
    {
      "id": "task_123",
      "user_id": "user_123",
      "topic": "Create a promotional video",
      "style": "modern, minimalist, warm tones",
      "status": "pending",
      "priority": "high",
      "progress": 0.0,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 10,
    "total_pages": 5
  }
}
```

### 3. 获取任务详情

**端点**: `GET /tasks/{task_id}`

**认证**: 需要

**路径参数**:
- `task_id` (string, 必需): 任务ID

**请求示例**:
```
GET /tasks/task_123
```

**响应示例** (200 OK):
```json
{
  "id": "task_123",
  "user_id": "user_123",
  "topic": "Create a promotional video for a new coffee brand",
  "style": "modern, minimalist, warm tones",
  "options": {
    "duration": 60,
    "resolution": "1080p",
    "format": "mp4"
  },
  "status": "completed",
  "priority": "high",
  "progress": 1.0,
  "current_agent": "composer_agent",
  "error_message": null,
  "error_code": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "completed_at": "2024-01-15T11:45:00Z",
  "output": {
    "video_url": "https://storage.example.com/videos/task_123.mp4",
    "thumbnail_url": "https://storage.example.com/thumbnails/task_123.jpg",
    "metadata": {
      "duration": 60,
      "resolution": "1920x1080",
      "size": "125MB"
    }
  }
}
```

**错误响应** (404 Not Found):
```json
{
  "error": "Not Found",
  "message": "Task not found",
  "details": {
    "task_id": "task_123"
  }
}
```

### 4. 更新任务

**端点**: `PATCH /tasks/{task_id}`

**认证**: 需要

**路径参数**:
- `task_id` (string, 必需): 任务ID

**请求体**（部分更新）:
```json
{
  "status": "processing",
  "progress": 0.5,
  "current_agent": "style_agent"
}
```

**完整请求体示例**:
```json
{
  "topic": "Updated topic for the video",
  "style": "modern, minimalist",
  "options": {
    "duration": 90,
    "resolution": "4K",
    "format": "mp4"
  },
  "status": "processing",
  "progress": 0.5,
  "current_agent": "style_agent",
  "error_message": null,
  "error_code": null
}
```

**响应示例** (200 OK):
```json
{
  "id": "task_123",
  "user_id": "user_123",
  "topic": "Updated topic for the video",
  "style": "modern, minimalist",
  "options": {
    "duration": 90,
    "resolution": "4K",
    "format": "mp4"
  },
  "status": "processing",
  "progress": 0.5,
  "current_agent": "style_agent",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### 5. 删除任务

**端点**: `DELETE /tasks/{task_id}`

**认证**: 需要

**路径参数**:
- `task_id` (string, 必需): 任务ID

**请求示例**:
```
DELETE /tasks/task_123
```

**响应示例** (200 OK):
```json
{
  "success": true,
  "message": "Task deleted successfully",
  "task_id": "task_123"
}
```

---

## 对话管理

### 1. 创建对话

**端点**: `POST /conversations`

**认证**: 需要

**请求示例**:
```json
{
  "user_id": "user_123",
  "session_id": "session_456",
  "task_id": "task_123",
  "title": "Coffee Brand Video Creation"
}
```

**响应示例** (201 Created):
```json
{
  "id": "conv_789",
  "user_id": "user_123",
  "session_id": "session_456",
  "task_id": "task_123",
  "title": "Coffee Brand Video Creation",
  "status": "active",
  "message_count": 0,
  "messages": [],
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "expires_at": "2024-01-22T10:35:00Z"
}
```

### 2. 获取对话列表

**端点**: `GET /conversations`

**认证**: 需要

**查询参数**:
- `user_id` (string, 必需): 用户ID
- `status` (string, 可选): 对话状态（active, archived, expired）
- `active_only` (boolean, 可选): 仅返回活跃对话（默认：true）
- `limit` (integer, 可选): 每页返回的对话数（默认：20）
- `offset` (integer, 可选): 跳过的对话数（默认：0）
- `include_messages` (boolean, 可选): 是否包含消息内容（默认：false）

**请求示例**:
```
GET /conversations?user_id=user_123&status=active&active_only=true&limit=10&offset=0&include_messages=false
```

**响应示例** (200 OK):
```json
{
  "conversations": [
    {
      "id": "conv_789",
      "user_id": "user_123",
      "session_id": "session_456",
      "task_id": "task_123",
      "title": "Coffee Brand Video Creation",
      "status": "active",
      "message_count": 5,
      "created_at": "2024-01-15T10:35:00Z",
      "updated_at": "2024-01-15T12:30:00Z",
      "expires_at": "2024-01-22T10:35:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 10,
    "total_pages": 3
  }
}
```

### 3. 获取对话详情（包含消息）

**端点**: `GET /conversations/{conversation_id}?include_messages=true`

**认证**: 需要

**路径参数**:
- `conversation_id` (string, 必需): 对话ID

**查询参数**:
- `include_messages` (boolean, 可选): 是否包含消息内容（默认：true）
- `message_limit` (integer, 可选): 返回的最大消息数（默认：50）

**请求示例**:
```
GET /conversations/conv_789?include_messages=true&message_limit=20
```

**响应示例** (200 OK):
```json
{
  "id": "conv_789",
  "user_id": "user_123",
  "session_id": "session_456",
  "task_id": "task_123",
  "title": "Coffee Brand Video Creation",
  "status": "active",
  "message_count": 5,
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T12:30:00Z",
  "expires_at": "2024-01-22T10:35:00Z",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "I want to create a promotional video for my coffee brand",
      "timestamp": "2024-01-15T10:35:15Z",
      "metadata": {}
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Sure! What style would you like for the video?",
      "timestamp": "2024-01-15T10:35:30Z",
      "metadata": {
        "agent": "style_agent",
        "model": "gpt-4"
      }
    }
  ]
}
```

### 4. 发送消息

**端点**: `POST /conversations/{conversation_id}/messages`

**认证**: 需要

**路径参数**:
- `conversation_id` (string, 必需): 对话ID

**请求示例**:
```json
{
  "role": "user",
  "content": "I'd like a modern, minimalist style with warm tones",
  "metadata": {
    "source": "chat_interface"
  }
}
```

**响应示例** (201 Created):
```json
{
  "id": "msg_006",
  "conversation_id": "conv_789",
  "role": "user",
  "content": "I'd like a modern, minimalist style with warm tones",
  "timestamp": "2024-01-15T12:35:00Z",
  "metadata": {
    "source": "chat_interface"
  }
}
```

---

## 错误码说明

| 错误码 | HTTP状态码 | 描述 | 解决方法 |
|--------|-----------|------|----------|
| `INVALID_TOKEN` | 401 | 无效的认证Token | 重新登录获取新Token |
| `EXPIRED_TOKEN` | 401 | 认证Token已过期 | 重新登录获取新Token |
| `MISSING_FIELDS` | 400 | 缺少必填字段 | 检查请求体，添加所有必填字段 |
| `INVALID_FIELD_TYPE` | 400 | 字段类型不正确 | 检查字段类型，确保符合API规范 |
| `FIELD_TOO_SHORT` | 400 | 字段长度不足 | 增加字段长度至最小要求 |
| `FIELD_TOO_LONG` | 400 | 字段长度过长 | 减少字段长度至最大限制 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 | 检查任务ID是否正确 |
| `CONVERSATION_NOT_FOUND` | 404 | 对话不存在 | 检查对话ID是否正确 |
| `UNAUTHORIZED` | 403 | 未授权访问 | 确认已提供有效的认证Token |
| `FORBIDDEN` | 403 | 禁止访问 | 确认用户有权限访问该资源 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 | 减少请求频率，等待后重试 |
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 | 稍后重试，如问题持续请联系技术支持 |
| `BAD_GATEWAY` | 502 | 网关错误 | 稍后重试，检查上游服务状态 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 | 稍后重试，检查依赖服务状态 |

---

## 速率限制

### 全局速率限制
- **请求频率**: 每15秒最多60个请求（240 req/min）
- **每个Token**: 每15秒最多120个请求（480 req/min）

### 端点级别限制
| 端点 | 限制 | 时间窗口 |
|------|------|---------|
| `POST /tasks` | 10 requests | 60秒 |
| `GET /tasks` | 100 requests | 60秒 |
| `GET /tasks/{task_id}` | 200 requests | 60秒 |
| `PATCH /tasks/{task_id}` | 50 requests | 60秒 |
| `DELETE /tasks/{task_id}` | 10 requests | 60秒 |
| `POST /conversations` | 20 requests | 60秒 |
| `GET /conversations` | 200 requests | 60秒 |
| `POST /conversations/{id}/messages` | 50 requests | 60秒 |

### 速率限制响应头
当请求受速率限制影响时，响应会包含以下头信息：
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704107200
```

**错误响应** (429 Too Many Requests):
```json
{
  "error": "Rate Limit Exceeded",
  "message": "You have exceeded the rate limit. Please wait before making another request.",
  "details": {
    "limit": 60,
    "remaining": 0,
    "reset": "1704107200"
  }
}
```

---

## 版本控制

### API版本策略
- **URL版本控制**: 使用`/api/v1`前缀
- **向后兼容**: 新版本保持向后兼容
- **弃用通知**: 在弃用端点前3个月发送弃用通知
- **移除周期**: 弃用后6个月移除

### 未来版本计划
- **v2.0**: 计划2024年Q3
  - 批量操作API
  - WebSocket实时更新
  - 高级筛选和搜索
  - 增强的速率限制控制

---

## 最佳实践

### 1. 认证
- 始终使用HTTPS
- 安全存储认证Token
- 定期刷新Token（过期前5分钟）
- 使用最小权限原则

### 2. 错误处理
- 实现适当的错误处理和重试逻辑
- 使用指数退避策略进行重试
- 记录错误日志以便调试
- 提供有意义的错误信息给用户

### 3. 分页
- 使用`limit`和`offset`参数进行分页
- 缓存分页结果以减少数据库负载
- 实现“加载更多”模式以提高用户体验
- 设置合理的`limit`值（建议：20-100）

### 4. 速率限制
- 遵守速率限制要求
- 实现退避策略（exponential backoff）
- 监控请求计数器（`X-RateLimit-Remaining`）
- 实现客户端请求队列以平滑请求流

### 5. 缓存
- 使用`If-Modified-Since`和`ETag`头进行条件请求
- 缓存频繁访问但不经常变化的数据
- 设置适当的缓存TTL
- 使用`Cache-Control`头控制缓存行为

### 6. 过滤和搜索
- 使用标准查询参数（`sort_by`、`order`、`filter`）
- 支持多种搜索方式（精确搜索、模糊搜索、分面搜索）
- 实现搜索结果排序和分页
- 提供搜索结果计数

---

## 测试工具

### 使用cURL测试API
```bash
# 创建任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "topic": "Create a promotional video",
    "style": "modern, minimalist"
  }'

# 获取任务列表
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取任务详情
curl -X GET http://localhost:8000/api/v1/tasks/task_123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 使用Postman测试API
1. 导入API集合到Postman
2. 在Postman中配置认证Token
3. 使用Postman的环境变量管理不同的环境
4. 使用Postman的测试集合运行多个测试用例

---

## 常见问题

### Q: 如何获取认证Token？
A: 发送POST请求到`/auth/token`端点，包含用户名和密码。响应中的`access_token`就是认证Token。

### Q: Token过期了怎么办？
A: Token有效期通常为1小时。过期后需要重新登录获取新Token。

### Q: 如何处理速率限制？
A: 遵循速率限制要求，实现退避策略，监控`X-RateLimit-Remaining`头信息。

### Q: 如何处理错误？
A: 检查HTTP状态码和错误响应体中的错误码和错误信息，根据错误码采取相应的处理措施。

### Q: 如何提高API性能？
A: 使用缓存（Redis）、优化数据库查询、使用分页、批量操作、连接池管理等。

---

## 技术支持

如有任何问题或建议，请联系：
- **Email**: support@arya-video-agent.com
- **GitHub Issues**: https://github.com/startcodeing/arya-video-agent/issues
- **Discord社区**: https://discord.gg/arya-video-agent

---

**文档版本**: v1.0.0
**最后更新**: 2024-01-15
**维护者**: Arya Video Agent Team
