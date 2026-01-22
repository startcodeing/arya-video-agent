"""Composer Agent for composing final video from clips."""

import asyncio
import json
import os
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.entities.task import Task
from app.services.video_processor import video_processor
from app.services.storage import StorageService
from app.prompts.composer_agent import COMPOSITION_PLAN_PROMPT
from app.models.manager import model_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ComposerAgent(BaseAgent):
    """
    Agent responsible for composing the final video from video clips.

    Takes generated video clips and composes them into a final video
    with transitions, audio, and effects using FFmpeg.
    """

    def __init__(self):
        """Initialize Composer Agent."""
        super().__init__(
            name="composer_agent",
            description="Composes final video from clips using FFmpeg",
            retry_times=1,
            retry_delay=1.0,
        )
        self._llm = None
        self._storage = None
        self._video_processor = None

    def _initialize_client(self) -> None:
        """Initialize services."""
        try:
            self._llm = model_manager.get_llm_provider()
            self._storage = StorageService()
            self._video_processor = video_processor
            logger.info("ComposerAgent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ComposerAgent: {e}")
            raise

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute video composition.

        Args:
            task: Task with generated videos in options

        Returns:
            Dict containing composition result
        """
        logger.info(f"ComposerAgent executing for task {task.id}")

        # Check if FFmpeg is available
        if not self._video_processor.is_available():
            logger.error("FFmpeg is not available")
            raise RuntimeError("FFmpeg is not installed or not in PATH")

        # Get generated videos
        generated_videos = task.options.get("generated_videos", [])
        if not generated_videos:
            raise ValueError("No generated videos found in task options")

        # Get storyboard for composition info
        storyboard = task.options.get("storyboard", {})

        # Filter successful videos
        successful_videos = [v for v in generated_videos if v.get("success")]
        if not successful_videos:
            raise ValueError("No successfully generated videos")

        logger.info(f"Composing {len(successful_videos)} video clips")

        # Create composition plan
        composition_plan = await self._create_composition_plan(
            storyboard,
            successful_videos,
            task,
        )

        # Sort videos by shot number
        sorted_videos = sorted(
            successful_videos,
            key=lambda v: (v["scene_number"], v["shot_number"]),
        )

        # Get local file paths for videos
        video_paths = []
        for video in sorted_videos:
            # In a real implementation, would download from storage
            # For now, use storage_path
            video_paths.append(video["storage_path"])

        # Compose videos
        output_path = await self._compose_videos(
            video_paths,
            composition_plan,
            task.id,
        )

        # Upload final video
        final_url = await self._upload_final_video(output_path, task.id)

        # Clean up temporary files
        await self._cleanup_temp_files([output_path])

        # Update task with output
        await self._update_task_output(task, final_url, composition_plan)

        return {
            "status": "success",
            "output_video_url": final_url,
            "total_clips": len(sorted_videos),
            "final_duration": composition_plan.get("total_duration", 0),
            "composition_plan": composition_plan,
        }

    async def _create_composition_plan(
        self,
        storyboard: Dict[str, Any],
        videos: List[Dict[str, Any]],
        task: Task,
    ) -> Dict[str, Any]:
        """
        Create a composition plan using LLM.

        Args:
            storyboard: Storyboard data
            videos: Generated video data
            task: Task entity

        Returns:
            Composition plan dict
        """
        try:
            # Calculate total duration from videos
            total_duration = sum(v.get("duration", 5) for v in videos)

            # Create prompt for composition plan
            storyboard_summary = {
                "total_scenes": storyboard.get("total_scenes", len(videos)),
                "total_shots": len(videos),
                "estimated_duration": total_duration,
            }

            prompt = COMPOSITION_PLAN_PROMPT.format(
                storyboard_summary=json.dumps(storyboard_summary),
                duration=total_duration,
                total_shots=len(videos),
            )

            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1000,
            )

            plan = self._parse_json_response(response)

            logger.info(f"Created composition plan with {total_duration}s duration")

            return plan.get("composition_plan", {})

        except Exception as e:
            logger.warning(f"Failed to create composition plan: {e}, using defaults")
            # Return default plan
            return {
                "total_duration": total_duration,
                "shot_order": list(range(1, len(videos) + 1)),
                "transitions": [
                    {
                        "from_shot": i,
                        "to_shot": i + 1,
                        "type": "cut",
                        "duration": 0,
                    }
                    for i in range(len(videos) - 1)
                ],
                "audio_plan": {},
                "notes": "Default composition plan",
            }

    async def _compose_videos(
        self,
        video_paths: List[str],
        composition_plan: Dict[str, Any],
        task_id: str,
    ) -> str:
        """
        Compose video clips into final video.

        Args:
            video_paths: List of video file paths
            composition_plan: Composition plan
            task_id: Task ID

        Returns:
            Path to composed video
        """
        import tempfile

        # Create temporary output file
        with tempfile.NamedTemporaryFile(
            suffix="_composed.mp4",
            delete=False,
        ) as tmp:
            output_path = tmp.name

        try:
            # Get transitions from plan
            transitions = composition_plan.get("transitions", [])
            transition_type = transitions[0].get("type", "cut") if transitions else "cut"
            transition_duration = transitions[0].get("duration", 0.5) if transitions else 0.5

            # Compose videos
            logger.info(f"Composing {len(video_paths)} videos with {transition_type} transitions")

            result_path = await self._video_processor.concatenate_videos(
                video_paths=video_paths,
                output_path=output_path,
                transition_type=transition_type,
                transition_duration=transition_duration,
            )

            logger.info(f"Video composition complete: {result_path}")

            return result_path

        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            # Clean up on failure
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    async def _upload_final_video(
        self,
        video_path: str,
        task_id: str,
    ) -> str:
        """
        Upload final video to storage.

        Args:
            video_path: Path to composed video
            task_id: Task ID

        Returns:
            Storage URL
        """
        import os

        try:
            # Read video file
            with open(video_path, "rb") as f:
                video_content = f.read()

            # Upload to storage
            storage_path = f"tasks/{task_id}/output/final_video.mp4"
            url = await self._storage.upload(
                storage_path,
                video_content,
                metadata={
                    "type": "final_output",
                    "task_id": task_id,
                },
            )

            logger.info(f"Final video uploaded: {storage_path}")

            return url

        except Exception as e:
            logger.error(f"Failed to upload final video: {e}")
            raise

    async def _cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary files.

        Args:
            file_paths: List of file paths to clean up
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.debug(f"Cleaned up temporary file: {path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {path}: {e}")

    async def _update_task_output(
        self,
        task: Task,
        video_url: str,
        composition_plan: Dict[str, Any],
    ) -> None:
        """
        Update task with output information.

        Args:
            task: Task entity
            video_url: URL to final video
            composition_plan: Composition plan
        """
        task.output_video_url = video_url
        task.output_metadata = {
            "composition_plan": composition_plan,
            "completed_at": str(asyncio.get_event_loop().time()),
        }

        logger.info(f"Task {task.id} output updated with final video URL")

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

    def validate_input(self, task: Task) -> bool:
        """
        Validate task input for composition.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        if not task:
            logger.error("Task is missing")
            return False

        generated_videos = task.options.get("generated_videos")
        if not generated_videos:
            logger.error("No generated videos found")
            return False

        # Check if at least one video was successfully generated
        successful = any(v.get("success") for v in generated_videos)
        if not successful:
            logger.error("No successfully generated videos")
            return False

        return True

    async def before_execute(self, task: Task) -> None:
        """Hook called before execution."""
        logger.debug(f"ComposerAgent before_execute for task {task.id}")

    async def after_execute(self, task: Task, result: Dict[str, Any]) -> None:
        """Hook called after execution."""
        logger.debug(f"ComposerAgent after_execute for task {task.id}")
        logger.info(
            f"Successfully composed final video for task {task.id}: "
            f"{result['output_video_url']}"
        )


__all__ = ["ComposerAgent"]
