"""Redis cache configuration and cache key management."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


class CacheNamespace(str, Enum):
    """Cache namespace enumeration for organizing cache keys.

    Namespaces:
    - TASKS: Task-related data
    - CONVERSATIONS: Conversation data
    - SCRIPTS: Script data
    - STORYBOARDS: Storyboard data
    - RESOURCES: Resource data
    - API: API responses
    - SESSIONS: Session data
    - USER: User data
    - AGENT: Agent state data
    """

    TASKS = "tasks"
    CONVERSATIONS = "conversations"
    SCRIPTS = "scripts"
    STORYBOARDS = "storyboards"
    RESOURCES = "resources"
    API = "api"
    SESSIONS = "sessions"
    USER = "user"
    AGENT = "agent"


class CacheVersion(str, Enum):
    """Cache version enumeration for cache invalidation."""

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


class CacheTTL(str, Enum):
    """Cache time-to-live enumeration for different cache types.

    Values are in seconds.

    SHORT = "60"          # 1 minute
    MEDIUM = "300"        # 5 minutes
    LONG = "900"          # 15 minutes
    VERY_LONG = "3600"    # 1 hour
    DAY = "86400"        # 24 hours
    WEEK = "604800"       # 7 days
    MONTH = "2592000"    # 30 days
    """


class CacheKeyGenerator:
    """
    Cache key generator with naming convention and version control.

    Naming convention:
    {namespace}:{version}:{key}

    Examples:
    - tasks:v1:task_123
    - conversations:v1:user_abc123:session_xyz
    - api:v1:conversations:list:user_abc123
    """

    CACHE_VERSION = CacheVersion.V1
    DEFAULT_TTL = CacheTTL.MEDIUM

    @staticmethod
    def generate_key(
        namespace: CacheNamespace,
        key: str,
        version: Optional[CacheVersion] = None
    ) -> str:
        """
        Generate a cache key with namespace and version.

        Args:
            namespace: Cache namespace
            key: Cache key
            version: Cache version (default: V1)

        Returns:
            Formatted cache key
        """
        cache_version = version or CacheKeyGenerator.CACHE_VERSION
        return f"{namespace.value}:{cache_version}:{key}"

    @staticmethod
    def generate_task_key(task_id: str) -> str:
        """
        Generate cache key for task data.

        Args:
            task_id: Task ID

        Returns:
            Cache key for task
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.TASKS,
            f"task_{task_id}"
        )

    @staticmethod
    def generate_user_tasks_key(
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> str:
        """
        Generate cache key for user tasks list.

        Args:
            user_id: User ID
            status: Optional task status filter
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip

        Returns:
            Cache key for user tasks list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.TASKS,
            f"user_tasks:{user_id}:{status or 'all'}:{limit}:{offset}"
        )

    @staticmethod
    def generate_pending_tasks_key(
        priority: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """
        Generate cache key for pending tasks list.

        Args:
            priority: Optional task priority filter
            limit: Maximum number of tasks to return

        Returns:
            Cache key for pending tasks list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.TASKS,
            f"pending_tasks:{priority or 'all'}:{limit}"
        )

    @staticmethod
    def generate_conversation_key(conversation_id: str) -> str:
        """
        Generate cache key for conversation data.

        Args:
            conversation_id: Conversation ID

        Returns:
            Cache key for conversation
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.CONVERSATIONS,
            f"conversation_{conversation_id}"
        )

    @staticmethod
    def generate_conversation_messages_key(
        conversation_id: str,
        message_limit: Optional[int] = None
    ) -> str:
        """
        Generate cache key for conversation messages.

        Args:
            conversation_id: Conversation ID
            message_limit: Maximum number of messages to include

        Returns:
            Cache key for conversation messages
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.CONVERSATIONS,
            f"conversation_messages:{conversation_id}:{message_limit or 'all'}"
        )

    @staticmethod
    def generate_user_conversations_key(
        user_id: str,
        active_only: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> str:
        """
        Generate cache key for user conversations list.

        Args:
            user_id: User ID
            active_only: Only return active conversations
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            Cache key for user conversations list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.CONVERSATIONS,
            f"user_conversations:{user_id}:{active_only}:{limit}:{offset}"
        )

    @staticmethod
    def generate_session_key(
        user_id: str,
        session_id: str,
        active_only: bool = True
    ) -> str:
        """
        Generate cache key for session data.

        Args:
            user_id: User ID
            session_id: Session ID
            active_only: Only return active sessions

        Returns:
            Cache key for session data
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.SESSIONS,
            f"session:{user_id}:{session_id}:{active_only}"
        )

    @staticmethod
    def generate_script_key(script_id: str) -> str:
        """
        Generate cache key for script data.

        Args:
            script_id: Script ID

        Returns:
            Cache key for script
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.SCRIPTS,
            f"script_{script_id}"
        )

    @staticmethod
    def generate_task_scripts_key(
        task_id: str,
        status_filter: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> str:
        """
        Generate cache key for task scripts list.

        Args:
            task_id: Task ID
            status_filter: Optional status filter
            limit: Maximum number of scripts to return
            offset: Number of scripts to skip

        Returns:
            Cache key for task scripts list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.SCRIPTS,
            f"task_scripts:{task_id}:{status_filter or 'all'}:{limit}:{offset}"
        )

    @staticmethod
    def generate_storyboard_key(storyboard_id: str) -> str:
        """
        Generate cache key for storyboard data.

        Args:
            storyboard_id: Storyboard ID

        Returns:
            Cache key for storyboard
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.STORYBOARDS,
            f"storyboard_{storyboard_id}"
        )

    @staticmethod
    def generate_task_storyboards_key(
        task_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        Generate cache key for task storyboards list.

        Args:
            task_id: Task ID
            status_filter: Optional status filter
            limit: Maximum number of storyboards to return
            offset: Number of storyboards to skip

        Returns:
            Cache key for task storyboards list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.STORYBOARDS,
            f"task_storyboards:{task_id}:{status_filter or 'all'}:{limit}:{offset}"
        )

    @staticmethod
    def generate_resource_key(resource_id: str) -> str:
        """
        Generate cache key for resource data.

        Args:
            resource_id: Resource ID

        Returns:
            Cache key for resource
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.RESOURCES,
            f"resource_{resource_id}"
        )

    @staticmethod
    def generate_task_resources_key(
        task_id: str,
        resource_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        Generate cache key for task resources list.

        Args:
            task_id: Task ID
            resource_type: Optional resource type filter
            limit: Maximum number of resources to return
            offset: Number of resources to skip

        Returns:
            Cache key for task resources list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.RESOURCES,
            f"task_resources:{task_id}:{resource_type or 'all'}:{limit}:{offset}"
        )

    @staticmethod
    def generate_first_frame_images_key(task_id: str) -> str:
        """
        Generate cache key for task first frame images.

        Args:
            task_id: Task ID

        Returns:
            Cache key for first frame images list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.RESOURCES,
            f"task_first_frames:{task_id}"
        )

    @staticmethod
    def generate_task_videos_key(task_id: str) -> str:
        """
        Generate cache key for task videos.

        Args:
            task_id: Task ID

        Returns:
            Cache key for task videos list
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.RESOURCES,
            f"task_videos:{task_id}"
        )

    @staticmethod
    def generate_api_response_key(
        endpoint: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate cache key for API response.

        Args:
            endpoint: API endpoint path
            params: Request parameters

        Returns:
            Cache key for API response
        """
        # Sort parameters for consistent cache key
        sorted_params = sorted(params.items())
        params_str = "&".join([f"{k}={v}" for k, v in sorted_params])

        return CacheKeyGenerator.generate_key(
            CacheNamespace.API,
            f"response:{endpoint}:{params_str}"
        )

    @staticmethod
    def generate_user_key(user_id: str, data_type: str) -> str:
        """
        Generate cache key for user data.

        Args:
            user_id: User ID
            data_type: Type of user data (e.g., profile, preferences)

        Returns:
            Cache key for user data
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.USER,
            f"user_{data_type}:{user_id}"
        )

    @staticmethod
    def generate_agent_state_key(agent_name: str, task_id: Optional[str] = None) -> str:
        """
        Generate cache key for agent state.

        Args:
            agent_name: Agent name
            task_id: Optional associated task ID

        Returns:
            Cache key for agent state
        """
        return CacheKeyGenerator.generate_key(
            CacheNamespace.AGENT,
            f"agent_state:{agent_name}:{task_id or 'default'}"
        )


class CacheConfig:
    """Cache configuration with TTL settings for different cache types."""

    CACHE_TTLS = {
        # Task cache
        CacheNamespace.TASKS: CacheTTL.MEDIUM,
        CacheNamespace.SCRIPTS: CacheTTL.LONG,
        CacheNamespace.STORYBOARDS: CacheTTL.LONG,
        CacheNamespace.RESOURCES: CacheTTL.MEDIUM,

        # Session and conversation cache
        CacheNamespace.CONVERSATIONS: CacheTTL.LONG,
        CacheNamespace.SESSIONS: CacheTTL.LONG,

        # API cache (short TTL for fast-changing data)
        CacheNamespace.API: CacheTTL.MEDIUM,

        # User data cache (long TTL)
        CacheNamespace.USER: CacheTTL.VERY_LONG,

        # Agent state cache (short TTL)
        CacheNamespace.AGENT: CacheTTL.SHORT,
    }

    @staticmethod
    def get_ttl(namespace: CacheNamespace) -> int:
        """
        Get TTL for a namespace.

        Args:
            namespace: Cache namespace

        Returns:
            TTL in seconds
        """
        return int(CacheConfig.CACHE_TTLS.get(namespace, CacheTTL.MEDIUM))

    @staticmethod
    def get_ttl_for_type(cache_type: str) -> int:
        """
        Get TTL for a cache type.

        Args:
            cache_type: Cache type string (short, medium, long)

        Returns:
            TTL in seconds
        """
        ttl_map = {
            "short": int(CacheTTL.SHORT),
            "medium": int(CacheTTL.MEDIUM),
            "long": int(CacheTTL.LONG),
            "very_long": int(CacheTTL.VERY_LONG),
            "day": int(CacheTTL.DAY),
            "week": int(CacheTTL.WEEK),
            "month": int(CacheTTL.MONTH),
        }
        return ttl_map.get(cache_type, int(CacheTTL.MEDIUM))


class CacheMetadata:
    """Cache metadata for tracking cache entries."""

    def __init__(
        self,
        created_at: datetime,
        ttl: int,
        key: str,
        value_type: str,
        version: str = CacheVersion.V1
    ):
        """
        Initialize cache metadata.

        Args:
            created_at: Cache entry creation time
            ttl: Time-to-live in seconds
            key: Cache key
            value_type: Type of cached value
            version: Cache version
        """
        self.created_at = created_at
        self.ttl = ttl
        self.expires_at = created_at + timedelta(seconds=ttl)
        self.key = key
        self.value_type = value_type
        self.version = version
        self.hit_count = 0
        self.miss_count = 0

    def is_expired(self) -> bool:
        """
        Check if cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.miss_count += 1

    def get_hit_rate(self) -> float:
        """
        Get cache hit rate.

        Returns:
            Hit rate (0.0 to 1.0)
        """
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total

    def get_age(self) -> int:
        """
        Get cache entry age in seconds.

        Returns:
            Age in seconds
        """
        return int((datetime.utcnow() - self.created_at).total_seconds())

    def get_ttl_remaining(self) -> int:
        """
        Get remaining TTL in seconds.

        Returns:
            Remaining TTL in seconds
        """
        return int(max(0, (self.expires_at - datetime.utcnow()).total_seconds()))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert cache metadata to dictionary.

        Returns:
            Cache metadata dictionary
        """
        return {
            "key": self.key,
            "value_type": self.value_type,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl": self.ttl,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.get_hit_rate(),
            "age": self.get_age(),
            "ttl_remaining": self.get_ttl_remaining(),
            "is_expired": self.is_expired(),
        }
