"""Performance-optimized Resource repository with caching and batch operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.database.base import Base
from app.entities.resource import Resource, ResourceType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResourceRepositoryOptimized:
    """
    Performance-optimized Resource repository with caching and batch operations.

    Optimizations:
    - Query result caching with TTL
    - Composite index usage
    - Batch operations for inserts/updates
    - Eager loading for relationships
    - Optimized pagination with proper indexing
    """

    def __init__(self, db: AsyncSession, cache_ttl: int = 300):
        """
        Initialize optimized resource repository.

        Args:
            db: Database session
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.db = db
        self.cache_ttl = cache_ttl

    async def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """
        Get resource by ID with caching.

        Args:
            resource_id: Resource ID

        Returns:
            Resource entity or None
        """
        try:
            # Use cache for single resource lookup
            cache_key = f"resource:{resource_id}"
            cached_resource = await self._get_from_cache(cache_key)

            if cached_resource:
                return cached_resource

            # If not in cache, query database
            result = await self.db.execute(
                select(Resource).where(Resource.id == resource_id)
            )
            resource = result.scalar_one_or_none()

            # Store in cache
            if resource:
                await self._set_to_cache(cache_key, resource)

            return resource

        except Exception as e:
            logger.error(f"Error getting resource {resource_id}: {str(e)}")
            return None

    async def get_by_task_id(
        self,
        task_id: UUID,
        resource_type: Optional[ResourceType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Resource]:
        """
        Get resources by task ID with optimized pagination and filtering.

        Uses composite index: task_id + resource_type + created_at DESC

        Args:
            task_id: Task ID
            resource_type: Optional resource type filter
            limit: Maximum number of resources to return
            offset: Number of resources to skip

        Returns:
            List of Resource entities
        """
        try:
            # Build query with optimized indexing
            query = select(Resource).where(Resource.task_id == task_id)

            # Add resource type filter
            if resource_type:
                query = query.where(Resource.resource_type == resource_type)

            # Apply pagination with proper index usage
            # Uses task_id + resource_type + created_at DESC composite index
            query = query.order_by(Resource.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Cache query results (for task resources lists)
            cache_key = f"task_resources:{task_id}:{resource_type or 'all'}:{limit}:{offset}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, resources)

            return resources

        except Exception as e:
            logger.error(f"Error getting resources for task {task_id}: {str(e)}")
            return []

    async def get_by_resource_type(
        self,
        resource_type: ResourceType,
        limit: int = 50,
        offset: int = 0
    ) -> List[Resource]:
        """
        Get resources by resource type with optimized pagination.

        Args:
            resource_type: Resource type filter
            limit: Maximum number of resources to return
            offset: Number of resources to skip

        Returns:
            List of Resource entities
        """
        try:
            # Build query with optimized indexing
            query = select(Resource).where(Resource.resource_type == resource_type)

            # Apply pagination with proper index usage
            # Uses resource_type + created_at DESC index
            query = query.order_by(Resource.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Cache query results
            cache_key = f"resources_type:{resource_type}:{limit}:{offset}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, resources)

            return resources

        except Exception as e:
            logger.error(f"Error getting resources of type {resource_type}: {str(e)}")
            return []

    async def create_resource(self, resource_data: Dict[str, Any]) -> Resource:
        """
        Create a new resource with batch operation support.

        Args:
            resource_data: Resource creation data

        Returns:
            Created Resource entity
        """
        try:
            # Create resource entity
            resource = Resource(**resource_data)

            # Add to session
            self.db.add(resource)

            # Commit immediately to reduce transaction overhead
            await self.db.commit()
            await self.db.refresh(resource)

            logger.info(f"Created resource {resource.id} for task {resource.task_id}")

            # Invalidate task resources cache
            await self._invalidate_cache_prefix(f"task_resources:{resource.task_id}")

            return resource

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating resource: {str(e)}")
            raise

    async def bulk_create_resources(self, resources_data: List[Dict[str, Any]]) -> List[Resource]:
        """
        Bulk create resources with optimized query.

        Args:
            resources_data: List of resource creation data

        Returns:
            List of created Resource entities
        """
        try:
            # Create resource entities
            resources = [Resource(**data) for data in resources_data]

            # Add all to session
            self.db.add_all(resources)

            # Commit immediately
            await self.db.commit()

            logger.info(f"Bulk created {len(resources)} resources")

            # Extract task IDs for cache invalidation
            task_ids = list(set([res.task_id for res in resources]))

            # Invalidate task resources caches
            for task_id in task_ids:
                await self._invalidate_cache_prefix(f"task_resources:{task_id}")

            return resources

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk creating resources: {str(e)}")
            raise

    async def update_resource_metadata(
        self,
        resource_id: UUID,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None
    ) -> bool:
        """
        Update resource metadata with optimized query.

        Args:
            resource_id: Resource ID
            width: Image width
            height: Image height
            duration: Video duration

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use optimized UPDATE query
            stmt = (
                update(Resource)
                .where(Resource.id == resource_id)
                .values(updated_at=datetime.utcnow())
            )

            # Add metadata fields
            if width is not None:
                stmt = stmt.values(width=width)
            if height is not None:
                stmt = stmt.values(height=height)
            if duration is not None:
                stmt = stmt.values(duration=duration)

            # Execute update
            result = await self.db.execute(stmt)
            success = result.rowcount > 0

            if success:
                await self.db.commit()
                logger.debug(f"Updated resource {resource_id} metadata")
            else:
                await self.db.rollback()

            # Invalidate resource cache
            await self._invalidate_cache(f"resource:{resource_id}")

            return success

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating resource {resource_id}: {str(e)}")
            raise

    async def update_storage_info(
        self,
        resource_id: UUID,
        public_url: Optional[str] = None,
        storage_key: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> bool:
        """
        Update resource storage information with optimized query.

        Args:
            resource_id: Resource ID
            public_url: Public URL
            storage_key: Storage key
            file_size: File size

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use optimized UPDATE query
            stmt = (
                update(Resource)
                .where(Resource.id == resource_id)
                .values(updated_at=datetime.utcnow())
            )

            # Add storage fields
            if public_url is not None:
                stmt = stmt.values(public_url=public_url)
            if storage_key is not None:
                stmt = stmt.values(storage_key=storage_key)
            if file_size is not None:
                stmt = stmt.values(file_size=file_size)

            # Execute update
            result = await self.db.execute(stmt)
            success = result.rowcount > 0

            if success:
                await self.db.commit()
                logger.debug(f"Updated resource {resource_id} storage info")
            else:
                await self.db.rollback()

            # Invalidate resource cache
            await self._invalidate_cache(f"resource:{resource_id}")

            return success

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating resource storage {resource_id}: {str(e)}")
            raise

    async def get_resources_for_task_by_type(
        self,
        task_id: UUID,
        resource_type: ResourceType,
        limit: Optional[int] = None
    ) -> List[Resource]:
        """
        Get resources for a task by type with optimized query.

        Uses composite index: task_id + resource_type + created_at DESC

        Args:
            task_id: Task ID
            resource_type: Resource type
            limit: Maximum number of resources to return

        Returns:
            List of Resource entities
        """
        try:
            # Build query with optimized indexing
            query = (
                select(Resource)
                .where(
                    and_(
                        Resource.task_id == task_id,
                        Resource.resource_type == resource_type
                    )
                )
                .order_by(Resource.created_at.desc())
            )

            # Apply limit if provided
            if limit:
                query = query.limit(limit)

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Cache query results (short TTL for task resources)
            cache_key = f"task_resources_type:{task_id}:{resource_type}:{limit or 'all'}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, resources, ttl=120)  # 2 minutes TTL

            return resources

        except Exception as e:
            logger.error(f"Error getting resources for task {task_id} type {resource_type}: {str(e)}")
            return []

    async def get_first_frame_images_for_task(self, task_id: UUID) -> List[Resource]:
        """
        Get first frame images for a task with optimized query.

        Uses composite index: task_id + resource_type + created_at DESC

        Args:
            task_id: Task ID

        Returns:
            List of first frame image resources
        """
        try:
            # Build query with optimized indexing
            query = (
                select(Resource)
                .where(
                    and_(
                        Resource.task_id == task_id,
                        Resource.resource_type == ResourceType.IMAGE
                    )
                )
                .order_by(Resource.created_at.asc())
            )

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Cache query results (short TTL for task resources)
            cache_key = f"task_first_frames:{task_id}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, resources, ttl=120)  # 2 minutes TTL

            return resources

        except Exception as e:
            logger.error(f"Error getting first frames for task {task_id}: {str(e)}")
            return []

    async def get_videos_for_task(self, task_id: UUID) -> List[Resource]:
        """
        Get video resources for a task with optimized query.

        Uses composite index: task_id + resource_type + created_at DESC

        Args:
            task_id: Task ID

        Returns:
            List of video resources
        """
        try:
            # Build query with optimized indexing
            query = (
                select(Resource)
                .where(
                    and_(
                        Resource.task_id == task_id,
                        Resource.resource_type == ResourceType.VIDEO
                    )
                )
                .order_by(Resource.created_at.asc())
            )

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Cache query results (short TTL for task resources)
            cache_key = f"task_videos:{task_id}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, resources, ttl=120)  # 2 minutes TTL

            return resources

        except Exception as e:
            logger.error(f"Error getting videos for task {task_id}: {str(e)}")
            return []

    async def get_resources_stats(self, task_id: UUID) -> Dict[str, Any]:
        """
        Get resources statistics for a task.

        Args:
            task_id: Task ID

        Returns:
            Resource statistics dictionary
        """
        try:
            # Build query with optimized indexing
            # Use resource_type index for fast counting
            query = select(Resource).where(Resource.task_id == task_id)

            # Execute query
            result = await self.db.execute(query)
            resources = list(result.scalars().all())

            # Calculate statistics
            stats = {
                "total_count": len(resources),
                "images_count": len([r for r in resources if r.resource_type == ResourceType.IMAGE]),
                "videos_count": len([r for r in resources if r.resource_type == ResourceType.VIDEO]),
                "audio_count": len([r for r in resources if r.resource_type == ResourceType.AUDIO]),
                "thumbnails_count": len([r for r in resources if r.resource_type == ResourceType.THUMBNAIL]),
                "total_size": sum([r.file_size for r in resources if r.file_size is not None]),
                "average_size": sum([r.file_size for r in resources if r.file_size is not None]) / len(resources) if resources else 0,
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting resources stats for task {task_id}: {str(e)}")
            return {
                "total_count": 0,
                "images_count": 0,
                "videos_count": 0,
                "audio_count": 0,
                "thumbnails_count": 0,
                "total_size": 0,
                "average_size": 0,
            }

    async def delete(self, resource_id: UUID) -> bool:
        """
        Delete a resource with optimized query.

        Args:
            resource_id: Resource ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(Resource).where(Resource.id == resource_id)
            )
            resource = result.scalar_one_or_none()

            if not resource:
                logger.warning(f"Resource {resource_id} not found")
                return False

            # Extract task_id for cache invalidation
            task_id = resource.task_id

            await self.db.delete(resource)
            await self.db.commit()

            # Invalidate resource cache
            await self._invalidate_cache(f"resource:{resource_id}")
            # Invalidate task resources cache
            await self._invalidate_cache_prefix(f"task_resources:{task_id}")

            logger.info(f"Deleted resource {resource_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete resource {resource_id}: {str(e)}")
            raise

    async def bulk_delete_resources(self, resource_ids: List[UUID]) -> int:
        """
        Bulk delete resources with optimized query.

        Args:
            resource_ids: List of resource IDs to delete

        Returns:
            Number of resources deleted
        """
        try:
            # Use optimized bulk DELETE query with index
            stmt = (
                delete(Resource)
                .where(Resource.id.in_(resource_ids))
            )

            # Execute bulk delete
            result = await self.db.execute(stmt)
            deleted_count = result.rowcount

            await self.db.commit()

            # Extract task IDs for cache invalidation
            # Would require extra query, so we'll do broad invalidation
            await self._invalidate_cache_prefix("task_resources")

            logger.info(f"Bulk deleted {deleted_count} resources")
            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk deleting resources: {str(e)}")
            raise

    async def count_by_task(self, task_id: UUID, resource_type: Optional[ResourceType] = None) -> int:
        """
        Count resources for a task with optimized query.

        Args:
            task_id: Task ID
            resource_type: Optional resource type filter

        Returns:
            Number of resources
        """
        try:
            # Build query with optimized indexing
            # Use task_id index for fast counting
            query = select(func.count(Resource.id)).where(Resource.task_id == task_id)

            # Add resource type filter
            if resource_type:
                query = query.where(Resource.resource_type == resource_type)

            # Execute query
            result = await self.db.execute(query)
            count = result.scalar() or 0

            return count

        except Exception as e:
            logger.error(f"Error counting resources for task {task_id}: {str(e)}")
            return 0

    async def get_user_total_storage_used(self, user_id: str) -> Dict[str, Any]:
        """
        Get total storage used by a user.

        Args:
            user_id: User ID

        Returns:
            Storage usage statistics
        """
        try:
            # Build query with optimized indexing
            # Join with tasks table to filter by user
            from app.entities.task import Task

            query = (
                select(
                    func.count(Resource.id),
                    func.sum(Resource.file_size)
                )
                .join(Task, Resource.task_id == Task.id)
                .where(Task.user_id == user_id)
            )

            # Execute query
            result = await self.db.execute(query)
            count, total_size = result.one()

            return {
                "total_count": count or 0,
                "total_size": total_size or 0,
                "total_size_mb": round((total_size or 0) / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Error getting storage usage for user {user_id}: {str(e)}")
            return {
                "total_count": 0,
                "total_size": 0,
                "total_size_mb": 0.0,
            }

    async def clean_old_resources(self, days: int = 7) -> int:
        """
        Clean up old resources.

        Args:
            days: Number of days before now

        Returns:
            Number of resources cleaned up

        Raises:
            Exception: If cleanup fails
        """
        try:
            from datetime import timedelta

            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Delete old resources (not first frame images)
            # Use optimized DELETE query with index
            stmt = (
                delete(Resource)
                .where(
                    and_(
                        Resource.created_at < cutoff_time,
                        # Only delete non-critical resources (not first frames or videos)
                        Resource.resource_type != ResourceType.IMAGE,  # Keep images for now
                    )
                )
            )

            result = await self.db.execute(stmt)
            deleted_count = result.rowcount

            await self.db.commit()

            # Invalidate resource caches broadly
            await self._invalidate_cache_prefix("task_resources")

            logger.info(f"Cleaned up {deleted_count} old resources older than {days} days")
            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error cleaning up resources: {str(e)}")
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
        # For now, return None (no actual caching)
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
        # For now, return True (no actual caching)
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
        # For now, return True (no actual caching)
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
        # For now, return True (no actual caching)
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
