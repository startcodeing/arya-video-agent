"""Unit tests for TaskStateMachine."""

import pytest
from app.core.state_machine import (
    TaskStateMachine,
    can_transition_to,
    get_next_pipeline_state,
    is_terminal_state,
    is_processing_state,
)
from app.entities.task import TaskStatus


class TestTaskStateMachine:
    """Test suite for TaskStateMachine."""

    def test_valid_normal_flow_transitions(self):
        """Test valid transitions in normal pipeline flow."""
        # PENDING -> STYLE_DETECTION
        assert TaskStateMachine.validate_transition(
            TaskStatus.PENDING,
            TaskStatus.STYLE_DETECTION
        ) is True

        # STYLE_DETECTION -> STORY_GENERATION
        assert TaskStateMachine.validate_transition(
            TaskStatus.STYLE_DETECTION,
            TaskStatus.STORY_GENERATION
        ) is True

        # STORY_GENERATION -> STORYBOARD_BREAKDOWN
        assert TaskStateMachine.validate_transition(
            TaskStatus.STORY_GENERATION,
            TaskStatus.STORYBOARD_BREAKDOWN
        ) is True

        # STORYBOARD_BREAKDOWN -> IMAGE_GENERATION
        assert TaskStateMachine.validate_transition(
            TaskStatus.STORYBOARD_BREAKDOWN,
            TaskStatus.IMAGE_GENERATION
        ) is True

        # IMAGE_GENERATION -> VIDEO_GENERATION
        assert TaskStateMachine.validate_transition(
            TaskStatus.IMAGE_GENERATION,
            TaskStatus.VIDEO_GENERATION
        ) is True

        # VIDEO_GENERATION -> COMPOSING
        assert TaskStateMachine.validate_transition(
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.COMPOSING
        ) is True

        # COMPOSING -> COMPLETED
        assert TaskStateMachine.validate_transition(
            TaskStatus.COMPOSING,
            TaskStatus.COMPLETED
        ) is True

    def test_invalid_transitions(self):
        """Test invalid state transitions."""
        # Can't skip states
        assert TaskStateMachine.validate_transition(
            TaskStatus.PENDING,
            TaskStatus.STORY_GENERATION
        ) is False

        # Can't go backwards in normal flow
        assert TaskStateMachine.validate_transition(
            TaskStatus.STORY_GENERATION,
            TaskStatus.STYLE_DETECTION
        ) is False

        # Can't transition from completed
        assert TaskStateMachine.validate_transition(
            TaskStatus.COMPLETED,
            TaskStatus.STYLE_DETECTION
        ) is False

    def test_failure_transitions(self):
        """Test transitions to FAILED state."""
        # Any processing state can transition to FAILED
        assert TaskStateMachine.validate_transition(
            TaskStatus.STYLE_DETECTION,
            TaskStatus.FAILED
        ) is True

        assert TaskStateMachine.validate_transition(
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.FAILED
        ) is True

    def test_cancellation_transitions(self):
        """Test transitions to CANCELLED state."""
        # Any state can transition to CANCELLED
        assert TaskStateMachine.validate_transition(
            TaskStatus.PENDING,
            TaskStatus.CANCELLED
        ) is True

        assert TaskStateMachine.validate_transition(
            TaskStatus.VIDEO_GENERATION,
            TaskStatus.CANCELLED
        ) is True

    def test_retry_transitions(self):
        """Test retry-related transitions."""
        # Processing states can transition to RETRYING
        assert TaskStateMachine.validate_transition(
            TaskStatus.STYLE_DETECTION,
            TaskStatus.RETRYING
        ) is True

        # FAILED can transition to RETRYING
        assert TaskStateMachine.validate_transition(
            TaskStatus.FAILED,
            TaskStatus.RETRYING
        ) is True

        # RETRYING can transition back to processing states
        assert TaskStateMachine.validate_transition(
            TaskStatus.RETRYING,
            TaskStatus.STYLE_DETECTION
        ) is True

    def test_get_valid_transitions(self):
        """Test getting valid transitions for a state."""
        transitions = TaskStateMachine.get_valid_transitions(TaskStatus.PENDING)

        assert TaskStatus.STYLE_DETECTION in transitions
        assert TaskStatus.FAILED in transitions
        assert TaskStatus.CANCELLED in transitions
        assert TaskStatus.STORY_GENERATION not in transitions

    def test_is_terminal(self):
        """Test terminal state detection."""
        assert TaskStateMachine.is_terminal(TaskStatus.COMPLETED) is True
        assert TaskStateMachine.is_terminal(TaskStatus.CANCELLED) is True
        assert TaskStateMachine.is_terminal(TaskStatus.PENDING) is False
        assert TaskStateMachine.is_terminal(TaskStatus.STYLE_DETECTION) is False
        assert TaskStateMachine.is_terminal(TaskStatus.FAILED) is False

    def test_is_processing(self):
        """Test processing state detection."""
        assert TaskStateMachine.is_processing(TaskStatus.STYLE_DETECTION) is True
        assert TaskStateMachine.is_processing(TaskStatus.VIDEO_GENERATION) is True
        assert TaskStateMachine.is_processing(TaskStatus.PENDING) is False
        assert TaskStateMachine.is_processing(TaskStatus.COMPLETED) is False
        assert TaskStateMachine.is_processing(TaskStatus.FAILED) is False

    def test_is_retryable(self):
        """Test retryable state detection."""
        assert TaskStateMachine.is_retryable(TaskStatus.STYLE_DETECTION) is True
        assert TaskStateMachine.is_retryable(TaskStatus.VIDEO_GENERATION) is True
        assert TaskStateMachine.is_retryable(TaskStatus.PENDING) is False
        assert TaskStateMachine.is_retryable(TaskStatus.COMPLETED) is False

    def test_get_next_state(self):
        """Test getting next state in pipeline."""
        assert TaskStateMachine.get_next_state(TaskStatus.PENDING) == TaskStatus.STYLE_DETECTION
        assert TaskStateMachine.get_next_state(TaskStatus.STYLE_DETECTION) == TaskStatus.STORY_GENERATION
        assert TaskStateMachine.get_next_state(TaskStatus.COMPOSING) == TaskStatus.COMPLETED
        assert TaskStateMachine.get_next_state(TaskStatus.COMPLETED) is None

    def test_get_previous_state(self):
        """Test getting previous state in pipeline."""
        assert TaskStateMachine.get_previous_state(TaskStatus.STYLE_DETECTION) == TaskStatus.PENDING
        assert TaskStateMachine.get_previous_state(TaskStatus.STORY_GENERATION) == TaskStatus.STYLE_DETECTION
        assert TaskStateMachine.get_previous_state(TaskStatus.PENDING) is None

    def test_can_proceed(self):
        """Test if task can proceed to next state."""
        assert TaskStateMachine.can_proceed(TaskStatus.PENDING) is True
        assert TaskStateMachine.can_proceed(TaskStatus.STYLE_DETECTION) is True
        assert TaskStateMachine.can_proceed(TaskStatus.COMPLETED) is False
        assert TaskStateMachine.can_proceed(TaskStatus.CANCELLED) is False

    def test_transition_with_raise(self):
        """Test transition with raise_on_invalid flag."""
        # Valid transition should succeed
        assert TaskStateMachine.transition(
            TaskStatus.PENDING,
            TaskStatus.STYLE_DETECTION,
            raise_on_invalid=True
        ) is True

        # Invalid transition should raise
        with pytest.raises(ValueError):
            TaskStateMachine.transition(
                TaskStatus.PENDING,
                TaskStatus.STORY_GENERATION,
                raise_on_invalid=True
            )

    def test_transition_without_raise(self):
        """Test transition without raising on invalid."""
        # Invalid transition should return False
        assert TaskStateMachine.transition(
            TaskStatus.PENDING,
            TaskStatus.STORY_GENERATION,
            raise_on_invalid=False
        ) is False

    def test_get_retry_state(self):
        """Test getting retry state after failure."""
        assert TaskStateMachine.get_retry_state(TaskStatus.STYLE_DETECTION) == TaskStatus.STYLE_DETECTION
        assert TaskStateMachine.get_retry_state(TaskStatus.VIDEO_GENERATION) == TaskStatus.VIDEO_GENERATION
        assert TaskStateMachine.get_retry_state(TaskStatus.PENDING) is None


class TestStateMachineConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_can_transition_to(self):
        """Test can_transition_to convenience function."""
        assert can_transition_to(
            TaskStatus.PENDING,
            TaskStatus.STYLE_DETECTION
        ) is True

        assert can_transition_to(
            TaskStatus.PENDING,
            TaskStatus.COMPLETED
        ) is False

    def test_get_next_pipeline_state(self):
        """Test get_next_pipeline_state convenience function."""
        assert get_next_pipeline_state(TaskStatus.PENDING) == TaskStatus.STYLE_DETECTION
        assert get_next_pipeline_state(TaskStatus.COMPLETED) is None

    def test_is_terminal_state(self):
        """Test is_terminal_state convenience function."""
        assert is_terminal_state(TaskStatus.COMPLETED) is True
        assert is_terminal_state(TaskStatus.PENDING) is False

    def test_is_processing_state(self):
        """Test is_processing_state convenience function."""
        assert is_processing_state(TaskStatus.STYLE_DETECTION) is True
        assert is_processing_state(TaskStatus.PENDING) is False


__all__ = ["TestTaskStateMachine", "TestStateMachineConvenienceFunctions"]
