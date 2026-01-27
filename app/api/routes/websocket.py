"""WebSocket routes for real-time task progress updates."""

import json
import uuid
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.entities.task import Task
from app.api.schemas import WebSocketMessage, ProgressUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections and broadcasts."""

    def __init__(self):
        """Initialize connection manager."""
        # Task ID -> Set of WebSocket connections
        self.task_subscriptions: Dict[uuid.UUID, Set[WebSocket]] = {}
        # All active connections
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, task_id: uuid.UUID) -> None:
        """
        Connect a WebSocket to subscribe to task updates.

        Args:
            websocket: WebSocket connection
            task_id: Task ID to subscribe to
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(websocket)

        logger.info(f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a WebSocket.

        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)

        # Remove from all task subscriptions
        for task_id, connections in self.task_subscriptions.items():
            connections.discard(websocket)
            if not connections:
                del self.task_subscriptions[task_id]

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket.

        Args:
            message: Message to send
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_task(self, task_id: uuid.UUID, message: dict) -> None:
        """
        Broadcast a message to all subscribers of a task.

        Args:
            task_id: Task ID
            message: Message to broadcast
        """
        if task_id not in self.task_subscriptions:
            return

        # Create a copy of connections to avoid modification during iteration
        connections = list(self.task_subscriptions[task_id])

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                self.disconnect(connection)

    async def broadcast_to_all(self, message: dict) -> None:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast
        """
        # Create a copy of connections
        connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                self.disconnect(connection)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)

    def get_task_subscriber_count(self, task_id: uuid.UUID) -> int:
        """Get number of subscribers for a specific task."""
        return len(self.task_subscriptions.get(task_id, set()))


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/tasks/{task_id}")
async def task_updates_websocket(
    websocket: WebSocket,
    task_id: uuid.UUID,
    token: str = Query(default=None),
):
    """
    WebSocket endpoint for real-time task progress updates.

    Clients can connect to this endpoint to receive real-time updates
    about task progress, status changes, and completion.

    Args:
        websocket: WebSocket connection
        task_id: Task ID to subscribe to
        token: Optional authentication token

    Example:
        ```python
        import asyncio
        import websockets
        import json

        async def connect_to_task(task_id):
            uri = f"ws://localhost:8000/ws/tasks/{task_id}"
            async with websockets.connect(uri) as websocket:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Progress: {data.get('progress')}%")
        ```
    """
    # TODO: Validate token if authentication is enabled
    # if token:
    #     user = await authenticate_user(token)
    #     if not user:
    #         await websocket.close(code=1008, reason="Unauthorized")
    #         return

    await manager.connect(websocket, task_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "task_id": str(task_id),
                "message": "Connected to task updates",
            },
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            message_type = message.get("type")

            if message_type == "ping":
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "data": {"timestamp": message.get("timestamp")},
                })

            elif message_type == "subscribe":
                # Subscribe to additional tasks
                additional_task_ids = message.get("data", {}).get("task_ids", [])
                for tid_str in additional_task_ids:
                    try:
                        tid = uuid.UUID(tid_str)
                        await manager.connect(websocket, tid)
                    except ValueError:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": f"Invalid task ID: {tid_str}"},
                        })

            elif message_type == "unsubscribe":
                # Unsubscribe from tasks
                task_ids = message.get("data", {}).get("task_ids", [])
                for tid_str in task_ids:
                    try:
                        tid = uuid.UUID(tid_str)
                        if tid in manager.task_subscriptions:
                            manager.task_subscriptions[tid].discard(websocket)
                    except ValueError:
                        pass

            else:
                # Echo back unknown message types
                await websocket.send_json({
                    "type": "unknown_message",
                    "data": {"original_type": message_type},
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect(websocket)


@router.websocket("/subscribe")
async def multi_task_websocket(
    websocket: WebSocket,
    token: str = Query(default=None),
):
    """
    WebSocket endpoint for subscribing to multiple tasks.

    Clients must send a subscription message with task IDs after connecting.

    Args:
        websocket: WebSocket connection
        token: Optional authentication token

    Example:
        ```python
        import asyncio
        import websockets
        import json

        async def subscribe_to_tasks():
            uri = "ws://localhost:8000/ws/subscribe"
            async with websockets.connect(uri) as websocket:
                # Subscribe to tasks
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "data": {"task_ids": ["task-id-1", "task-id-2"]}
                }))

                # Listen for updates
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Update: {data}")
        ```
    """
    await websocket.accept()
    manager.active_connections.add(websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to multi-task updates",
                "instructions": "Send subscribe message with task_ids to receive updates",
            },
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "subscribe":
                # Subscribe to multiple tasks
                task_ids = message.get("data", {}).get("task_ids", [])
                for tid_str in task_ids:
                    try:
                        tid = uuid.UUID(tid_str)
                        if tid not in manager.task_subscriptions:
                            manager.task_subscriptions[tid] = set()
                        manager.task_subscriptions[tid].add(websocket)
                    except ValueError:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": f"Invalid task ID: {tid_str}"},
                        })

                # Confirm subscription
                await websocket.send_json({
                    "type": "subscribed",
                    "data": {
                        "task_ids": task_ids,
                        "count": len(task_ids),
                    },
                })

            elif message_type == "unsubscribe":
                # Unsubscribe from tasks
                task_ids = message.get("data", {}).get("task_ids", [])
                for tid_str in task_ids:
                    try:
                        tid = uuid.UUID(tid_str)
                        if tid in manager.task_subscriptions:
                            manager.task_subscriptions[tid].discard(websocket)
                    except ValueError:
                        pass

            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {"timestamp": message.get("timestamp")},
                })

            else:
                await websocket.send_json({
                    "type": "unknown_message",
                    "data": {"original_type": message_type},
                })

    except WebSocketDisconnect:
        manager.active_connections.discard(websocket)
        # Clean up task subscriptions
        for task_id, connections in manager.task_subscriptions.items():
            connections.discard(websocket)
            if not connections:
                del manager.task_subscriptions[task_id]
        logger.info("Multi-task WebSocket disconnected")
    except Exception as e:
        logger.error(f"Multi-task WebSocket error: {e}")
        manager.active_connections.discard(websocket)


@router.get("/status")
async def websocket_status():
    """
    Get WebSocket connection status.

    Returns:
        Statistics about active WebSocket connections
    """
    return {
        "active_connections": manager.get_connection_count(),
        "task_subscriptions": {
            str(task_id): len(connections)
            for task_id, connections in manager.task_subscriptions.items()
        },
    }


# Helper functions for broadcasting task updates
async def broadcast_task_progress(task_id: uuid.UUID, progress_update: ProgressUpdate) -> None:
    """
    Broadcast task progress update to all subscribers.

    Args:
        task_id: Task ID
        progress_update: Progress update data
    """
    message = {
        "type": "progress_update",
        "data": progress_update.model_dump(),
    }
    await manager.broadcast_to_task(task_id, message)


async def broadcast_task_status_change(
    task_id: uuid.UUID,
    old_status: str,
    new_status: str,
) -> None:
    """
    Broadcast task status change to all subscribers.

    Args:
        task_id: Task ID
        old_status: Previous status
        new_status: New status
    """
    message = {
        "type": "status_change",
        "data": {
            "task_id": str(task_id),
            "old_status": old_status,
            "new_status": new_status,
        },
    }
    await manager.broadcast_to_task(task_id, message)


async def broadcast_task_completed(task_id: uuid.UUID, output_url: str) -> None:
    """
    Broadcast task completion to all subscribers.

    Args:
        task_id: Task ID
        output_url: URL to generated video
    """
    message = {
        "type": "task_completed",
        "data": {
            "task_id": str(task_id),
            "output_video_url": output_url,
        },
    }
    await manager.broadcast_to_task(task_id, message)


async def broadcast_task_failed(task_id: uuid.UUID, error_message: str) -> None:
    """
    Broadcast task failure to all subscribers.

    Args:
        task_id: Task ID
        error_message: Error message
    """
    message = {
        "type": "task_failed",
        "data": {
            "task_id": str(task_id),
            "error_message": error_message,
        },
    }
    await manager.broadcast_to_task(task_id, message)


__all__ = [
    "router",
    "manager",
    "broadcast_task_progress",
    "broadcast_task_status_change",
    "broadcast_task_completed",
    "broadcast_task_failed",
]
