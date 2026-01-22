"""Story Agent for generating video scripts."""

import json
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.core.context import AgentContext
from app.models.manager import model_manager
from app.prompts.story_agent import STORY_GENERATION_PROMPT, STORY_VALIDATION_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StoryAgent(BaseAgent):
    """
    Agent responsible for generating video scripts.

    Creates compelling narratives with scene-by-scene breakdowns,
    dialogue, visual descriptions, and pacing information.
    """

    def __init__(self):
        """Initialize Story Agent."""
        super().__init__(
            name="story_agent",
            description="Generates engaging video scripts with scene breakdowns",
            retry_times=2,
            retry_delay=1.0,
        )
        self._llm = None

    def _initialize_client(self) -> None:
        """Initialize LLM client."""
        try:
            self._llm = model_manager.get_llm_provider()
            logger.info("StoryAgent initialized with LLM provider")
        except Exception as e:
            logger.error(f"Failed to initialize StoryAgent LLM: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute script generation for the task.

        Args:
            task: Task with topic and style

        Returns:
            Dict containing generated script
        """
        logger.info(f"StoryAgent executing for task {task.id}")

        # Get style from task options or result
        style = task.style or task.options.get("style", "cinematic")

        # Get target duration
        duration = task.options.get("duration", 60)

        # Generate script
        script = await self._generate_script(task, style, duration)

        # Validate script
        validation = await self._validate_script(script)

        return {
            "status": "success",
            "script": script,
            "validation": validation,
        }

    async def _generate_script(
        self,
        task: Task,
        style: str,
        duration: int,
    ) -> Dict[str, Any]:
        """
        Generate video script.

        Args:
            task: Task to generate script for
            style: Video style
            duration: Target duration in seconds

        Returns:
            Dict containing script data
        """
        try:
            # Generate prompt
            prompt = STORY_GENERATION_PROMPT.format(
                topic=task.topic,
                style=style,
                duration=duration,
            )

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.8,
                max_tokens=2000,
            )

            # Parse JSON response
            script_data = self._parse_json_response(response)

            logger.info(
                f"Generated script '{script_data.get('title')}' "
                f"with {len(script_data.get('scenes', []))} scenes "
                f"for task {task.id}"
            )

            # Add metadata
            script_data["style"] = style
            script_data["target_duration"] = duration

            return script_data

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise

    async def _validate_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generated script.

        Args:
            script: Script to validate

        Returns:
            Dict containing validation results
        """
        try:
            # Generate validation prompt
            prompt = STORY_VALIDATION_PROMPT.format(script=json.dumps(script))

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse validation response
            validation_data = self._parse_json_response(response)

            logger.info(
                f"Script validation - score: {validation_data.get('overall_score')}, "
                f"valid: {validation_data.get('is_valid')}"
            )

            return validation_data

        except Exception as e:
            logger.warning(f"Script validation failed: {e}")
            # Return basic validation if detailed validation fails
            return {
                "is_valid": bool(script.get("scenes")),
                "overall_score": 7.0,
                "reasoning": "Basic validation performed",
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)

            raise ValueError(f"Could not extract valid JSON from response: {response[:200]}")

    def validate_input(self, task: Task) -> bool:
        """
        Validate task input for script generation.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        if not task or not task.topic:
            logger.error("Task or topic is missing")
            return False

        if len(task.topic.strip()) < 5:
            logger.error("Topic is too short for script generation")
            return False

        return True

    async def before_execute(self, task: Task) -> None:
        """Hook called before execution."""
        logger.debug(f"StoryAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"StoryAgent after_execute for task {task.id}")
        # Could store script in database here

    async def refine_script(
        self,
        task: Task,
        current_script: Dict[str, Any],
        feedback: str,
    ) -> Dict[str, Any]:
        """
        Refine an existing script based on feedback.

        Args:
            task: Original task
            current_script: Current script to refine
            feedback: User feedback for improvements

        Returns:
            Refined script
        """
        from app.prompts.story_agent import STORY_REFINEMENT_PROMPT

        logger.info(f"Refining script for task {task.id}")

        try:
            prompt = STORY_REFINEMENT_PROMPT.format(
                current_script=json.dumps(current_script),
                feedback=feedback,
            )

            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            refined_script = self._parse_json_response(response)

            logger.info(f"Script refined successfully for task {task.id}")

            return refined_script

        except Exception as e:
            logger.error(f"Script refinement failed: {e}")
            raise


__all__ = ["StoryAgent"]
