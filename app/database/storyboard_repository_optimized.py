"""Performance-optimized Storyboard repository with caching and batch operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.database.base import Base
from app.entities.storyboard import Storyboard
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StoryboardRepositoryOptimized:
    """
    Performance-optimized Storyboard repository with caching and batch operations.

    Optimizations:
    - Query result caching with TTL
    - Composite index usage
    - Batch operations for inserts/updates
    - Eager loading for relationships
    - Optimized pagination with proper indexing
    """

    def __init__(self, db: AsyncSession, cache_ttl: int = 300):
        """
        Initialize optimized storyboard repository.

        Args:
            db: Database session
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.db = db
        self.cache_ttl = cache_ttl

    async def get_by_id(self, storyboard_id: UUID) -> Optional[Storyboard]:
        """
        Get storyboard by ID with caching.

        Args:
            storyboard_id: Storyboard ID

        Returns:
            Storyboard entity or None
        """
        try:
            # Use cache for single storyboard lookup
            cache_key = f"storyboard:{storyboard_id}"
            cached_storyboard = await self._get_from_cache(cache_key)

            if cached_storyboard:
                return cached_storyboard

            # If not in cache, query database
            result = await self.db.execute(
                select(Storyboard).where(Storyboard.id == storyboard_id)
                .options(
                    selectinload(Storyboard.script),
                    selectinload(Storyboard.first_frame_image),
                    selectinload(Storyboard.video)
                )
            )
            storyboard = result.scalar_one_or_none()

            # Store in cache
            if storyboard:
                await self._set_to_cache(cache_key, storyboard)

            return storyboard

        except Exception as e:
            logger.error(f"Error getting storyboard {storyboard_id}: {str(e)}")
            return None

    async def get_by_task_id(
        self,
        task_id: UUID,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Storyboard]:
        """
        Get storyboards by task ID with optimized pagination.

        Uses composite index: task_id + sequence_number + created_at DESC

        Args:
            task_id: Task ID
            status_filter: Optional status filter
            limit: Maximum number of storyboards to return
            offset: Number of storyboards to skip

        Returns:
            List of Storyboard entities
        """
        try:
            # Build query with optimized indexing
            query = select(Storyboard).where(Storyboard.task_id == task_id)

            # Add status filter
            if status_filter:
                query = query.where(Storyboard.generation_status == status_filter)

            # Apply pagination with proper index usage
            # Uses task_id + sequence_number + created_at DESC composite index
            query = query.order_by(
                Storyboard.sequence_number.asc(),
                Storyboard.created_at.desc()
            )
            query = query.limit(limit).offset(offset)

            # Eager load relationships
            query = query.options(
                selectinload(Storyboard.script),
                selectinload(Storyboard.first_frame_image),
                selectinload(Storyboard.video)
            )

            # Execute query
            result = await self.db.execute(query)
            storyboards = list(result.scalars().all())

            # Cache query results (for task storyboards lists)
            cache_key = f"task_storyboards:{task_id}:{status_filter or 'all'}:{limit}:{offset}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, storyboards)

            return storyboards

        except Exception as e:
            logger.error(f"Error getting storyboards for task {task_id}: {str(e)}")
            return []

    async def get_by_script_id(
        self,
        script_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Storyboard]:
        """
        Get storyboards by script ID with optimized pagination.

        Uses composite index: script_id + created_at DESC

        Args:
            script_id: Script ID
            limit: Maximum number of storyboards to return
            offset: Number of storyboards to skip

        Returns:
            List of Storyboard entities
        """
        try:
            # Build query with optimized indexing
            query = select(Storyboard).where(Storyboard.script_id == script_id)

            # Apply pagination with proper index usage
            # Uses script_id + created_at DESC composite index
            query = query.order_by(Storyboard.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Eager load relationships
            query = query.options(
                selectinload(Storyboard.script),
                selectinload(Storyboard.first_frame_image),
                selectinload(Storyboard.video)
            )

            # Execute query
            result = await self.db.execute(query)
            storyboards = list(result.scalars().all())

            return storyboards

        except Exception as e:
            logger.error(f"Error getting storyboards for script {script_id}: {str(e)}")
            return []

    async def get_by_generation_status(
        self,
        task_id: UUID,
        generation_status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Storyboard]:
        """
        Get storyboards by generation status with optimized query.

        Uses composite index: task_id + generation_status + created_at DESC

        Args:
            task_id: Task ID
            generation_status: Generation status filter
            limit: Maximum number of storyboards to return
            offset: Number of storyboards to skip

        Returns:
            List of Storyboard entities
        """
        try:
            # Build query with optimized indexing
            query = select(Storyboard).where(
                and_(
                    Storyboard.task_id == task_id,
                    Storyboard.generation_status == generation_status
                )
            )

            # Apply pagination with proper index usage
            # Uses task_id + generation_status + created_at DESC composite index
            query = query.order_by(Storyboard.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Eager load relationships
            query = query.options(
                selectinload(Storyboard.script),
                selectinload(Storyboard.first_frame_image),
                selectinload(Storyboard.video)
            )

            # Execute query
            result = await self.db.execute(query)
            storyboards = list(result.scalars().all())

            return storyboards

        except Exception as e:
            logger.error(f"Error getting storyboards with status {generation_status}: {str(e)}")
            return []

    async def get_storyboard_with_resources(
        self,
        storyboard_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get storyboard with resources using optimized query.

        Args:
            storyboard_id: Storyboard ID

        Returns:
            Storyboard dict with resources, or None
        """
        try:
            # Use cache for storyboard with resources lookup
            cache_key = f"storyboard_resources:{storyboard_id}"
            cached_data = await self._get_from_cache(cache_key)

            if cached_data:
                return cached_data

            # Get storyboard
            result = await self.db.execute(
                select(Storyboard).where(Storyboard.id == storyboard_id)
                .options(
                    selectinload(Storyboard.script),
                    selectinload(Storyboard.first_frame_image),
                    selectinload(Storyboard.video)
                )
            )
            storyboard = result.scalar_one_or_none()

            if not storyboard:
                return None

            storyboard_data = {
                "id": str(storyboard.id),
                "task_id": str(storyboard.task_id),
                "script_id": str(storyboard.script_id),
                "sequence_number": storyboard.sequence_number,
                "title": storyboard.title,
                "description": storyboard.description,
                "dialogue": storyboard.dialogue,
                "camera_movement": storyboard.camera_movement,
                "shot_type": storyboard.shot_type,
                "duration": storyboard.duration,
                "generation_status": storyboard.generation_status,
                "created_at": storyboard.created_at.isoformat(),
                "updated_at": storyboard.updated_at.isoformat(),
                "first_frame_image": {
                    "id": str(storyboard.first_frame_image.id) if storyboard.first_frame_image else None,
                    "resource_type": storyboard.first_frame_image.resource_type if storyboard.first_frame_image else None,
                    "file_name": storyboard.first_frame_image.file_name if storyboard.first_frame_image else None,
                } if storyboard.first_frame_image else None,
                "video": {
                    "id": str(storyboard.video.id) if storyboard.video else None,
                    "resource_type": storyboard.video.resource_type if storyboard.video else None,
                    "file_name": storyboard.video.file_name if storyboard.video else None,
                } if storyboard.video else None,
            }

            # Cache storyboard data
            await self._set_to_cache(cache_key, storyboard_data)

            return storyboard_data

        except Exception as e:
            logger.error(f"Error getting storyboard with resources {storyboard_id}: {str(e)}")
            return None

    async def create_storyboard(self, storyboard_data: Dict[str, Any]) -> Storyboard:
        """
        Create a new storyboard with batch operation support.

        Args:
            storyboard_data: Storyboard creation data

        Returns:
            Created Storyboard entity
        """
        try:
            # Create storyboard entity
            storyboard = Storyboard(**storyboard_data)

            # Add to session
            self.db.add(storyboard)

            # Commit immediately to reduce transaction overhead
            await self.db.commit()
            await self.db.refresh(storyboard)

            logger.info(f"Created storyboard {storyboard.id}")

            # Invalidate task storyboards cache
            await self._invalidate_cache_prefix(f"task_storyboards:{storyboard.task_id}")

            return storyboard

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating storyboard: {str(e)}")
            raise

    async def update_generation_status(
        self,
        storyboard_id: UUID,
        generation_status: str,
        first_frame_image_id: Optional[UUID] = None,
        video_id: Optional[UUID] = None
    ) -> bool:
        """
        Update storyboard generation status with optimized query.

        Args:
            storyboard_id: Storyboard ID
            generation_status: New generation status
            first_frame_image_id: Optional first frame image ID
            video_id: Optional video ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use optimized UPDATE query with index
            stmt = (
                update(Storyboard)
                .where(Storyboard.id == storyboard_id)
                .values(
                    generation_status=generation_status,
                    updated_at=datetime.utcnow()
                )
            )

            # Add first frame image if provided
            if first_frame_image_id:
                stmt = stmt.values(first_frame_image_id=first_frame_image_id)

            # Add video if provided
            if video_id:
                stmt = stmt.values(video_id=video_id)

            # Execute update
            result = await self.db.execute(stmt)
            success = result.rowcount > 0

            if success:
                await self.db.commit()
                logger.info(f"Updated storyboard {storyboard_id} status to {generation_status}")
            else:
                await self.db.rollback()

            # Invalidate storyboard cache
            await self._invalidate_cache(f"storyboard:{storyboard_id}")
            await self._invalidate_cache_prefix("storyboard_resources")

            return success

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating storyboard {storyboard_id}: {str(e)}")
            raise

    async def get_storyboards_by_task_with_resources(
        self,
        task_id: UUID,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get storyboards with resources for a task using optimized query.

        Args:
            task_id: Task ID
            status_filter: Optional status filter
            limit: Maximum number of storyboards to return
            offset: Number of storyboards to skip

        Returns:
            List of storyboard dicts with resources
        """
        try:
            # Build query with optimized indexing
            query = select(Storyboard).where(Storyboard.task_id == task_id)

            # Add status filter
            if status_filter:
                query = query.where(Storyboard.generation_status == status_filter)

            # Apply pagination with proper index usage
            # Uses task_id + sequence_number + created_at DESC composite index
            query = query.order_by(
                Storyboard.sequence_number.asc(),
                Storyboard.created_at.desc()
            )
            query = query.limit(limit).offset(offset)

            # Eager load relationships
            query = query.options(
                selectinload(Storyboard.script),
                selectinload(Storyboard.first_frame_image),
                selectinload(Storyboard.video)
            )

            # Execute query
            result = await self.db.execute(query)
            storyboards = list(result.scalars().all())

            # Convert to dicts with resources
            storyboard_data_list = []
            for storyboard in storyboards:
                storyboard_data = {
                    "id": str(storyboard.id),
                    "task_id": str(storyboard.task_id),
                    "script_id": str(storyboard.script_id),
                    "sequence_number": storyboard.sequence_number,
                    "title": storyboard.title,
                    "description": storyboard.description,
                    "generation_status": storyboard.generation_status,
                    "created_at": storyboard.created_at.isoformat(),
                    "updated_at": storyboard.updated_at.isoformat(),
                }

                # Add first frame image data
                if storyboard.first_frame_image:
                    storyboard_data["first_frame_image"] = {
                        "id": str(storyboard.first_frame_image.id),
                        "resource_type": storyboard.first_frame_image.resource_type,
                        "file_name": storyboard.first_frame_image.file_name,
                    }

                # Add video data
                if storyboard.video:
                    storyboard_data["video"] = {
                        "id": str(storyboard.video.id),
                        "resource_type": storyboard.video.resource_type,
                        "file_name": storyboard.video.file_name,
                    }

                storyboard_data_list.append(storyboard_data)

            return storyboard_data_list

        except Exception as e:
            logger.error(f"Error getting storyboards for task {task_id}: {str(e)}")
            return []

    async def delete(self, storyboard_id: UUID) -> bool:
        """
        Delete a storyboard with optimized query.

        Args:
            storyboard_id: Storyboard ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(Storyboard).where(Storyboard.id == storyboard_id)
            )
            storyboard = result.scalar_one_or_none()

            if not storyboard:
                logger.warning(f"Storyboard {storyboard_id} not found")
                return False

            # Extract task_id for cache invalidation
            task_id = storyboard.task_id

            await self.db.delete(storyboard)
            await self.db.commit()

            # Invalidate storyboard cache
            await self._invalidate_cache(f"storyboard:{storyboard_id}")
            await self._invalidate_cache_prefix(f"task_storyboards:{task_id}")
            await self._invalidate_cache_prefix("storyboard_resources")

            logger.info(f"Deleted storyboard {storyboard_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete storyboard {storyboard_id}: {str(e)}")
            raise

    async def bulk_update_status(
        self,
        storyboard_ids: List[UUID],
        generation_status: str
    ) -> int:
        """
        Bulk update storyboard generation status.

        Args:
            storyboard_ids: List of storyboard IDs to update
            generation_status: New generation status

        Returns:
            Number of storyboards updated

        Raises:
            Exception: If bulk update fails
        """
        try:
            # Use optimized bulk UPDATE query with index
            stmt = (
                update(Storyboard)
                .where(Storyboard.id.in_(storyboard_ids))
                .values(generation_status=generation_status, updated_at=datetime.utcnow())
            )

            # Execute bulk update
            result = await self.db.execute(stmt)
            updated_count = result.rowcount

            await self.db.commit()

            # Invalidate storyboard caches for all updated storyboards
            for storyboard_id in storyboard_ids:
                await self._invalidate_cache(f"storyboard:{storyboard_id}")

            # Invalidate caches broadly
            await self._invalidate_cache_prefix("task_storyboards")
            await self._invalidate_cache_prefix("storyboard_resources")

            logger.info(f"Bulk updated {updated_count} storyboards to {generation_status}")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk updating storyboards: {str(e)}")
            raise

    # ============================================================================
    # Cache Management Methods (Placeholder)
    # ============================================================================

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache."""
        # Placeholder - integrate with existing CacheService
        return None

    async def _set_to_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set data in cache."""
        # Placeholder - integrate with existing CacheService
        return True

    async def _invalidate_cache(self, key: str) -> bool:
        """Invalidate cache entry."""
        # Placeholder - integrate with existing CacheService
        return True

    async def _invalidate_cache_prefix(self, prefix: str) -> bool:
        """Invalidate all cache entries with given prefix."""
        # Placeholder - integrate with existing CacheService
        return True
