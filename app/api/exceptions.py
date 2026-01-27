"""Custom exceptions for the Video Agent API."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class VideoAgentException(Exception):
    """Base exception for Video Agent errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Video Agent exception.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
        """
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException for FastAPI."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.code,
                "message": self.message,
                "details": self.details,
            },
        )

    @property
    def status_code(self) -> int:
        """Get HTTP status code for this exception."""
        return status.HTTP_500_INTERNAL_SERVER_ERROR


class TaskNotFoundException(VideoAgentException):
    """Task not found exception."""

    def __init__(self, task_id: str):
        """
        Initialize exception.

        Args:
            task_id: Task ID that was not found
        """
        super().__init__(
            message=f"Task {task_id} not found",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id},
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND


class TaskValidationException(VideoAgentException):
    """Task validation failed exception."""

    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Validation error message
            field: Field that failed validation
        """
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_422_UNPROCESSABLE_ENTITY


class TaskStateException(VideoAgentException):
    """Invalid task state exception."""

    def __init__(
        self,
        task_id: str,
        current_status: str,
        desired_action: str,
    ):
        """
        Initialize exception.

        Args:
            task_id: Task ID
            current_status: Current task status
            desired_action: Action that was attempted
        """
        super().__init__(
            message=f"Cannot {desired_action} task in {current_status} status",
            code="INVALID_STATE",
            details={
                "task_id": task_id,
                "current_status": current_status,
                "desired_action": desired_action,
            },
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST


class AgentExecutionException(VideoAgentException):
    """Agent execution failed exception."""

    def __init__(
        self,
        agent_name: str,
        task_id: str,
        error: str,
    ):
        """
        Initialize exception.

        Args:
            agent_name: Name of the agent that failed
            task_id: Task ID
            error: Error message
        """
        super().__init__(
            message=f"{agent_name} failed for task {task_id}: {error}",
            code="AGENT_EXECUTION_ERROR",
            details={
                "agent": agent_name,
                "task_id": task_id,
                "error": error,
            },
        )


class ModelProviderException(VideoAgentException):
    """Model provider error exception."""

    def __init__(
        self,
        provider: str,
        model_type: str,
        error: str,
    ):
        """
        Initialize exception.

        Args:
            provider: Provider name (e.g., "openai")
            model_type: Model type (e.g., "llm", "image")
            error: Error message
        """
        super().__init__(
            message=f"{provider} {model_type} provider error: {error}",
            code="MODEL_PROVIDER_ERROR",
            details={
                "provider": provider,
                "model_type": model_type,
                "error": error,
            },
        )


class StorageException(VideoAgentException):
    """Storage operation failed exception."""

    def __init__(
        self,
        operation: str,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize exception.

        Args:
            operation: Operation that failed (e.g., "upload", "download")
            path: File path
            error: Error message
        """
        details = {"operation": operation}
        if path:
            details["path"] = path
        if error:
            details["error"] = error

        super().__init__(
            message=f"Storage {operation} failed",
            code="STORAGE_ERROR",
            details=details,
        )


class VideoProcessingException(VideoAgentException):
    """Video processing failed exception."""

    def __init__(
        self,
        operation: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize exception.

        Args:
            operation: Operation that failed (e.g., "concatenate", "trim")
            error: Error message
            details: Additional details
        """
        all_details = {"operation": operation, "error": error}
        if details:
            all_details.update(details)

        super().__init__(
            message=f"Video processing {operation} failed: {error}",
            code="VIDEO_PROCESSING_ERROR",
            details=all_details,
        )


class RateLimitException(VideoAgentException):
    """Rate limit exceeded exception."""

    def __init__(
        self,
        limit: int,
        window: int,
    ):
        """
        Initialize exception.

        Args:
            limit: Rate limit
            window: Time window in seconds
        """
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window} seconds",
            code="RATE_LIMIT_EXCEEDED",
            details={
                "limit": limit,
                "window": window,
            },
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_429_TOO_MANY_REQUESTS


class AuthenticationException(VideoAgentException):
    """Authentication failed exception."""

    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize exception.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_401_UNAUTHORIZED


class AuthorizationException(VideoAgentException):
    """Authorization failed exception."""

    def __init__(
        self,
        resource: str,
        action: str,
    ):
        """
        Initialize exception.

        Args:
            resource: Resource being accessed
            action: Action being attempted
        """
        super().__init__(
            message=f"Not authorized to {action} {resource}",
            code="AUTHORIZATION_ERROR",
            details={
                "resource": resource,
                "action": action,
            },
        )

    @property
    def status_code(self) -> int:
        return status.HTTP_403_FORBIDDEN


class ConfigurationException(VideoAgentException):
    """Configuration error exception."""

    def __init__(
        self,
        config_key: str,
        message: str,
    ):
        """
        Initialize exception.

        Args:
            config_key: Configuration key
            message: Error message
        """
        super().__init__(
            message=f"Configuration error for {config_key}: {message}",
            code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
            },
        )


__all__ = [
    "VideoAgentException",
    "TaskNotFoundException",
    "TaskValidationException",
    "TaskStateException",
    "AgentExecutionException",
    "ModelProviderException",
    "StorageException",
    "VideoProcessingException",
    "RateLimitException",
    "AuthenticationException",
    "AuthorizationException",
    "ConfigurationException",
]
