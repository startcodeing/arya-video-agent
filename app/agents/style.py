"""Style Agent for detecting and setting video style."""

import json
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.core.context import AgentContext
from app.models.manager import model_manager
from app.prompts.style_agent import STYLE_DETECTION_PROMPT, STYLE_VALIDATION_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StyleAgent(BaseAgent):
    """
    Agent responsible for detecting and setting the video style.

    Analyzes the topic and determines the most appropriate visual style,
    including color palette, mood, camera techniques, and visual elements.
    """

    def __init__(self):
        """Initialize Style Agent."""
        super().__init__(
            name="style_agent",
            description="Detects and sets the appropriate video style based on topic analysis",
            retry_times=2,
            retry_delay=1.0,
        )
        self._llm = None

    def _initialize_client(self) -> None:
        """Initialize LLM client."""
        try:
            self._llm = model_manager.get_llm_provider()
            logger.info("StyleAgent initialized with LLM provider")
        except Exception as e:
            logger.error(f"Failed to initialize StyleAgent LLM: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute style detection for the task.

        Args:
            task: Task with topic to analyze

        Returns:
            Dict containing detected style information
        """
        logger.info(f"StyleAgent executing for task {task.id}")

        # If style is already specified, validate and use it
        if task.style:
            logger.info(f"Style already specified: {task.style}")
            result = await self._validate_existing_style(task)
        else:
            # Detect style from topic
            result = await self._detect_style(task)

        return result

    async def _detect_style(self, task: Task) -> Dict[str, Any]:
        """
        Detect appropriate style from topic.

        Args:
            task: Task to analyze

        Returns:
            Dict containing style information
        """
        try:
            # Generate prompt
            prompt = STYLE_DETECTION_PROMPT.format(topic=task.topic)

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )

            # Parse JSON response
            style_data = self._parse_json_response(response)

            logger.info(
                f"Detected style: {style_data.get('style')} for task {task.id}"
            )

            return {
                "status": "success",
                "style": style_data.get("style"),
                "reasoning": style_data.get("reasoning"),
                "visual_elements": style_data.get("visual_elements", []),
                "color_palette": style_data.get("color_palette"),
                "mood": style_data.get("mood"),
                "camera_style": style_data.get("camera_style"),
                "auto_detected": True,
            }

        except Exception as e:
            logger.error(f"Style detection failed: {e}")
            raise

    async def _validate_existing_style(self, task: Task) -> Dict[str, Any]:
        """
        Validate and enhance an existing style specification.

        Args:
            task: Task with pre-specified style

        Returns:
            Dict containing validated and enhanced style information
        """
        try:
            # Generate validation prompt
            prompt = STYLE_VALIDATION_PROMPT.format(
                topic=task.topic,
                style=task.style,
            )

            # Call LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=500,
            )

            # Parse validation response
            validation_data = self._parse_json_response(response)

            logger.info(
                f"Validated style: {task.style} - "
                f"appropriate: {validation_data.get('is_appropriate')}"
            )

            return {
                "status": "success",
                "style": task.style,
                "is_appropriate": validation_data.get("is_appropriate", True),
                "confidence": validation_data.get("confidence", 1.0),
                "suggestions": validation_data.get("suggestions", []),
                "reasoning": validation_data.get("reasoning"),
                "auto_detected": False,
            }

        except Exception as e:
            logger.error(f"Style validation failed: {e}")
            # Even if validation fails, return the specified style
            return {
                "status": "success",
                "style": task.style,
                "is_appropriate": True,
                "confidence": 1.0,
                "auto_detected": False,
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
            # LLMs sometimes add extra text
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)

            raise ValueError(f"Could not extract valid JSON from response: {response[:200]}")

    def validate_input(self, task: Task) -> bool:
        """
        Validate task input for style detection.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        if not task or not task.topic:
            logger.error("Task or topic is missing")
            return False

        if len(task.topic.strip()) < 3:
            logger.error("Topic is too short")
            return False

        return True

    async def before_execute(self, task: Task) -> None:
        """Hook called before execution."""
        logger.debug(f"StyleAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"StyleAgent after_execute for task {task.id}")
        # Could store result in database or cache here


__all__ = ["StyleAgent"]
