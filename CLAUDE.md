# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Project Overview

Video Agent - A production-grade AI video generation system that takes a text topic and automatically produces a complete video through multi-Agent orchestration.

## Project Status

The project is in the design phase. `document.md` contains the complete architecture design document (318KB) with detailed specifications for system architecture, technology choices, module structure, data models, API design, and a 16-week MVP development plan.

## Key Architecture Decisions

**Technology Stack:**
- **Web Framework**: FastAPI (async, type-safe, auto-generated docs)
- **Task Scheduling**: Celery + Redis (async tasks, retries, priority queues)
- **Database**: PostgreSQL + SQLAlchemy 2.0 async ORM
- **Video Processing**: FFmpeg
- **Language**: Python 3.11+

**Agent Architecture:**
The system uses a 6-Agent pipeline:
1. **Style Agent** - Style detection/selection
2. **Story Agent** - Script generation
3. **Storyboard Agent** - Scene breakdown
4. **Image Agent** - First frame generation (concurrent)
5. **Video Agent** - Video clip generation (concurrent)
6. **Composer Agent** - Video concatenation with FFmpeg

**Data Flow:**
```
User Request → API → Task Queue → Agent Orchestrator → Model Abstraction Layer → External APIs (OpenAI, Runway, etc.)
                                                                      ↓
                            Storage Service (OSS/S3/MinIO) → Final Video Output
```

## Directory Structure (Planned)

```
video_agent/
├── app/
│   ├── api/              # FastAPI routes and schemas
│   ├── agents/           # Agent implementations
│   ├── core/             # Task manager, state machine, context
│   ├── models/           # Model abstraction (LLM, Image, Video)
│   ├── scheduler/        # Celery tasks
│   ├── services/         # Storage, cache, video processing
│   ├── database/         # DB session, migrations
│   ├── entities/         # ORM models (Task, Script, Storyboard, Resource)
│   ├── prompts/          # Prompt templates for LLM
│   └── utils/           # Logging, validators, retry decorators
├── tests/
├── scripts/
└── docs/
```

## Core Concepts

**Task State Machine:**
Tasks flow through states: PENDING → STYLE_DETECTION → STORY_GENERATION → STORYBOARD_BREAKDOWN → IMAGE_GENERATION → VIDEO_GENERATION → COMPOSING → COMPLETED

Any state can transition to FAILED or CANCELLED. FAILED can transition to RETRYING and back to any retryable state.

**Agent Context:**
`AgentContext` manages shared data across Agents, database operations, caching, and event publishing. It's passed to each Agent during execution.

**Model Abstraction:**
All model providers (OpenAI, Claude, DeepSeek, Runway, etc.) implement abstract base classes. This enables:
- Multi-vendor fallback strategies
- Easy addition of new providers
- Centralized configuration and routing

## Important Files (Once Created)

- `app/config.py` - Pydantic Settings for all configuration
- `app/core/task_manager.py` - Orchestrates Agent pipeline execution
- `app/core/state_machine.py` - Validates and manages task state transitions
- `app/core/context.py` - AgentContext for cross-Agent data sharing
- `app/agents/base.py` - BaseAgent class all agents inherit from
- `app/scheduler/celery_app.py` - Celery configuration and task definitions
- `app/services/video_processor.py` - FFmpeg wrapper for video composition

## Development Guidelines

**Adding a New Agent:**
1. Inherit from `BaseAgent` in `app/agents/base.py`
2. Implement `execute(self, task: Task) -> Dict[str, Any]` method
3. Register in `TaskManager.agents` dictionary
4. Add to the pipeline in `TaskManager.run_pipeline()`
5. Create corresponding status in `TaskStatus` enum

**Adding a New Model Provider:**
1. Create abstract base class in `app/models/{type}/base.py` if it doesn't exist
2. Implement the provider in `app/models/{type}/{provider}.py`
3. Register in `ModelManager` or configuration

**State Transitions:**
Always use `TaskStateMachine.validate_transition()` before updating task status. Never directly modify `Task.status`.

**Concurrency:**
- ImageAgent and VideoAgent process storyboards concurrently
- Use `asyncio.Semaphore` to limit concurrent API calls
- Configure `MAX_CONCURRENT_GENERATIONS` in settings

## Environment Setup (Planned)

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
alembic upgrade head

# Start services
docker-compose up -d  # PostgreSQL, Redis
uvicorn app.main:app --reload  # API server
celery -A app.scheduler.celery_app worker --loglevel=info  # Worker
```

## Testing Strategy

- **Unit tests**: Test individual Agents, models, and utilities
- **Integration tests**: Test complete pipeline execution
- Tests use `pytest` with `pytest-asyncio` for async support
- Mock external API calls in tests using `unittest.mock`

## Performance Considerations

- All model API calls should have timeouts and retry logic
- Use Redis caching for expensive operations (e.g., repeated prompts)
- Limit concurrent generations to avoid rate limits
- Clean up temporary resources after task completion

## References

- `document.md` - Complete architecture specification (read for detailed design)
- MVP follows 16-week development plan outlined in the document
