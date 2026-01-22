# Video Agent - AI Video Generation System

A production-grade AI video generation system that takes a text topic and automatically produces a complete video through multi-Agent orchestration.

## Project Overview

This system implements a 6-Agent pipeline:
1. **Style Agent** - Style detection/selection
2. **Story Agent** - Script generation
3. **Storyboard Agent** - Scene breakdown
4. **Image Agent** - First frame generation (concurrent)
5. **Video Agent** - Video clip generation (concurrent)
6. **Composer Agent** - Video concatenation with FFmpeg

## Technology Stack

- **Web Framework**: FastAPI (async, type-safe, auto-generated docs)
- **Task Scheduling**: Celery + Redis (async tasks, retries, priority queues)
- **Database**: PostgreSQL + SQLAlchemy 2.0 async ORM
- **Video Processing**: FFmpeg
- **Language**: Python 3.11+

## Current Status

### Week 1 - Completed ✅

Project initialization and basic infrastructure setup is complete:

- ✅ Project directory structure created
- ✅ FastAPI application framework configured
- ✅ PostgreSQL database connection configured (asyncpg)
- ✅ Database entity models created (Task, Script, Storyboard, Resource)
- ✅ Alembic database migration configured
- ✅ Redis connection configured
- ✅ Celery basic settings configured
- ✅ Health check endpoints implemented
- ✅ Logging system implemented
- ✅ Helper scripts created
- ✅ Comprehensive unit tests written
- ✅ Development documentation created
- ✅ Project verification script created

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- FFmpeg

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd VideoAgent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start services using Docker**
   ```bash
   docker-compose up -d
   ```

   Or manually start PostgreSQL and Redis:
   ```bash
   # PostgreSQL
   docker run -d -p 5432:5432 \
     -e POSTGRES_DB=video_agent \
     -e POSTGRES_USER=videoagent \
     -e POSTGRES_PASSWORD=changeme \
     postgres:15-alpine

   # Redis
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the API server**
   ```bash
   # Using the start script
   python scripts/start_api.py

   # Or using uvicorn directly
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Start Celery worker** (in a new terminal)
   ```bash
   # Using the start script
   python scripts/start_worker.py

   # Or using celery directly
   celery -A app.scheduler.celery_app worker --loglevel=info
   ```

### Using Helper Scripts

The project includes several helper scripts in the `scripts/` directory:

- `scripts/verify_setup.py` - Verify project setup and dependencies
- `scripts/start_api.py` - Start the API server
- `scripts/start_worker.py` - Start the Celery worker
- `scripts/init_db.py` - Initialize the database
- `scripts/run_tests.py` - Run all tests

## Verification & Testing

### Quick Verification

Before running the application, verify your setup:

```bash
# Run verification script
python scripts/verify_setup.py

# This will check:
# - All module imports
# - Configuration settings
# - Database entities
# - Celery configuration
# - API routes
# - Database connection (requires services running)
# - Redis connection (requires services running)
```

### Running Tests

```bash
# Run all tests
python scripts/run_tests.py
# Or
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

### Available Tests

- `tests/test_health.py` - Health check endpoint tests
- `tests/test_entities.py` - Database entity tests
- `tests/test_config.py` - Configuration tests
- `tests/test_logger.py` - Logging system tests
- `tests/test_cache.py` - Cache service tests
- `tests/test_celery.py` - Celery configuration tests
- `tests/test_database.py` - Database session tests

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Health Check Endpoints

- `GET /` - Root endpoint
- `GET /health` - Basic health check
- `GET /api/v1/health` - Health check (API v1)
- `GET /api/v1/health/detailed` - Detailed health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

## Project Structure

```
video_agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── api/                    # API layer
│   │   ├── routes/             # API endpoints
│   │   │   └── health.py       # Health check endpoints
│   │   └── ...
│   ├── core/                   # Core business layer
│   ├── agents/                 # Agent implementations
│   ├── models/                 # Model abstraction layer
│   ├── scheduler/              # Celery tasks
│   │   ├── celery_app.py       # Celery configuration
│   │   └── tasks.py            # Task definitions
│   ├── services/               # Services
│   │   └── cache.py            # Redis cache service
│   ├── database/               # Database layer
│   │   ├── base.py             # Base classes
│   │   ├── session.py          # DB session management
│   │   └── migrations/         # Alembic migrations
│   ├── entities/               # ORM models
│   │   ├── task.py             # Task entity
│   │   ├── script.py           # Script entity
│   │   ├── storyboard.py       # Storyboard entity
│   │   └── resource.py         # Resource entity
│   ├── prompts/                # Prompt templates
│   └── utils/                  # Utilities
│       └── logger.py           # Logging configuration
├── tests/                      # Tests
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
├── storage/                    # Local file storage
├── logs/                       # Application logs
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project configuration
├── alembic.ini                 # Alembic configuration
└── README.md                   # This file
```

## Development Plan

The project follows a 16-week MVP development plan:

- **Week 1-3**: Basic infrastructure (current)
- **Week 4-8**: Core Agent development
- **Week 9-11**: System integration
- **Week 12-13**: Performance optimization
- **Week 14-16**: Deployment and production

See `document.md` for detailed architecture and development plan.

## Next Steps (Week 2)

The following features will be implemented in Week 2:

1. Implement BaseAgent abstract class
2. Implement model abstraction base classes (LLM, Image, Video)
3. Implement OpenAI LLM Provider
4. Implement OpenAI Image Provider (DALL-E)
5. Implement Runway Video Provider (or Mock)
6. Implement model routing logic
7. Implement Agent context management (AgentContext)
8. Write model call unit tests
9. Add API key management mechanism

## License

MIT License

## Contributing

Contributions are welcome! Please read the development guidelines in `CLAUDE.md`.
