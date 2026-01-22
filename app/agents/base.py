"""Base Agent class that all agents inherit from."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.context import AgentContext
from app.entities.task import Task


class BaseAgent(ABC):
    """
    Base Agent class that defines the standard interface for all agents.

    All agents should inherit from this class and implement the execute method.
    """

    # Agent metadata (should be overridden by subclasses)
    agent_name: str = "BaseAgent"
    agent_description: str = "Base agent class"
    retry_times: int = 3
    timeout: int = 300

    def __init__(self, context: AgentContext):
        """
        Initialize the agent.

        Args:
            context: AgentContext instance for shared data and operations
        """
        self.context = context

    @abstractmethod
    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute the agent's logic.

        This method must be implemented by all subclasses.

        Args:
            task: The task to process

        Returns:
            Dict containing the result of the agent's execution

        Raises:
            Exception: If execution fails
        """
        raise NotImplementedError(f"{self.agent_name} must implement execute()")

    async def execute_with_retry(self, task: Task) -> Dict[str, Any]:
        """
        Execute the agent with automatic retry logic.

        Implements exponential backoff retry strategy.

        Args:
            task: The task to process

        Returns:
            Dict containing the result of the agent's execution

        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.retry_times):
            try:
                await self.context.log(
                    f"{self.agent_name} executing... (Attempt {attempt + 1}/{self.retry_times})"
                )
                result = await self.execute(task)
                await self.context.log(
                    f"{self.agent_name} completed successfully"
                )
                return result

            except Exception as e:
                last_error = e
                await self.context.log(
                    f"{self.agent_name} failed on attempt {attempt + 1}: {str(e)}",
                    level="warning"
                )

                # If not the last attempt, backoff and retry
                if attempt < self.retry_times - 1:
                    backoff_delay = await self._backoff(attempt)
                    await self.context.log(
                        f"Retrying in {backoff_delay} seconds..."
                    )
                else:
                    # Last attempt failed, give up
                    break

        # All retries failed
        error_msg = f"{self.agent_name} failed after {self.retry_times} attempts: {str(last_error)}"
        await self.context.log(error_msg, level="error")
        raise Exception(error_msg) from last_error

    async def _backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay using exponential backoff strategy.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: 2^attempt seconds (1, 2, 4, 8, ...)
        delay = 2 ** attempt

        # Cap at 60 seconds
        delay = min(delay, 60)

        # Sleep
        await asyncio.sleep(delay)

        return delay

    async def validate_input(self, task: Task) -> bool:
        """
        Validate input task data.

        Override this method to add custom validation logic.

        Args:
            task: The task to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        # Basic validation
        if not task.topic:
            raise ValueError("Task topic is required")

        return True

    async def pre_execute(self, task: Task) -> None:
        """
        Hook called before execute method.

        Override this method to add pre-execution logic.

        Args:
            task: The task about to be processed
        """
        pass

    async def post_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """
        Hook called after execute method.

        Override this method to add post-execution logic.

        Args:
            task: The task that was processed
            result: The result from execute method
        """
        pass

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent metadata.

        Returns:
            Dict containing agent information
        """
        return {
            "name": self.agent_name,
            "description": self.agent_description,
            "retry_times": self.retry_times,
            "timeout": self.timeout,
        }

    async def health_check(self) -> bool:
        """
        Check if the agent is healthy.

        Override this method to add custom health checks.

        Returns:
            True if agent is healthy
        """
        return True

    async def cleanup(self, task: Task) -> None:
        """
        Cleanup resources after execution.

        Override this method to add cleanup logic.

        Args:
            task: The task that was processed
        """
        pass


__all__ = ["BaseAgent"]
