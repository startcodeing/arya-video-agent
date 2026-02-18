#!/usr/bin/env python3
"""
Performance benchmarking script for database operations.

This script benchmarks common database operations before and after
performance optimizations to validate performance improvements.

Usage:
    python scripts/benchmark_database.py --before
    python scripts/benchmark_database.py --after
"""

import asyncio
import time
import argparse
from typing import Dict, List, Tuple
from statistics import mean, stdev

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, func, and_
from sqlalchemy.sql.expression import text

from app.database.session import get_db
from app.entities.task import Task, TaskStatus, TaskPriority
from app.entities.conversation import Conversation, ConversationStatus
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseBenchmark:
    """Benchmark database operations and measure performance."""

    def __init__(self, engine=None):
        """
        Initialize benchmark.

        Args:
            engine: AsyncEngine instance (default: use production engine)
        """
        if engine is None:
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=5,
                max_overflow=10
            )
        else:
            self.engine = engine

        self.results: Dict[str, List[float]] = {}

    async def benchmark_task_pagination(self, session: AsyncSession) -> float:
        """
        Benchmark task pagination queries.

        Args:
            session: Database session

        Returns:
            Query execution time in seconds
        """
        user_id = "benchmark_user"

        # Warm up query
        await session.execute(
            select(Task).where(Task.user_id == user_id).limit(1)
        )

        # Benchmark query
        start_time = time.time()
        result = await session.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.status == TaskStatus.COMPLETED)
            .order_by(Task.created_at.desc())
            .limit(50)
            .offset(0)
        )
        rows = result.scalars().all()
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"Task pagination: {len(rows)} rows, {execution_time:.4f}s")

        return execution_time

    async def benchmark_conversation_pagination(self, session: AsyncSession) -> float:
        """
        Benchmark conversation pagination queries.

        Args:
            session: Database session

        Returns:
            Query execution time in seconds
        """
        user_id = "benchmark_user"

        # Warm up query
        await session.execute(
            select(Conversation).where(Conversation.user_id == user_id).limit(1)
        )

        # Benchmark query
        start_time = time.time()
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.status == ConversationStatus.ACTIVE)
            .order_by(Conversation.created_at.desc())
            .limit(50)
            .offset(0)
        )
        rows = result.scalars().all()
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"Conversation pagination: {len(rows)} rows, {execution_time:.4f}s")

        return execution_time

    async def benchmark_user_task_count(self, session: AsyncSession) -> float:
        """
        Benchmark user task count query.

        Args:
            session: Database session

        Returns:
            Query execution time in seconds
        """
        user_id = "benchmark_user"

        # Warm up query
        await session.execute(
            select(func.count(Task.id)).where(Task.user_id == user_id)
        )

        # Benchmark query
        start_time = time.time()
        result = await session.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.user_id == user_id,
                    Task.status == TaskStatus.COMPLETED
                )
            )
        )
        count = result.scalar()
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"Task count: {count}, {execution_time:.4f}s")

        return execution_time

    async def run_benchmark_suite(self, iterations: int = 10) -> Dict[str, List[float]]:
        """
        Run full benchmark suite with multiple iterations.

        Args:
            iterations: Number of benchmark iterations

        Returns:
            Dictionary mapping operation names to list of execution times
        """
        results = {
            "task_pagination": [],
            "conversation_pagination": [],
            "user_task_count": [],
        }

        async with AsyncSession(self.engine) as session:
            # Create test data
            await self._create_test_data(session, user_id="benchmark_user")

            # Run benchmarks
            for i in range(iterations):
                logger.info(f"Benchmark iteration {i+1}/{iterations}")

                try:
                    # Benchmark task pagination
                    task_time = await self.benchmark_task_pagination(session)
                    results["task_pagination"].append(task_time)

                    # Benchmark conversation pagination
                    conv_time = await self.benchmark_conversation_pagination(session)
                    results["conversation_pagination"].append(conv_time)

                    # Benchmark task count
                    count_time = await self.benchmark_user_task_count(session)
                    results["user_task_count"].append(count_time)

                except Exception as e:
                    logger.error(f"Benchmark failed: {e}")
                    continue

            # Clean up test data
            await self._cleanup_test_data(session)

        self.results = results
        return results

    async def _create_test_data(self, session: AsyncSession, user_id: str):
        """Create test data for benchmarking."""
        # Create test conversations
        for i in range(100):
            conversation = Conversation(
                user_id=user_id,
                session_id=f"session_{i}",
                title=f"Test Conversation {i}",
                status=ConversationStatus.ACTIVE,
                message_count=0
            )
            session.add(conversation)

        # Create test tasks
        from app.entities.task import Task
        for i in range(50):
            task = Task(
                user_id=user_id,
                topic=f"Test Topic {i}",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.NORMAL,
                progress=100.0
            )
            session.add(task)

        await session.commit()

    async def _cleanup_test_data(self, session: AsyncSession):
        """Clean up test data created for benchmarking."""
        user_id = "benchmark_user"

        # Delete test conversations
        await session.execute(
            text("DELETE FROM conversations WHERE user_id = :user_id")
        ).params(user_id=user_id)
        )

        # Delete test tasks
        await session.execute(
            text("DELETE FROM tasks WHERE user_id = :user_id")
        ).params(user_id=user_id)

        await session.commit()

    def generate_report(self) -> str:
        """
        Generate benchmark report.

        Returns:
            Benchmark report as markdown string
        """
        report = "# Database Performance Benchmark Report\n\n"
        report += f"**Benchmark Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for operation, times in self.results.items():
            if not times:
                continue

            avg_time = mean(times)
            std_dev = stdev(times) if len(times) > 1 else 0
            min_time = min(times)
            max_time = max(times)

            report += f"## {operation.replace('_', ' ').title()}\n\n"
            report += f"| Metric | Value |\n"
            report += f"|--------|-------|\n"
            report += f"| Average Time | {avg_time:.4f}s |\n"
            report += f"| Std Deviation | {std_dev:.4f}s |\n"
            report += f"| Min Time | {min_time:.4f}s |\n"
            report += f"| Max Time | {max_time:.4f}s |\n\n"

        return report


async def main():
    """Main entry point for benchmark execution."""
    parser = argparse.ArgumentParser(description="Database performance benchmarking")
    parser.add_argument("--iterations", type=int, default=10, help="Number of benchmark iterations")
    parser.add_argument("--mode", choices=["before", "after"], default="before", help="Benchmark mode")

    args = parser.parse_args()

    logger.info(f"Starting database benchmark ({args.mode} mode)...")
    logger.info(f"Iterations: {args.iterations}")

    # Create benchmark instance
    benchmark = DatabaseBenchmark()

    # Run benchmark suite
    results = await benchmark.run_benchmark_suite(iterations=args.iterations)

    # Generate and print report
    report = benchmark.generate_report()
    print("\n" + report)

    # Save results to file
    output_file = f"benchmark_results_{args.mode}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w') as f:
        f.write(report)

    logger.info(f"Benchmark results saved to {output_file}")
    logger.info(f"Benchmark completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
