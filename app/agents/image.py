"""Image Agent for generating first frame images."""

import asyncio
import json
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.models.manager import model_manager
from app.prompts.image_agent import IMAGE_PROMPT_ENHANCEMENT
from app.services.storage import StorageService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageAgent(BaseAgent):
    """
    Agent responsible for generating first frame images for shots.

    Takes storyboard shots and generates images using AI image generation models.
    Supports concurrent generation of multiple images.
    """

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize Image Agent.

        Args:
            max_concurrent: Maximum number of concurrent image generations
        """
        super().__init__(
            name="image_agent",
            description="Generates first frame images for storyboard shots using AI",
            retry_times=2,
            retry_delay=2.0,
        )
        self.max_concurrent = max_concurrent
        self._llm = None
        self._image_model = None
        self._storage = None

    def _initialize_client(self) -> None:
        """Initialize LLM and image model clients."""
        try:
            self._llm = model_manager.get_llm_provider()
            self._image_model = model_manager.get_image_provider()
            self._storage = StorageService()
            logger.info("ImageAgent initialized with LLM and image providers")
        except Exception as e:
            logger.error(f"Failed to initialize ImageAgent: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute image generation for all storyboard shots.

        Args:
            task: Task with storyboard in options

        Returns:
            Dict containing generated images
        """
        logger.info(f"ImageAgent executing for task {task.id}")

        # Get storyboard from task options
        storyboard = task.options.get("storyboard")
        if not storyboard:
            raise ValueError("Storyboard not found in task options")

        # Get style
        style = task.style or task.options.get("style", "cinematic")

        # Generate images for all shots
        shots = storyboard.get("scenes", [])
        logger.info(f"Generating images for {len(shots)} shots")

        # Generate images concurrently
        results = await self._generate_images_concurrent(shots, style, task.id)

        # Store results and update task
        await self._store_results(task, results)

        return {
            "status": "success",
            "total_shots": len(shots),
            "generated_images": len([r for r in results if r["success"]]),
            "failed_images": len([r for r in results if not r["success"]]),
            "images": results,
        }

    async def _generate_images_concurrent(
        self,
        shots: List[Dict[str, Any]],
        style: str,
        task_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate images for all shots concurrently.

        Args:
            shots: List of shot data
            style: Video style
            task_id: Task ID for storage paths

        Returns:
            List of generation results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def generate_with_limit(shot_data: Dict[str, Any], index: int) -> Dict[str, Any]:
            async with semaphore:
                return await self._generate_single_image(shot_data, style, task_id, index)

        tasks = [
            generate_with_limit(shot, index)
            for index, shot in enumerate(shots)
        ]

        return await asyncio.gather(*tasks)

    async def _generate_single_image(
        self,
        shot: Dict[str, Any],
        style: str,
        task_id: str,
        index: int,
    ) -> Dict[str, Any]:
        """
        Generate image for a single shot.

        Args:
            shot: Shot data
            style: Video style
            task_id: Task ID
            index: Shot index

        Returns:
            Dict containing generation result
        """
        shot_number = shot.get("shot_number", index + 1)
        scene_number = shot.get("scene_number", 1)

        try:
            logger.info(f"Generating image for shot {shot_number}")

            # Get visual description
            visual_description = shot.get("visual_description", "")
            if not visual_description:
                raise ValueError(f"Shot {shot_number} has no visual description")

            # Enhance prompt using LLM
            enhanced_prompt_data = await self._enhance_prompt(
                visual_description,
                style,
            )

            # Generate image
            image_result = await self._image_model.generate(
                prompt=enhanced_prompt_data["enhanced_prompt"],
                size="1024x1024",
                n=1,
                quality="standard",
            )

            # Download image
            image_url = image_result.get("url")
            if not image_url:
                raise ValueError(f"No image URL returned for shot {shot_number}")

            image_content = await self._image_model.download_image(image_url)

            # Store image
            storage_path = f"tasks/{task_id}/images/scene_{scene_number}_shot_{shot_number}.png"
            stored_url = await self._storage.upload(
                storage_path,
                image_content,
                metadata={
                    "shot_number": shot_number,
                    "scene_number": scene_number,
                    "style": style,
                },
            )

            logger.info(f"Successfully generated image for shot {shot_number}: {storage_path}")

            return {
                "success": True,
                "shot_number": shot_number,
                "scene_number": scene_number,
                "storage_path": storage_path,
                "url": stored_url,
                "prompt": enhanced_prompt_data["enhanced_prompt"],
                "original_url": image_url,
            }

        except Exception as e:
            logger.error(f"Failed to generate image for shot {shot_number}: {e}")
            return {
                "success": False,
                "shot_number": shot_number,
                "scene_number": scene_number,
                "error": str(e),
            }

    async def _enhance_prompt(
        self,
        shot_description: str,
        style: str,
    ) -> Dict[str, Any]:
        """
        Enhance shot description for image generation.

        Args:
            shot_description: Original shot description
            style: Video style

        Returns:
            Dict containing enhanced prompt and metadata
        """
        try:
            prompt = IMAGE_PROMPT_ENHANCEMENT.format(
                shot_description=shot_description,
                style=style,
            )

            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
            )

            return self._parse_json_response(response)

        except Exception as e:
            logger.warning(f"Prompt enhancement failed: {e}, using original description")
            # Fall back to original description
            return {
                "enhanced_prompt": shot_description,
                "negative_prompt": "",
                "style_keywords": [style],
                "quality_modifiers": ["high quality"],
                "key_elements": [],
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dict
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)

            raise ValueError(f"Could not extract valid JSON from response")

    async def _store_results(self, task: Task, results: List[Dict[str, Any]]) -> None:
        """
        Store generation results.

        Args:
            task: Task entity
            results: Generation results
        """
        # Store results in task options for next agents
        task.options["generated_images"] = results

        # In a real implementation, would also save to database
        logger.debug(f"Stored {len(results)} image generation results")

    def validate_input(self, task: Task) -> bool:
        """
        Validate task input for image generation.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        if not task:
            logger.error("Task is missing")
            return False

        storyboard = task.options.get("storyboard")
        if not storyboard:
            logger.error("Storyboard not found in task options")
            return False

        shots = storyboard.get("scenes")
        if not shots or len(shots) == 0:
            logger.error("Storyboard has no scenes")
            return False

        return True

    async def before_execute(self, task: Task) -> None:
        """Hook called before execution."""
        logger.debug(f"ImageAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"ImageAgent after_execute for task {task.id}")
        logger.info(
            f"Generated {result['generated_images']}/{result['total_shots']} images "
            f"for task {task.id}"
        )


__all__ = ["ImageAgent"]
