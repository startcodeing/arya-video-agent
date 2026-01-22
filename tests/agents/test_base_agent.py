"""Unit tests for BaseAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.base import BaseAgent
from app.entities.task import Task, TaskStatus
from app.utils.logger import get_logger


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    async def execute(self, task: Task) -> dict:
        """Simple mock execute that returns success."""
        return {"status": "success", "data": "test_data"}

    def validate_input(self, task: Task) -> bool:
        """Simple mock validation."""
        return task is not None


class TestBaseAgent:
    """Test suite for BaseAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = MockAgent(
            name="test_agent",
            description="Test agent",
            retry_times=3,
            retry_delay=1.0
        )

        assert agent.name == "test_agent"
        assert agent.description == "Test agent"
        assert agent.retry_times == 3
        assert agent.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        agent = MockAgent(name="test_agent")

        # Create a mock task
        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        result = await agent.execute(task)

        assert result["status"] == "success"
        assert result["data"] == "test_data"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_on_first_attempt(self):
        """Test retry mechanism succeeds on first attempt."""
        agent = MockAgent(name="test_agent", retry_times=3, retry_delay=0.1)

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        result = await agent.execute_with_retry(task)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self):
        """Test retry mechanism succeeds after retry."""
        call_count = 0

        class FlakyAgent(BaseAgent):
            async def execute(self, task: Task) -> dict:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Temporary error")
                return {"status": "success"}

            def validate_input(self, task: Task) -> bool:
                return True

        agent = FlakyAgent(name="flaky_agent", retry_times=3, retry_delay=0.01)

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        result = await agent.execute_with_retry(task)

        assert result["status"] == "success"
        assert call_count == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self):
        """Test retry mechanism exhausted all attempts."""
        class FailingAgent(BaseAgent):
            async def execute(self, task: Task) -> dict:
                raise ValueError("Permanent error")

            def validate_input(self, task: Task) -> bool:
                return True

        agent = FailingAgent(name="failing_agent", retry_times=2, retry_delay=0.01)

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        with pytest.raises(ValueError, match="Permanent error"):
            await agent.execute_with_retry(task)

    @pytest.mark.asyncio
    async def test_execute_with_hooks(self):
        """Test execution with before/after hooks."""
        hook_called = {"before": False, "after": False}

        class AgentWithHooks(BaseAgent):
            async def execute(self, task: Task) -> dict:
                return {"status": "success"}

            def validate_input(self, task: Task) -> bool:
                return True

            async def before_execute(self, task: Task) -> None:
                hook_called["before"] = True

            async def after_execute(self, task: Task, result: dict) -> None:
                hook_called["after"] = True

        agent = AgentWithHooks(name="hooked_agent")

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        await agent.execute_with_retry(task)

        assert hook_called["before"] is True
        assert hook_called["after"] is True

    @pytest.mark.asyncio
    async def test_execute_validation_fails(self):
        """Test execution fails validation."""
        class ValidatedAgent(BaseAgent):
            async def execute(self, task: Task) -> dict:
                return {"status": "success"}

            def validate_input(self, task: Task) -> bool:
                # Reject tasks with "invalid" in topic
                return "invalid" not in task.topic

        agent = ValidatedAgent(name="validated_agent")

        task = Task(
            id="test-task-id",
            topic="invalid topic",
            status=TaskStatus.PENDING
        )

        with pytest.raises(ValueError, match="Input validation failed"):
            await agent.execute_with_retry(task)

    @pytest.mark.asyncio
    async def test_execute_hook_exception_handling(self):
        """Test exceptions in hooks are handled properly."""
        class AgentWithBadHook(BaseAgent):
            async def execute(self, task: Task) -> dict:
                return {"status": "success"}

            def validate_input(self, task: Task) -> bool:
                return True

            async def before_execute(self, task: Task) -> None:
                raise RuntimeError("Hook error")

        agent = AgentWithBadHook(name="bad_hook_agent")

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        with pytest.raises(RuntimeError, match="Hook error"):
            await agent.execute_with_retry(task)

    @pytest.mark.asyncio
    async def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        agent = MockAgent(name="test_agent", retry_times=3, retry_delay=1.0)

        # Check backoff times
        assert agent._get_backoff_time(0) == pytest.approx(1.0 * (2 ** 0))
        assert agent._get_backoff_time(1) == pytest.approx(1.0 * (2 ** 1))
        assert agent._get_backoff_time(2) == pytest.approx(1.0 * (2 ** 2))

    @pytest.mark.asyncio
    async def test_abstract_methods_raise_error(self):
        """Test that abstract methods raise NotImplementedError."""
        agent = BaseAgent(name="abstract_agent")
        agent._validate_input_enabled = False  # Disable validation

        task = Task(
            id="test-task-id",
            topic="Test topic",
            status=TaskStatus.PENDING
        )

        with pytest.raises(NotImplementedError):
            await agent.execute(task)

    def test_get_info(self):
        """Test get_info method."""
        agent = MockAgent(
            name="info_agent",
            description="Agent for testing get_info"
        )

        info = agent.get_info()

        assert info["name"] == "info_agent"
        assert info["description"] == "Agent for testing get_info"
        assert "retry_times" in info
        assert "retry_delay" in info


__all__ = ["TestBaseAgent"]
