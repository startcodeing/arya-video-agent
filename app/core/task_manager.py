"""Task manager for orchestrating agent pipeline execution."""

import asyncio
from typing import Any, Dict, List, Optional
from app.entities.task import Task, TaskStatus
from app.core.context import AgentContext
from app.core.state_machine import TaskStateMachine
from app.agents.base import BaseAgent
from app.models.manager import model_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskManager:
    """
    Orchestrates the execution of agents in the video generation pipeline.

    Manages:
    - Agent registration and discovery
    - Pipeline execution flow
    - State transitions
    - Error handling and retry logic
    - Progress tracking
    """

    def __init__(self):
        """Initialize task manager."""
        self._agents: Dict[str, BaseAgent] = {}
        self._pipeline: List[str] = []
        self._initialize_default_pipeline()

    def _initialize_default_pipeline(self) -> None:
        """Initialize the default agent pipeline."""
        self._pipeline = [
            "style_agent",
            "story_agent",
            "storyboard_agent",
            "image_agent",
            "video_agent",
            "composer_agent",
        ]

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent with the task manager.

        Args:
            name: Unique name for the agent
            agent: Agent instance
        """
        self._agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def unregister_agent(self, name: str) -> None:
        """
        Unregister an agent.

        Args:
            name: Name of the agent to unregister
        """
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Unregistered agent: {name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """
        List all registered agents.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def set_pipeline(self, pipeline: List[str]) -> None:
        """
        Set a custom pipeline execution order.

        Args:
            pipeline: List of agent names in execution order
        """
        # Validate all agents exist
        for agent_name in pipeline:
            if agent_name not in self._agents:
                raise ValueError(f"Agent not registered: {agent_name}")

        self._pipeline = pipeline
        logger.info(f"Pipeline set: {' -> '.join(pipeline)}")

    def get_pipeline(self) -> List[str]:
        """
        Get the current pipeline.

        Returns:
            List of agent names in execution order
        """
        return self._pipeline.copy()

    async def execute_task(
        self,
        task: Task,
        db_session,
        start_from: Optional[str] = None,
        stop_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task through the agent pipeline.

        Args:
            task: Task to execute
            db_session: Database session for AgentContext
            start_from: Agent name to start from (default: beginning)
            stop_at: Agent name to stop at (default: end)

        Returns:
            Dict containing execution results
        """
        logger.info(f"Starting task execution: {task.id}")

        # Create agent context
        context = AgentContext(db=db_session, task_id=task.id)

        # Get pipeline slice
        pipeline = self._get_pipeline_slice(start_from, stop_at)

        # Track results
        results = {
            "task_id": task.id,
            "pipeline_executed": pipeline,
            "agent_results": {},
            "final_status": task.status,
            "errors": [],
        }

        try:
            # Execute each agent in pipeline
            for agent_name in pipeline:
                agent = self._agents.get(agent_name)

                if not agent:
                    logger.error(f"Agent not found: {agent_name}")
                    raise ValueError(f"Agent not found: {agent_name}")

                # Update current agent in task
                await context.update_task_status(
                    status=TaskStatus(agent_name.replace("_agent", "") + "_generation")
                    if "_agent" in agent_name
                    else TaskStatus.PROCESSING,
                    current_agent=agent_name,
                )

                logger.info(f"Executing agent: {agent_name} for task {task.id}")

                # Execute agent with retry
                try:
                    agent_result = await agent.execute_with_retry(task)
                    results["agent_results"][agent_name] = agent_result

                    # Store result in context
                    context.set(f"{agent_name}_result", agent_result)

                    logger.info(
                        f"Agent {agent_name} completed successfully for task {task.id}"
                    )

                except Exception as e:
                    logger.error(
                        f"Agent {agent_name} failed for task {task.id}: {e}"
                    )
                    results["errors"].append({
                        "agent": agent_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    })

                    # Update task status to failed
                    await context.update_task_status(
                        status=TaskStatus.FAILED,
                        error_message=str(e),
                        error_code=type(e).__name__,
                        failed_step=agent_name,
                    )

                    # Check if we should retry
                    if task.retry_count < task.max_retries:
                        logger.info(
                            f"Initiating retry {task.retry_count + 1}/{task.max_retries}"
                        )
                        await context.update_task_status(
                            status=TaskStatus.RETRYING,
                        )
                        # Retry logic would be handled by caller
                        raise

                    # If no retries left, fail the task
                    results["final_status"] = TaskStatus.FAILED
                    return results

            # All agents completed successfully
            await context.update_task_status(
                status=TaskStatus.COMPLETED,
                progress=100.0,
            )

            results["final_status"] = TaskStatus.COMPLETED
            logger.info(f"Task {task.id} completed successfully")

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            results["final_status"] = TaskStatus.FAILED
            results["errors"].append({
                "step": "execution",
                "error": str(e),
            })

        return results

    async def execute_single_agent(
        self,
        task: Task,
        agent_name: str,
        db_session,
    ) -> Dict[str, Any]:
        """
        Execute a single agent for a task.

        Args:
            task: Task to execute
            agent_name: Name of agent to execute
            db_session: Database session

        Returns:
            Dict containing execution result
        """
        logger.info(f"Executing single agent {agent_name} for task {task.id}")

        context = AgentContext(db=db_session, task_id=task.id)
        agent = self._agents.get(agent_name)

        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")

        # Update current agent
        await context.update_task_status(
            current_agent=agent_name,
        )

        try:
            result = await agent.execute_with_retry(task)
            return {
                "task_id": task.id,
                "agent": agent_name,
                "status": "success",
                "result": result,
            }
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "task_id": task.id,
                "agent": agent_name,
                "status": "failed",
                "error": str(e),
            }

    async def retry_task(
        self,
        task: Task,
        db_session,
        from_state: Optional[TaskStatus] = None,
    ) -> Dict[str, Any]:
        """
        Retry a failed task from a specific state.

        Args:
            task: Task to retry
            db_session: Database session
            from_state: State to retry from (default: last failed state)

        Returns:
            Dict containing retry results
        """
        logger.info(f"Retrying task {task.id} from state {from_state}")

        # Determine which agent to start from
        if from_state:
            # Map state to agent
            state_to_agent = {
                TaskStatus.STYLE_DETECTION: "style_agent",
                TaskStatus.STORY_GENERATION: "story_agent",
                TaskStatus.STORYBOARD_BREAKDOWN: "storyboard_agent",
                TaskStatus.IMAGE_GENERATION: "image_agent",
                TaskStatus.VIDEO_GENERATION: "video_agent",
                TaskStatus.COMPOSING: "composer_agent",
            }
            start_agent = state_to_agent.get(from_state)
        else:
            # Use failed_step from task
            start_agent = task.failed_step

        if not start_agent:
            raise ValueError(f"Cannot determine retry agent for state: {from_state}")

        # Increment retry count
        task.retry_count += 1

        # Execute from the retry point
        return await self.execute_task(
            task=task,
            db_session=db_session,
            start_from=start_agent,
        )

    def _get_pipeline_slice(
        self,
        start_from: Optional[str] = None,
        stop_at: Optional[str] = None,
    ) -> List[str]:
        """
        Get a slice of the pipeline.

        Args:
            start_from: Agent name to start from
            stop_at: Agent name to stop at

        Returns:
            List of agent names
        """
        pipeline = self._pipeline.copy()

        if start_from:
            try:
                start_idx = pipeline.index(start_from)
                pipeline = pipeline[start_idx:]
            except ValueError:
                pass

        if stop_at:
            try:
                stop_idx = pipeline.index(stop_at)
                pipeline = pipeline[:stop_idx + 1]
            except ValueError:
                pass

        return pipeline

    async def get_task_progress(self, task: Task, db_session) -> Dict[str, Any]:
        """
        Get progress information for a task.

        Args:
            task: Task to check
            db_session: Database session

        Returns:
            Dict containing progress information
        """
        context = AgentContext(db=db_session, task_id=task.id)
        current_task = await context.get_task()

        if not current_task:
            return {"error": "Task not found"}

        # Calculate progress based on status
        progress_map = {
            TaskStatus.PENDING: 0,
            TaskStatus.STYLE_DETECTION: 10,
            TaskStatus.STORY_GENERATION: 25,
            TaskStatus.STORYBOARD_BREAKDOWN: 40,
            TaskStatus.IMAGE_GENERATION: 55,
            TaskStatus.VIDEO_GENERATION: 80,
            TaskStatus.COMPOSING: 90,
            TaskStatus.COMPLETED: 100,
            TaskStatus.FAILED: current_task.progress,
            TaskStatus.CANCELLED: current_task.progress,
        }

        progress = progress_map.get(current_task.status, 0)

        return {
            "task_id": task.id,
            "status": current_task.status,
            "progress": progress,
            "current_agent": current_task.current_agent,
            "error_message": current_task.error_message,
            "retry_count": current_task.retry_count,
            "elapsed_duration": current_task.elapsed_duration,
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get status of the pipeline configuration.

        Returns:
            Dict containing pipeline status
        """
        return {
            "pipeline": self._pipeline,
            "registered_agents": list(self._agents.keys()),
            "total_agents": len(self._agents),
            "pipeline_length": len(self._pipeline),
        }


# Global task manager instance
task_manager = TaskManager()


__all__ = ["TaskManager", "task_manager"]
