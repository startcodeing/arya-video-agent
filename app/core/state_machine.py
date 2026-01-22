"""State machine for task status transitions."""

from typing import Dict, List, Optional, Set
from app.entities.task import TaskStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStateMachine:
    """
    State machine for managing task status transitions.

    Defines valid transitions between task states and enforces state transition rules.
    """

    # Define valid state transitions
    # Format: {from_state: [to_states]}
    VALID_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        # Normal flow: PENDING -> STYLE_DETECTION -> STORY_GENERATION -> ...
        TaskStatus.PENDING: {
            TaskStatus.STYLE_DETECTION,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.STYLE_DETECTION: {
            TaskStatus.STORY_GENERATION,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        TaskStatus.STORY_GENERATION: {
            TaskStatus.STORYBOARD_BREAKDOWN,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        TaskStatus.STORYBOARD_BREAKDOWN: {
            TaskStatus.IMAGE_GENERATION,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        TaskStatus.IMAGE_GENERATION: {
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        TaskStatus.VIDEO_GENERATION: {
            TaskStatus.COMPOSING,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        TaskStatus.COMPOSING: {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RETRYING,
        },
        # Terminal states
        TaskStatus.COMPLETED: set(),  # No transitions from completed
        TaskStatus.CANCELLED: set(),  # No transitions from cancelled
        # Failed can transition to RETRYING
        TaskStatus.FAILED: {
            TaskStatus.RETRYING,
            TaskStatus.CANCELLED,
        },
        # Retrying can transition back to any retryable state
        TaskStatus.RETRYING: {
            TaskStatus.STYLE_DETECTION,
            TaskStatus.STORY_GENERATION,
            TaskStatus.STORYBOARD_BREAKDOWN,
            TaskStatus.IMAGE_GENERATION,
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.COMPOSING,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
    }

    # Define retryable states (can be retried after failure)
    RETRYABLE_STATES: Set[TaskStatus] = {
        TaskStatus.STYLE_DETECTION,
        TaskStatus.STORY_GENERATION,
        TaskStatus.STORYBOARD_BREAKDOWN,
        TaskStatus.IMAGE_GENERATION,
        TaskStatus.VIDEO_GENERATION,
        TaskStatus.COMPOSING,
    }

    # Define terminal states
    TERMINAL_STATES: Set[TaskStatus] = {
        TaskStatus.COMPLETED,
        TaskStatus.CANCELLED,
    }

    # Define processing states (active, not terminal)
    PROCESSING_STATES: Set[TaskStatus] = {
        TaskStatus.STYLE_DETECTION,
        TaskStatus.STORY_GENERATION,
        TaskStatus.STORYBOARD_BREAKDOWN,
        TaskStatus.IMAGE_GENERATION,
        TaskStatus.VIDEO_GENERATION,
        TaskStatus.COMPOSING,
    }

    @classmethod
    def validate_transition(
        cls,
        current_status: TaskStatus,
        new_status: TaskStatus
    ) -> bool:
        """
        Validate if a state transition is allowed.

        Args:
            current_status: Current task status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        try:
            # Get valid transitions for current state
            valid_transitions = cls.VALID_TRANSITIONS.get(current_status, set())

            # Check if new status is in valid transitions
            if new_status in valid_transitions:
                logger.debug(
                    f"Valid transition: {current_status.value} -> {new_status.value}"
                )
                return True

            logger.warning(
                f"Invalid transition: {current_status.value} -> {new_status.value}"
            )
            return False

        except Exception as e:
            logger.error(f"Error validating transition: {e}")
            return False

    @classmethod
    def can_transition(
        cls,
        current_status: TaskStatus,
        new_status: TaskStatus
    ) -> bool:
        """
        Alias for validate_transition for backward compatibility.
        """
        return cls.validate_transition(current_status, new_status)

    @classmethod
    def get_valid_transitions(cls, current_status: TaskStatus) -> List[TaskStatus]:
        """
        Get all valid transitions from a given state.

        Args:
            current_status: Current task status

        Returns:
            List of valid target statuses
        """
        return list(cls.VALID_TRANSITIONS.get(current_status, set()))

    @classmethod
    def is_terminal(cls, status: TaskStatus) -> bool:
        """
        Check if a status is a terminal state.

        Args:
            status: Task status to check

        Returns:
            True if status is terminal
        """
        return status in cls.TERMINAL_STATES

    @classmethod
    def is_processing(cls, status: TaskStatus) -> bool:
        """
        Check if a status is a processing state.

        Args:
            status: Task status to check

        Returns:
            True if status is a processing state
        """
        return status in cls.PROCESSING_STATES

    @classmethod
    def is_retryable(cls, status: TaskStatus) -> bool:
        """
        Check if a status can be retried after failure.

        Args:
            status: Task status to check

        Returns:
            True if status is retryable
        """
        return status in cls.RETRYABLE_STATES

    @classmethod
    def get_retry_state(cls, failed_status: TaskStatus) -> Optional[TaskStatus]:
        """
        Determine which state to retry from after a failure.

        Args:
            failed_status: The status that failed

        Returns:
            The state to transition to for retry, or None if not retryable
        """
        if failed_status in cls.RETRYABLE_STATES:
            return failed_status
        return None

    @classmethod
    def get_next_state(cls, current_status: TaskStatus) -> Optional[TaskStatus]:
        """
        Get the next state in the normal pipeline flow.

        Args:
            current_status: Current task status

        Returns:
            Next status in pipeline, or None if current is terminal
        """
        pipeline_flow = [
            TaskStatus.PENDING,
            TaskStatus.STYLE_DETECTION,
            TaskStatus.STORY_GENERATION,
            TaskStatus.STORYBOARD_BREAKDOWN,
            TaskStatus.IMAGE_GENERATION,
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.COMPOSING,
            TaskStatus.COMPLETED,
        ]

        try:
            current_index = pipeline_flow.index(current_status)
            if current_index + 1 < len(pipeline_flow):
                return pipeline_flow[current_index + 1]
        except ValueError:
            pass

        return None

    @classmethod
    def get_previous_state(cls, current_status: TaskStatus) -> Optional[TaskStatus]:
        """
        Get the previous state in the normal pipeline flow.

        Args:
            current_status: Current task status

        Returns:
            Previous status in pipeline, or None if current is PENDING
        """
        pipeline_flow = [
            TaskStatus.PENDING,
            TaskStatus.STYLE_DETECTION,
            TaskStatus.STORY_GENERATION,
            TaskStatus.STORYBOARD_BREAKDOWN,
            TaskStatus.IMAGE_GENERATION,
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.COMPOSING,
            TaskStatus.COMPLETED,
        ]

        try:
            current_index = pipeline_flow.index(current_status)
            if current_index > 0:
                return pipeline_flow[current_index - 1]
        except ValueError:
            pass

        return None

    @classmethod
    def can_proceed(cls, current_status: TaskStatus) -> bool:
        """
        Check if task can proceed to next state.

        Args:
            current_status: Current task status

        Returns:
            True if task can proceed
        """
        if cls.is_terminal(current_status):
            return False

        next_state = cls.get_next_state(current_status)
        return next_state is not None

    @classmethod
    def transition(
        cls,
        current_status: TaskStatus,
        new_status: TaskStatus,
        raise_on_invalid: bool = False
    ) -> bool:
        """
        Attempt to transition to a new state.

        Args:
            current_status: Current task status
            new_status: Desired new status
            raise_on_invalid: If True, raise exception on invalid transition

        Returns:
            True if transition succeeded

        Raises:
            ValueError: If transition is invalid and raise_on_invalid is True
        """
        if not cls.validate_transition(current_status, new_status):
            if raise_on_invalid:
                raise ValueError(
                    f"Invalid state transition: {current_status.value} -> {new_status.value}"
                )
            return False

        logger.info(
            f"State transition: {current_status.value} -> {new_status.value}"
        )
        return True


# Convenience functions for common operations
def can_transition_to(current_status: TaskStatus, new_status: TaskStatus) -> bool:
    """Check if transition to new status is allowed."""
    return TaskStateMachine.can_transition(current_status, new_status)


def get_next_pipeline_state(current_status: TaskStatus) -> Optional[TaskStatus]:
    """Get the next state in the normal pipeline."""
    return TaskStateMachine.get_next_state(current_status)


def is_terminal_state(status: TaskStatus) -> bool:
    """Check if status is a terminal state."""
    return TaskStateMachine.is_terminal(status)


def is_processing_state(status: TaskStatus) -> bool:
    """Check if status is a processing state."""
    return TaskStateMachine.is_processing(status)


__all__ = [
    "TaskStateMachine",
    "can_transition_to",
    "get_next_pipeline_state",
    "is_terminal_state",
    "is_processing_state",
]
