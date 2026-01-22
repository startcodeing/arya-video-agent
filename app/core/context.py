"""Agent Context for managing shared data across agents."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.resource import Resource
from app.entities.script import Script
from app.entities.storyboard import Storyboard
from app.entities.task import Task, TaskStatus
from app.services.cache import CacheService
from app.services.storage import StorageService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentContext:
    """
    Agent Context for managing shared data across agents.

    This class provides:
    - Database operations
    - Shared memory storage
    - Cache management
    - Event publishing
    - Logging
    """

    def __init__(self, db: AsyncSession, task_id: str):
        """
        Initialize the agent context.

        Args:
            db: Database session
            task_id: Task ID
        """
        self.db = db
        self.task_id = task_id
        self._cache = CacheService()
        self._storage = StorageService()
        self._shared_data: Dict[str, Any] = {}
        self._event_handlers: List[callable] = []

    async def get_task(self) -> Optional[Task]:
        """
        Get task information from database.

        Returns:
            Task object or None if not found
        """
        try:
            result = await self.db.execute(
                select(Task).where(Task.id == self.task_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self.log(f"Error getting task: {str(e)}", level="error")
            return None

    async def update_task_status(
        self,
        status: TaskStatus,
        current_agent: str = None
    ) -> None:
        """
        Update task status in database.

        Args:
            status: New task status
            current_agent: Name of the agent currently processing
        """
        try:
            await self.db.execute(
                update(Task)
                .where(Task.id == self.task_id)
                .values(
                    status=status,
                    current_agent=current_agent,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            # Publish event
            await self._publish_event("status_changed", {
                "task_id": self.task_id,
                "status": status,
                "current_agent": current_agent
            })

        except Exception as e:
            await self.log(f"Error updating task status: {str(e)}", level="error")
            raise

    async def update_task_progress(
        self,
        progress: float,
        message: str = None
    ) -> None:
        """
        Update task progress.

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        try:
            await self.db.execute(
                update(Task)
                .where(Task.id == self.task_id)
                .values(
                    progress=progress,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()

            # Publish progress event
            await self._publish_event("progress_update", {
                "task_id": self.task_id,
                "progress": progress,
                "message": message
            })

        except Exception as e:
            await self.log(f"Error updating task progress: {str(e)}", level="error")
            raise

    async def update_task_output(
        self,
        video_url: str,
        metadata: dict
    ) -> None:
        """
        Update task output.

        Args:
            video_url: URL of the generated video
            metadata: Output metadata
        """
        try:
            await self.db.execute(
                update(Task)
                .where(Task.id == self.task_id)
                .values(
                    output_video_url=video_url,
                    output_metadata=metadata,
                    status=TaskStatus.COMPLETED,
                    completed_at=datetime.utcnow()
                )
            )
            await self.db.commit()

        except Exception as e:
            await self.log(f"Error updating task output: {str(e)}", level="error")
            raise

    async def set_error(
        self,
        error_message: str,
        error_code: str = None,
        failed_step: str = None
    ) -> None:
        """
        Set task error information.

        Args:
            error_message: Error message
            error_code: Optional error code
            failed_step: Name of the failed step
        """
        try:
            await self.db.execute(
                update(Task)
                .where(Task.id == self.task_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_message=error_message,
                    error_code=error_code,
                    failed_step=failed_step,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()

        except Exception as e:
            await self.log(f"Error setting task error: {str(e)}", level="error")
            raise

    def set_shared_data(self, key: str, value: Any) -> None:
        """
        Set shared data in memory.

        Args:
            key: Data key
            value: Data value
        """
        self._shared_data[key] = value

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """
        Get shared data from memory.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Data value or default
        """
        return self._shared_data.get(key, default)

    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            full_key = f"task:{self.task_id}:{key}"
            data = await self._cache.get(full_key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            await self.log(f"Error getting from cache: {str(e)}", level="error")
            return None

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> None:
        """
        Set data in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            full_key = f"task:{self.task_id}:{key}"
            json_value = json.dumps(value)
            await self._cache.set(full_key, json_value, ttl)

        except Exception as e:
            await self.log(f"Error setting cache: {str(e)}", level="error")
            raise

    async def save_script(self, script_data: dict) -> Script:
        """
        Save script to database.

        Args:
            script_data: Script data

        Returns:
            Created Script object
        """
        try:
            script = Script(
                task_id=self.task_id,
                **script_data
            )
            self.db.add(script)
            await self.db.commit()
            await self.db.refresh(script)

            # Cache script
            await self.cache_set("script", script_data)

            return script

        except Exception as e:
            await self.log(f"Error saving script: {str(e)}", level="error")
            raise

    async def get_script(self) -> Optional[Script]:
        """
        Get script from database or cache.

        Returns:
            Script object or None
        """
        # Try cache first
        cached = await self.cache_get("script")
        if cached:
            return Script(**cached)

        # Query database
        try:
            result = await self.db.execute(
                select(Script).where(Script.task_id == self.task_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            await self.log(f"Error getting script: {str(e)}", level="error")
            return None

    async def save_storyboards(
        self,
        storyboards: List[dict]
    ) -> List[Storyboard]:
        """
        Save multiple storyboards to database.

        Args:
            storyboards: List of storyboard data

        Returns:
            List of created Storyboard objects
        """
        try:
            entities = []

            for i, sb_data in enumerate(storyboards):
                sb = Storyboard(
                    task_id=self.task_id,
                    sequence_number=i + 1,
                    **sb_data
                )
                self.db.add(sb)
                entities.append(sb)

            await self.db.commit()

            for entity in entities:
                await self.db.refresh(entity)

            return entities

        except Exception as e:
            await self.log(f"Error saving storyboards: {str(e)}", level="error")
            raise

    async def get_storyboards(self) -> List[Storyboard]:
        """
        Get all storyboards for this task.

        Returns:
            List of Storyboard objects ordered by sequence number
        """
        try:
            result = await self.db.execute(
                select(Storyboard)
                .where(Storyboard.task_id == self.task_id)
                .order_by(Storyboard.sequence_number)
            )
            return list(result.scalars().all())

        except Exception as e:
            await self.log(f"Error getting storyboards: {str(e)}", level="error")
            return []

    async def save_image_resource(
        self,
        storyboard: Storyboard,
        image_data: dict
    ) -> Resource:
        """
        Save image resource to database.

        Args:
            storyboard: Storyboard to associate with
            image_data: Image resource data

        Returns:
            Created Resource object
        """
        try:
            resource = Resource(
                task_id=self.task_id,
                resource_type="image",
                **image_data
            )
            self.db.add(resource)
            await self.db.commit()
            await self.db.refresh(resource)

            # Update storyboard
            await self.db.execute(
                update(Storyboard)
                .where(Storyboard.id == storyboard.id)
                .values(first_frame_image_id=str(resource.id))
            )
            await self.db.commit()

            return resource

        except Exception as e:
            await self.log(f"Error saving image resource: {str(e)}", level="error")
            raise

    async def save_video_resource(
        self,
        storyboard: Storyboard,
        video_data: dict
    ) -> Resource:
        """
        Save video resource to database.

        Args:
            storyboard: Storyboard to associate with
            video_data: Video resource data

        Returns:
            Created Resource object
        """
        try:
            resource = Resource(
                task_id=self.task_id,
                resource_type="video",
                **video_data
            )
            self.db.add(resource)
            await self.db.commit()
            await self.db.refresh(resource)

            # Update storyboard
            await self.db.execute(
                update(Storyboard)
                .where(Storyboard.id == storyboard.id)
                .values(
                    video_id=str(resource.id),
                    generation_status="completed"
                )
            )
            await self.db.commit()

            return resource

        except Exception as e:
            await self.log(f"Error saving video resource: {str(e)}", level="error")
            raise

    async def upload_file(
        self,
        file_path: str,
        content: bytes,
        content_type: str = None
    ) -> str:
        """
        Upload file to storage.

        Args:
            file_path: Path to store file
            content: File content
            content_type: MIME type

        Returns:
            Public URL of uploaded file
        """
        return await self._storage.upload(
            file_path=file_path,
            content=content,
            content_type=content_type
        )

    async def get_signed_url(
        self,
        storage_key: str,
        ttl: int = 3600
    ) -> str:
        """
        Get signed URL for file access.

        Args:
            storage_key: Storage key
            ttl: Time to live in seconds

        Returns:
            Signed URL
        """
        return await self._storage.get_signed_url(storage_key, ttl)

    async def log(self, message: str, level: str = "info") -> None:
        """
        Log a message.

        Args:
            message: Log message
            level: Log level (debug, info, warning, error, critical)
        """
        log_func = getattr(logger, level, logger.info)
        await log_func(f"[{self.task_id}] {message}")

    async def _publish_event(
        self,
        event_type: str,
        data: dict
    ) -> None:
        """
        Publish event to subscribers.

        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Call registered event handlers
        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                await self.log(
                    f"Error in event handler: {str(e)}",
                    level="error"
                )

    def register_event_handler(self, handler: callable) -> None:
        """
        Register an event handler.

        Args:
            handler: Callable that receives event dict
        """
        self._event_handlers.append(handler)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            await self._cache.close()
            await self.log("Context cleanup completed")
        except Exception as e:
            await self.log(f"Error during cleanup: {str(e)}", level="error")


__all__ = ["AgentContext"]
