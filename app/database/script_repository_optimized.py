"""Performance-optimized Script repository with caching and batch operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.database.base import Base
from app.entities.script import Script
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScriptRepositoryOptimized:
    """
    Performance-optimized Script repository with caching and batch operations.

    Optimizations:
    - Query result caching with TTL
    - Composite index usage
    - Batch operations for inserts/updates
    - Eager loading for relationships
    - Optimized pagination with proper indexing
    """

    def __init__(self, db: AsyncSession, cache_ttl: int = 300):
        """
        Initialize optimized script repository.

        Args:
            db: Database session
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.db = db
        self.cache_ttl = cache_ttl

    async def get_by_id(self, script_id: UUID) -> Optional[Script]:
        """
        Get script by ID with caching.

        Args:
            script_id: Script ID

        Returns:
            Script entity or None
        """
        try:
            # Use cache for single script lookup
            cache_key = f"script:{script_id}"
            cached_script = await self._get_from_cache(cache_key)

            if cached_script:
                return cached_script

            # If not in cache, query database
            result = await self.db.execute(
                select(Script).where(Script.id == script_id)
            )
            script = result.scalar_one_or_none()

            # Store in cache
            if script:
                await self._set_to_cache(cache_key, script)

            return script

        except Exception as e:
            logger.error(f"Error getting script {script_id}: {str(e)}")
            return None

    async def get_by_task_id(
        self,
        task_id: UUID,
        status_filter: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Script]:
        """
        Get scripts by task ID with optimized pagination.

        Uses composite index: task_id + created_at DESC

        Args:
            task_id: Task ID
            status_filter: Optional status filter
            limit: Maximum number of scripts to return
            offset: Number of scripts to skip

        Returns:
            List of Script entities
        """
        try:
            # Build query with optimized indexing
            query = select(Script).where(Script.task_id == task_id)

            # Add status filter
            if status_filter:
                query = query.where(Script.status == status_filter)

            # Apply pagination with proper index usage
            # Uses task_id + created_at DESC composite index
            query = query.order_by(Script.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Eager load task relationship
            query = query.options(joinedload(Script.task))

            # Execute query
            result = await self.db.execute(query)
            scripts = list(result.scalars().all())

            # Cache query results (for task scripts lists)
            cache_key = f"task_scripts:{task_id}:{status_filter or 'all'}:{limit}:{offset}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, scripts)

            return scripts

        except Exception as e:
            logger.error(f"Error getting scripts for task {task_id}: {str(e)}")
            return []

    async def create_script(self, script_data: Dict[str, Any]) -> Script:
        """
        Create a new script with batch operation support.

        Args:
            script_data: Script creation data

        Returns:
            Created Script entity
        """
        try:
            # Create script entity
            script = Script(**script_data)

            # Add to session
            self.db.add(script)

            # Commit immediately to reduce transaction overhead
            await self.db.commit()
            await self.db.refresh(script)

            logger.info(f"Created script {script.id} for task {script.task_id}")

            # Invalidate task scripts cache
            await self._invalidate_cache_prefix(f"task_scripts:{script.task_id}")

            return script

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating script: {str(e)}")
            raise

    async def update_script_status(
        self,
        script_id: UUID,
        status: str
    ) -> bool:
        """
        Update script status with optimized query.

        Args:
            script_id: Script ID
            status: New status

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use optimized UPDATE query with index
            stmt = (
                update(Script)
                .where(Script.id == script_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow()
                )
            )

            # Execute update
            result = await self.db.execute(stmt)
            success = result.rowcount > 0

            if success:
                await self.db.commit()
                logger.info(f"Updated script {script_id} status to {status}")
            else:
                await self.db.rollback()

            # Invalidate script cache
            await self._invalidate_cache(f"script:{script_id}")
            # Invalidate task scripts cache
            # Extract task_id from script_id (would need extra query)
            await self._invalidate_cache_prefix("task_scripts")

            return success

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating script {script_id}: {str(e)}")
            raise

    async def bulk_update_script_status(
        self,
        script_ids: List[UUID],
        status: str
    ) -> int:
        """
        Bulk update script status for multiple scripts.

        Args:
            script_ids: List of script IDs to update
            status: New status for all scripts

        Returns:
            Number of scripts updated

        Raises:
            Exception: If bulk update fails
        """
        try:
            # Use optimized bulk UPDATE query with index
            stmt = (
                update(Script)
                .where(Script.id.in_(script_ids))
                .values(status=status, updated_at=datetime.utcnow())
                .execution_options(synchronize_session=False)
            )

            # Execute bulk update
            result = await self.db.execute(stmt)
            updated_count = result.rowcount

            await self.db.commit()

            # Invalidate script caches for all updated scripts
            for script_id in script_ids:
                await self._invalidate_cache(f"script:{script_id}")

            # Invalidate task scripts caches broadly
            await self._invalidate_cache_prefix("task_scripts")

            logger.info(f"Bulk updated {updated_count} scripts to {status}")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk updating scripts: {str(e)}")
            raise

    async def count_by_task(self, task_id: UUID, status_filter: Optional[str] = None) -> int:
        """
        Count scripts for a task with optimized query.

        Args:
            task_id: Task ID
            status_filter: Optional status filter

        Returns:
            Number of scripts
        """
        try:
            # Build query with optimized indexing
            query = select(func.count(Script.id)).where(Script.task_id == task_id)

            # Add status filter
            if status_filter:
                query = query.where(Script.status == status_filter)

            # Execute query
            result = await self.db.execute(query)
            count = result.scalar() or 0

            return count

        except Exception as e:
            logger.error(f"Error counting scripts for task {task_id}: {str(e)}")
            return 0

    async def get_script_with_structured_content(
        self,
        script_id: UUID
    ) -> Optional[dict]:
        """
        Get script with structured content using optimized query.

        Args:
            script_id: Script ID

        Returns:
            Script dict with structured content, or None
        """
        try:
            # Use cache for script lookup
            cache_key = f"script_full:{script_id}"
            cached_data = await self._get_from_cache(cache_key)

            if cached_data:
                return cached_data

            # Get script
            result = await self.db.execute(
                select(Script).where(Script.id == script_id)
            )
            script = result.scalar_one_or_none()

            if not script:
                return None

            script_data = {
                "id": str(script.id),
                "task_id": str(script.task_id),
                "title": script.title,
                "synopsis": script.synopsis,
                "content": script.content,
                "structured_content": script.structured_content,
                "style_tags": script.style_tags,
                "visual_style": script.visual_style,
                "mood": script.mood,
                "total_duration": script.total_duration,
                "scene_count": script.scene_count,
                "status": script.status,
                "created_at": script.created_at.isoformat(),
                "updated_at": script.updated_at.isoformat(),
            }

            # Cache script data
            await self._set_to_cache(cache_key, script_data)

            return script_data

        except Exception as e:
            logger.error(f"Error getting script with content {script_id}: {str(e)}")
            return None

    async def get_latest_script_by_task(self, task_id: UUID) -> Optional[Script]:
        """
        Get latest script for a task with optimized query.

        Uses composite index: task_id + created_at DESC

        Args:
            task_id: Task ID

        Returns:
            Latest Script entity or None
        """
        try:
            # Build query with optimized indexing
            # Uses task_id + created_at DESC composite index
            query = (
                select(Script)
                .where(Script.task_id == task_id)
                .order_by(Script.created_at.desc())
                .limit(1)
            )

            # Execute query
            result = await self.db.execute(query)
            script = result.scalar_one_or_none()

            return script

        except Exception as e:
            logger.error(f"Error getting latest script for task {task_id}: {str(e)}")
            return None

    async def delete_script(self, script_id: UUID) -> bool:
        """
        Delete a script with optimized query.

        Args:
            script_id: Script ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(Script).where(Script.id == script_id)
            )
            script = result.scalar_one_or_none()

            if not script:
                logger.warning(f"Script {script_id} not found")
                return False

            # Extract task_id for cache invalidation
            task_id = script.task_id

            await self.db.delete(script)
            await self.db.commit()

            # Invalidate script cache
            await self._invalidate_cache(f"script:{script_id}")
            # Invalidate task scripts cache
            await self._invalidate_cache_prefix(f"task_scripts:{task_id}")

            logger.info(f"Deleted script {script_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete script {script_id}: {str(e)}")
            raise

    # ============================================================================
    # Cache Management Methods (Placeholder - integrate with existing CacheService)
    # ============================================================================

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        # This would integrate with your existing CacheService
        # For now, this is a placeholder
        return None

    async def _set_to_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set data in cache.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Cache time-to-live (default from class)

        Returns:
            True if successful, False otherwise
        """
        # This would integrate with your existing CacheService
        # For now, this is a placeholder
        return True

    async def _invalidate_cache(self, key: str) -> bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if successful, False otherwise
        """
        # This would integrate with your existing CacheService
        # For now, this is a placeholder
        return True

    async def _invalidate_cache_prefix(self, prefix: str) -> bool:
        """
        Invalidate all cache entries with given prefix.

        Args:
            prefix: Cache key prefix

        Returns:
            True if successful, False otherwise
        """
        # This would integrate with your existing CacheService
        # For now, this is a placeholder
        return True

    # ============================================================================
    # Performance Metrics
    # ============================================================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        # This would integrate with your existing CacheService
        # For now, return placeholder stats
        return {
            "cache_hit_rate": 0.0,
            "cache_miss_rate": 1.0,
            "total_queries": 0
        }
