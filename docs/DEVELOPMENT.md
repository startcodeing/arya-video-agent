# Development Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- FFmpeg (for video processing)

## Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set these variables:
# - OPENAI_API_KEY
# - SECRET_KEY
# - JWT_SECRET_KEY
```

### 3. Start Services

#### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Check services are running
docker-compose ps
```

#### Option B: Manual Setup

```bash
# Start PostgreSQL
docker run -d \
  --name video_agent_db \
  -e POSTGRES_DB=video_agent \
  -e POSTGRES_USER=videoagent \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name video_agent_redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 4. Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Or use the init script
python scripts/init_db.py
```

### 5. Start the Application

```bash
# Start API server
python scripts/start_api.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Celery Worker (in another terminal)

```bash
python scripts/start_worker.py

# Or use celery directly
celery -A app.scheduler.celery_app worker --loglevel=info --concurrency=4
```

## Running Tests

### Run All Tests

```bash
# Using the test script
python scripts/run_tests.py

# Or using pytest directly
pytest

# With coverage
pytest --cov=app --cov-report=html

# With verbose output
pytest -v
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/test_health.py

# Run specific test function
pytest tests/test_config.py::test_default_settings

# Run tests by keyword
pytest -k "test_cache"
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
# Open htmlcov/index.html in browser
```

## Development Workflow

### 1. Make Code Changes

Edit files in the `app/` directory.

### 2. Run Tests

```bash
pytest
```

### 3. Check Code Style

```bash
# Format code with black
black app/ tests/

# Check with flake8
flake8 app/ tests/

# Sort imports with isort
isort app/ tests/

# Type check with mypy
mypy app/
```

### 4. Run Application

```bash
# API server
python scripts/start_api.py

# Celery worker
python scripts/start_worker.py
```

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Health Check Endpoints

- `GET /` - Root endpoint
- `GET /health` - Simple health check
- `GET /api/v1/health` - Health check (API v1)
- `GET /api/v1/health/detailed` - Detailed health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

## Database Migrations

### Create a New Migration

```bash
# Auto-generate migration
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>
```

### View Migration History

```bash
alembic history
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs video_agent_db

# Connect to database
docker exec -it video_agent_db psql -U videoagent -d video_agent
```

### Redis Connection Issues

```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
docker exec -it video_agent_redis redis-cli ping
```

### Port Already in Use

```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Kill process
# Windows:
taskkill /PID <PID> /F
# Linux/Mac:
kill -9 <PID>
```

### Import Errors

```bash
# Ensure you're in the virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Project Structure

```
video_agent/
├── app/                      # Application code
│   ├── api/                  # API endpoints
│   ├── core/                 # Core business logic
│   ├── agents/               # Agent implementations
│   ├── models/               # Model abstraction layer
│   ├── scheduler/            # Celery tasks
│   ├── services/             # Services (cache, storage, etc.)
│   ├── database/             # Database configuration
│   ├── entities/             # ORM models
│   ├── prompts/              # Prompt templates
│   └── utils/                # Utilities
├── tests/                    # Test code
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── storage/                  # Local file storage
└── logs/                     # Application logs
```

## Code Quality Standards

### Python Version

- Use Python 3.11+ type hints
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions and classes

### Testing

- Write unit tests for all new code
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external dependencies

### Commits

- Write clear commit messages
- Use conventional commit format
- Reference issues in commits

## Getting Help

- Check the documentation in `docs/`
- Review the architecture in `document.md`
- Check test examples in `tests/`
- Review CLAUDE.md for AI-assisted development guidelines
