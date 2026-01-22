"""Video Agent for generating video clips."""

import asyncio
import json
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.models.manager import model_manager
from app.prompts.video_agent import VIDEO_PROMPT_ENHANCEMENT
from app.services.storage import StorageService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VideoAgent(BaseAgent):
    """
    Agent responsible for generating video clips from shots.

    Takes storyboard shots and first frame images, then generates
    video clips using AI video generation models.
    Supports concurrent generation of multiple videos.
    """

    def __init__(self, max_concurrent: int = 2):
        """
        Initialize Video Agent.

        Args:
            max_concurrent: Maximum number of concurrent video generations
        """
        super().__init__(
            name="video_agent",
            description="Generates video clips from storyboard shots using AI",
            retry_times=2,
            retry_delay=3.0,
        )
        self.max_concurrent = max_concurrent
        self._llm = None
        self._video_model = None
        self._storage = None

    def _initialize_client(self) -> None:
        """Initialize LLM and video model clients."""
        try:
            self._llm = model_manager.get_llm_provider()
            self._video_model = model_manager.get_video_provider()
            self._storage = StorageService()
            logger.info("VideoAgent initialized with LLM and video providers")
        except Exception as e:
            logger.error(f"Failed to initialize VideoAgent: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute video generation for all storyboard shots.

        Args:
            task: Task with storyboard and generated images in options

        Returns:
            Dict containing generated videos
        """
        logger.info(f"VideoAgent executing for task {task.id}")

        # Get storyboard from task options
        storyboard = task.options.get("storyboard")
        if not storyboard:
            raise ValueError("Storyboard not found in task options")

        # Get generated images
        generated_images = task.options.get("generated_images", [])
        images_dict = {
            (img["scene_number"], img["shot_number"]): img
            for img in generated_images
            if img.get("success")
        }

        # Get style
        style = task.style or task.options.get("style", "cinematic")

        # Generate videos for all shots
        shots = storyboard.get("scenes", [])
        logger.info(f"Generating videos for {len(shots)} shots")

        # Generate videos concurrently
        results = await self._generate_videos_concurrent(
            shots,
            images_dict,
            style,
            task.id,
        )

        # Store results
        await self._store_results(task, results)

        return {
            "status": "success",
            "total_shots": len(shots),
            "generated_videos": len([r for r in results if r["success"]]),
            "failed_videos": len([r for r in results if not r["success"]]),
            "videos": results,
        }

    async def _generate_videos_concurrent(
        self,
        shots: List[Dict[str, Any]],
        images_dict: Dict[tuple, Dict[str, Any]],
        style: str,
        task_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate videos for all shots concurrently.

        Args:
            shots: List of shot data
            images_dict: Dict mapping (scene, shot) to image data
            style: Video style
            task_id: Task ID for storage paths

        Returns:
            List of generation results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def generate_with_limit(shot_data: Dict[str, Any], index: int) -> Dict[str, Any]:
            async with semaphore:
                return await self._generate_single_video(
                    shot_data,
                    images_dict,
                    style,
                    task_id,
                    index,
                )

        tasks = [
            generate_with_limit(shot, index)
            for index, shot in enumerate(shots)
        ]

        return await asyncio.gather(*tasks)

    async def _generate_single_video(
        self,
        shot: Dict[str, Any],
        images_dict: Dict[tuple, Dict[str, Any]],
        style: str,
        task_id: str,
        index: int,
    ) -> Dict[str, Any]:
        """
        Generate video for a single shot.

        Args:
            shot: Shot data
            images_dict: Dict mapping (scene, shot) to image data
            style: Video style
            task_id: Task ID
            index: Shot index

        Returns:
            Dict containing generation result
        """
        shot_number = shot.get("shot_number", index + 1)
        scene_number = shot.get("scene_number", 1)
        duration = shot.get("duration", 5)

        try:
            logger.info(f"Generating video for shot {shot_number} (duration: {duration}s)")

            # Get visual description
            visual_description = shot.get("visual_description", "")
            if not visual_description:
                raise ValueError(f"Shot {shot_number} has no visual description")

            # Get first frame image
            image_key = (scene_number, shot_number)
            image_data = images_dict.get(image_key)

            # Enhance prompt for video generation
            enhanced_prompt_data = await self._enhance_prompt(
                visual_description,
                image_data.get("prompt", "") if image_data else "",
                style,
                duration,
            )

            # Generate video (image-to-video or text-to-video)
            if image_data:
                # Use image as first frame
                video_result = await self._video_model.generate_from_image(
                    image_url=image_data.get("url", ""),
                    prompt=enhanced_prompt_data["enhanced_prompt"],
                    duration=duration,
                    motion=enhanced_prompt_data.get("motion_description", "medium"),
                )
            else:
                # Text-to-video generation
                video_result = await self._video_model.generate(
                    prompt=enhanced_prompt_data["enhanced_prompt"],
                    duration=duration,
                    aspect_ratio="16:9",
                )

            # Get video URL
            video_url = video_result.get("url")
            if not video_url:
                # For mock provider, might need to poll for status
                generation_id = video_result.get("id")
                if generation_id:
                    # Poll for completion
                    video_url = await self._wait_for_video_completion(generation_id)

            if not video_url:
                raise ValueError(f"No video URL returned for shot {shot_number}")

            # Download video
            video_content = await self._video_model.download_video(video_url)

            # Store video
            storage_path = f"tasks/{task_id}/videos/scene_{scene_number}_shot_{shot_number}.mp4"
            stored_url = await self._storage.upload(
                storage_path,
                video_content,
                metadata={
                    "shot_number": shot_number,
                    "scene_number": scene_number,
                    "style": style,
                    "duration": duration,
                },
            )

            logger.info(f"Successfully generated video for shot {shot_number}: {storage_path}")

            return {
                "success": True,
                "shot_number": shot_number,
                "scene_number": scene_number,
                "storage_path": storage_path,
                "url": stored_url,
                "duration": duration,
                "original_url": video_url,
            }

        except Exception as e:
            logger.error(f"Failed to generate video for shot {shot_number}: {e}")
            return {
                "success": False,
                "shot_number": shot_number,
                "scene_number": scene_number,
                "error": str(e),
            }

    async def _enhance_prompt(
        self,
        shot_description: str,
        image_description: str,
        style: str,
        duration: int,
    ) -> Dict[str, Any]:
        """
        Enhance shot description for video generation.

        Args:
            shot_description: Original shot description
            image_description: First frame image description
            style: Video style
            duration: Video duration

        Returns:
            Dict containing enhanced prompt and metadata
        """
        try:
            prompt = VIDEO_PROMPT_ENHANCEMENT.format(
                shot_description=shot_description,
                image_description=image_description,
                style=style,
                duration=duration,
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
                "motion_description": "smooth camera movement",
                "camera_movement": "slow pan",
                "pacing": "moderate",
                "key_moments": [],
            }

    async def _wait_for_video_completion(
        self,
        generation_id: str,
        max_wait: int = 60,
        poll_interval: int = 2,
    ) -> str:
        """
        Wait for video generation to complete.

        Args:
            generation_id: Video generation ID
            max_wait: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            Video URL
        """
        import asyncio

        waited = 0
        while waited < max_wait:
            status = await self._video_model.get_generation_status(generation_id)

            if status.get("status") == "completed":
                return status.get("url", "")
            elif status.get("status") == "failed":
                raise RuntimeError(f"Video generation failed: {status.get('error')}")

            await asyncio.sleep(poll_interval)
            waited += poll_interval

        raise TimeoutError(f"Video generation timed out after {max_wait}s")

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
        task.options["generated_videos"] = results

        # In a real implementation, would also save to database
        logger.debug(f"Stored {len(results)} video generation results")

    def validate_input(self, task: Task) -> bool:
        """
        Validate task input for video generation.

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
        logger.debug(f"VideoAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"VideoAgent after_execute for task {task.id}")
        logger.info(
            f"Generated {result['generated_videos']}/{result['total_shots']} videos "
            f"for task {task.id}"
        )


__all__ = ["VideoAgent"]
