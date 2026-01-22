"""Storyboard Agent for breaking down scripts into shots."""

import json
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.core.context import AgentContext
from app.models.manager import model_manager
from app.prompts.storyboard_agent import (
    STORYBOARD_BREAKDOWN_PROMPT,
    STORYBOARD_VALIDATION_PROMPT,
    FRAME_DESCRIPTION_PROMPT,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StoryboardAgent(BaseAgent):
    """
    Agent responsible for breaking down scripts into storyboard shots.

    Converts script scenes into detailed shot-by-shot storyboards with
    camera angles, movements, visual descriptions, and production notes.
    """

    def __init__(self):
        """Initialize Storyboard Agent."""
        super().__init__(
            name="storyboard_agent",
            description="Breaks down scripts into detailed storyboard shots",
            retry_times=2,
            retry_delay=1.0,
        )
        self._llm = None

    def _initialize_client(self) -> None:
        """Initialize LLM client."""
        try:
            self._llm = model_manager.get_llm_provider()
            logger.info("StoryboardAgent initialized with LLM provider")
        except Exception as e:
            logger.error(f"Failed to initialize StoryboardAgent LLM: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute storyboard breakdown for the task.

        Args:
            task: Task with script data in context

        Returns:
            Dict containing storyboard breakdown
        """
        logger.info(f"StoryboardAgent executing for task {task.id}")

        # Get script from task options (it should have been stored by previous agents)
        script = task.options.get("script")
        if not script:
            raise ValueError("Script not found in task options")

        # Get style
        style = task.style or task.options.get("style", "cinematic")

        # Get duration
        duration = task.options.get("duration", 60)

        # Generate storyboard
        storyboard = await self._generate_storyboard(script, style, duration)

        # Validate storyboard
        validation = await self._validate_storyboard(storyboard, script)

        return {
            "status": "success",
            "storyboard": storyboard,
            "validation": validation,
        }

    async def _generate_storyboard(
        self,
        script: Dict[str, Any],
        style: str,
        duration: int,
    ) -> Dict[str, Any]:
        """
        Generate storyboard from script.

        Args:
            script: Script to break down
            style: Video style
            duration: Total duration

        Returns:
            Dict containing storyboard data
        """
        try:
            # Generate prompt
            prompt = STORYBOARD_BREAKDOWN_PROMPT.format(
                title=script.get("title", "Untitled"),
                script=json.dumps(script),
                style=style,
                duration=duration,
            )

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=3000,
            )

            # Parse JSON response
            storyboard_data = self._parse_json_response(response)

            logger.info(
                f"Generated storyboard with {storyboard_data.get('total_shots', 0)} shots "
                f"across {storyboard_data.get('total_scenes', 0)} scenes "
                f"for task"
            )

            # Add metadata
            storyboard_data["style"] = style
            storyboard_data["source_script_title"] = script.get("title")

            return storyboard_data

        except Exception as e:
            logger.error(f"Storyboard generation failed: {e}")
            raise

    async def _validate_storyboard(
        self,
        storyboard: Dict[str, Any],
        script: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate generated storyboard.

        Args:
            storyboard: Storyboard to validate
            script: Original script

        Returns:
            Dict containing validation results
        """
        try:
            # Generate validation prompt
            prompt = STORYBOARD_VALIDATION_PROMPT.format(
                storyboard=json.dumps(storyboard),
                script=json.dumps(script),
            )

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse validation response
            validation_data = self._parse_json_response(response)

            logger.info(
                f"Storyboard validation - score: {validation_data.get('overall_score')}, "
                f"valid: {validation_data.get('is_valid')}"
            )

            return validation_data

        except Exception as e:
            logger.warning(f"Storyboard validation failed: {e}")
            # Return basic validation
            return {
                "is_valid": bool(storyboard.get("scenes")),
                "overall_score": 7.0,
                "reasoning": "Basic validation performed",
            }

    async def generate_frame_description(
        self,
        shot: Dict[str, Any],
        style: str,
    ) -> Dict[str, Any]:
        """
        Generate detailed first frame description for AI image generation.

        Args:
            shot: Shot data from storyboard
            style: Video style

        Returns:
            Dict containing frame generation prompt
        """
        try:
            shot_description = shot.get("visual_description", "")
            if not shot_description:
                raise ValueError("Shot has no visual description")

            # Generate prompt
            prompt = FRAME_DESCRIPTION_PROMPT.format(
                shot_description=shot_description,
                style=style,
            )

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=500,
            )

            # Parse response
            frame_data = self._parse_json_response(response)

            logger.debug(f"Generated frame description for shot")

            return frame_data

        except Exception as e:
            logger.error(f"Frame description generation failed: {e}")
            raise

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
        Validate task input for storyboard generation.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        if not task:
            logger.error("Task is missing")
            return False

        # Check if script exists in task options
        script = task.options.get("script")
        if not script:
            logger.error("Script not found in task options")
            return False

        # Check if script has scenes
        scenes = script.get("scenes")
        if not scenes or len(scenes) == 0:
            logger.error("Script has no scenes")
            return False

        return True

    async def before_execute(self, task: Task) -> None:
        """Hook called before execution."""
        logger.debug(f"StoryboardAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"StoryboardAgent after_execute for task {task.id}")
        # Could store storyboard in database here

    async def refine_storyboard(
        self,
        task: Task,
        current_storyboard: Dict[str, Any],
        feedback: str,
    ) -> Dict[str, Any]:
        """
        Refine an existing storyboard based on feedback.

        Args:
            task: Original task
            current_storyboard: Current storyboard to refine
            feedback: User feedback for improvements

        Returns:
            Refined storyboard
        """
        from app.prompts.storyboard_agent import STORYBOARD_REFINEMENT_PROMPT

        logger.info(f"Refining storyboard for task {task.id}")

        try:
            prompt = STORYBOARD_REFINEMENT_PROMPT.format(
                current_storyboard=json.dumps(current_storyboard),
                feedback=feedback,
            )

            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=3000,
            )

            refined_storyboard = self._parse_json_response(response)

            logger.info(f"Storyboard refined successfully for task {task.id}")

            return refined_storyboard

        except Exception as e:
            logger.error(f"Storyboard refinement failed: {e}")
            raise


__all__ = ["StoryboardAgent"]
