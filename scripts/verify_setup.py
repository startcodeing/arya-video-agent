"""Script to verify project setup and basic functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.config import settings
from app.utils.logger import setup_logger, get_logger


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_success(message):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"✗ {message}")


def print_info(message):
    """Print info message."""
    print(f"  {message}")


async def verify_imports():
    """Verify that all modules can be imported."""
    print_section("Verifying Imports")

    modules = [
        "app.config",
        "app.main",
        "app.database.session",
        "app.database.base",
        "app.entities.task",
        "app.entities.script",
        "app.entities.storyboard",
        "app.entities.resource",
        "app.services.cache",
        "app.scheduler.celery_app",
        "app.scheduler.tasks",
        "app.api.routes.health",
        "app.utils.logger",
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print_success(f"Imported: {module}")
        except Exception as e:
            print_error(f"Failed to import {module}: {e}")
            failed.append((module, str(e)))

    return len(failed) == 0


def verify_config():
    """Verify configuration."""
    print_section("Verifying Configuration")

    # Check required settings
    required = [
        ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
        ("SECRET_KEY", settings.SECRET_KEY),
        ("JWT_SECRET_KEY", settings.JWT_SECRET_KEY),
    ]

    all_ok = True
    for name, value in required:
        if value and value != "":
            if name == "OPENAI_API_KEY" and not value.startswith("sk-"):
                print_info(f"{name}: Set (but may not be a valid key)")
            else:
                print_success(f"{name}: Set")
        else:
            print_error(f"{name}: Not set")
            all_ok = False

    # Check optional settings
    print_info(f"App Name: {settings.APP_NAME}")
    print_info(f"Environment: {settings.ENV}")
    print_info(f"Debug: {settings.DEBUG}")
    print_info(f"Database: {settings.DATABASE_URL[:30]}...")
    print_info(f"Redis: {settings.REDIS_URL}")
    print_info(f"Log Level: {settings.LOG_LEVEL}")

    return all_ok


async def verify_database():
    """Verify database connection."""
    print_section("Verifying Database Connection")

    try:
        from app.database.session import engine

        # Try to connect
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print_success("Database connection successful")
            return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("Make sure PostgreSQL is running:")
        print_info("  docker-compose up -d")
        return False


async def verify_redis():
    """Verify Redis connection."""
    print_section("Verifying Redis Connection")

    try:
        from app.services.cache import CacheService

        cache = CacheService()
        # Try to get client
        await cache.get_client()

        # Try basic operation
        await cache.set("test_key", "test_value", ttl=10)
        value = await cache.get("test_key")

        if value == "test_value":
            print_success("Redis connection successful")
            await cache.delete("test_key")
            await cache.close()
            return True
        else:
            print_error("Redis connection failed: value mismatch")
            await cache.close()
            return False
    except Exception as e:
        print_error(f"Redis connection failed: {e}")
        print_info("Make sure Redis is running:")
        print_info("  docker-compose up -d")
        return False


async def verify_celery():
    """Verify Celery configuration."""
    print_section("Verifying Celery Configuration")

    try:
        from app.scheduler.celery_app import celery_app

        print_success(f"Celery app created: {celery_app.main}")
        print_info(f"Broker: {celery_app.conf.broker_url}")
        print_info(f"Backend: {celery_app.conf.result_backend}")
        print_info(f"Registered tasks: {len(celery_app.tasks)}")

        # Check if tasks are registered
        expected_tasks = [
            "app.scheduler.tasks.hello_world",
            "app.scheduler.tasks.process_video_generation",
        ]

        for task in expected_tasks:
            if task in celery_app.tasks:
                print_success(f"Task registered: {task}")
            else:
                print_error(f"Task not registered: {task}")
                return False

        return True
    except Exception as e:
        print_error(f"Celery verification failed: {e}")
        return False


async def verify_entities():
    """Verify database entities."""
    print_section("Verifying Database Entities")

    try:
        from app.entities.task import Task, TaskStatus, TaskPriority
        from app.entities.script import Script
        from app.entities.storyboard import Storyboard
        from app.entities.resource import Resource, ResourceType

        print_success("Task entity")
        print_info(f"  Statuses: {len(TaskStatus)} ({', '.join([s.value for s in TaskStatus][:5])}...)")
        print_info(f"  Priorities: {len(TaskPriority)} ({', '.join([p.value for p in TaskPriority])})")

        print_success("Script entity")
        print_success("Storyboard entity")
        print_success("Resource entity")

        return True
    except Exception as e:
        print_error(f"Entity verification failed: {e}")
        return False


async def verify_api():
    """Verify API can start."""
    print_section("Verifying API Application")

    try:
        from app.main import app

        print_success("FastAPI application created")
        print_info(f"Title: {app.title}")
        print_info(f"Version: {app.version}")
        print_info(f"Routes: {len(app.routes)}")

        # Check for health routes
        routes = [route.path for route in app.routes]
        health_routes = [
            "/api/v1/health",
            "/api/v1/health/detailed",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        ]

        for route in health_routes:
            if route in routes:
                print_success(f"Route exists: {route}")
            else:
                print_error(f"Route missing: {route}")
                return False

        return True
    except Exception as e:
        print_error(f"API verification failed: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("  Video Agent - Project Verification")
    print("=" * 60)

    # Setup logger
    setup_logger(
        log_file=settings.LOG_FILE,
        log_level=settings.LOG_LEVEL,
    )

    results = {}

    # Run verifications
    results["imports"] = await verify_imports()
    results["config"] = verify_config()
    results["entities"] = await verify_entities()
    results["celery"] = await verify_celery()
    results["api"] = await verify_api()
    results["database"] = await verify_database()
    results["redis"] = await verify_redis()

    # Summary
    print_section("Verification Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name.capitalize()}: {status}")

    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("\n" + "=" * 60)
        print("  All checks passed! Project is ready to run.")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Start services: docker-compose up -d")
        print("  2. Initialize DB: python scripts/init_db.py")
        print("  3. Start API: python scripts/start_api.py")
        print("  4. Start worker: python scripts/start_worker.py")
        print("  5. Run tests: pytest")
        return 0
    else:
        print("\n" + "=" * 60)
        print("  Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
