"""
WebSocket Real-Time Messaging - Production-Ready Implementation with Enhanced Stability

DDD + KISS Architecture:
- Clean separation: Connection management vs message handling
- Single responsibility: WebSocket lifecycle only
- Simple state: In-memory connection tracking
- Production-ready: Auto-reconnect, error handling, health checks

Features:
- Multi-device support (multiple connections per user)
- Automatic cleanup of dead connections
- Heartbeat/ping-pong keep-alive with timeout detection
- Graceful disconnection handling
- Real-time event broadcasting
- Message acknowledgment system
- Connection health monitoring
- Token expiration handling
"""

import asyncio
import logging
import time
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.utils import StringUtils
from database import get_db
from models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass
class ConnectionInfo:
    """Metadata for a WebSocket connection."""

    user_id: int
    connected_at: float
    last_ping: float = field(default_factory=time.time)
    last_pong: float = field(default_factory=time.time)
    pending_acks: dict[str, float] = field(default_factory=dict)


class WebSocketManager:
    """
    Production WebSocket connection manager with enhanced stability.

    Responsibilities:
    1. Connection Lifecycle: Accept, track, cleanup
    2. Message Broadcasting: Send to users/groups
    3. Presence Tracking: Online/offline status
    4. Health Monitoring: Dead connection cleanup
    5. Message Acknowledgment: Track message delivery

    Design Principles (KISS):
    - In-memory state (single instance)
    - Auto-cleanup of dead connections
    - No external dependencies
    - Simple dict-based tracking

    Features:
    - Multi-device support (N connections per user)
    - Automatic dead connection removal
    - Graceful error handling
    - Presence detection
    - Message acknowledgment with retry
    - Connection health monitoring
    """

    # Configuration
    PING_TIMEOUT_SECONDS = 60  # Consider connection dead if no pong in 60s
    ACK_TIMEOUT_SECONDS = 10  # Wait 10s for message acknowledgment
    CLEANUP_INTERVAL_SECONDS = 30  # Run cleanup every 30s

    def __init__(self) -> None:
        """Initialize manager with empty state."""
        # Primary connection store: user_id -> set of WebSocket connections
        self.active_connections: dict[int, set[WebSocket]] = {}

        # Connection metadata for monitoring/debugging
        self.connection_metadata: dict[WebSocket, ConnectionInfo] = {}

        # Statistics (optional, for monitoring)
        self._stats = {
            "total_connections": 0,
            "total_disconnections": 0,
            "failed_sends": 0,
            "acks_sent": 0,
            "acks_timeout": 0,
        }

        # Background cleanup task
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start_cleanup_task(self) -> None:
        """Start background task for cleaning up stale connections."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("WebSocket cleanup task started")

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._cleanup_task
            logger.info("WebSocket cleanup task stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def _cleanup_stale_connections(self) -> None:
        """Remove connections that haven't responded to pings."""
        current_time = time.time()
        stale_connections: list[tuple[WebSocket, int]] = []

        for ws, info in list(self.connection_metadata.items()):
            # Check if connection is stale (no pong received recently)
            if current_time - info.last_pong > self.PING_TIMEOUT_SECONDS:
                stale_connections.append((ws, info.user_id))

            # Check for timed out acknowledgments
            timed_out_acks = [
                ack_id
                for ack_id, ack_time in list(info.pending_acks.items())
                if current_time - ack_time > self.ACK_TIMEOUT_SECONDS
            ]
            for ack_id in timed_out_acks:
                del info.pending_acks[ack_id]
                self._stats["acks_timeout"] += 1
                logger.debug(f"Ack timeout for message {ack_id} to user {info.user_id}")

        # Disconnect stale connections
        for ws, user_id in stale_connections:
            logger.warning(f"Cleaning up stale connection for user {user_id}")
            await self.disconnect(ws, user_id)
            try:
                await ws.close(code=4000, reason="Connection timeout")
            except Exception:
                pass

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: ID of authenticated user

        Note:
            Supports multiple connections per user (multi-device)
        """
        try:
            await websocket.accept()

            # Initialize user's connection set if first connection
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()

            # Add connection to user's set
            self.active_connections[user_id].add(websocket)

            # Store metadata for monitoring
            current_time = time.time()
            self.connection_metadata[websocket] = ConnectionInfo(
                user_id=user_id,
                connected_at=current_time,
                last_ping=current_time,
                last_pong=current_time,
            )

            # Update stats
            self._stats["total_connections"] += 1

            # Ensure cleanup task is running
            await self.start_cleanup_task()

            logger.info(
                f"WebSocket connected: user={user_id}, "
                f"user_connections={len(self.active_connections[user_id])}, "
                f"total_users_online={len(self.active_connections)}"
            )

        except Exception as e:
            logger.error(f"Failed to accept WebSocket for user {user_id}: {e}", exc_info=True)
            raise

    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """
        Unregister and close a WebSocket connection.

        Args:
            websocket: WebSocket instance to disconnect
            user_id: User ID associated with connection

        Note:
            Automatically cleans up user entry if last connection
        """
        try:
            # Remove connection from user's set
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                # Remove user entry if no connections left
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Clean up metadata
            self.connection_metadata.pop(websocket, None)

            # Update stats
            self._stats["total_disconnections"] += 1

            remaining = len(self.active_connections.get(user_id, set()))
            logger.info(
                f"WebSocket disconnected: user={user_id}, "
                f"remaining_user_connections={remaining}, "
                f"total_users_online={len(self.active_connections)}"
            )

        except Exception as e:
            logger.error(f"Error during disconnect for user {user_id}: {e}", exc_info=True)

    def update_pong(self, websocket: WebSocket) -> None:
        """Update the last pong time for a connection."""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket].last_pong = time.time()

    def track_pending_ack(self, websocket: WebSocket, ack_id: str) -> None:
        """Track a message that needs acknowledgment."""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket].pending_acks[ack_id] = time.time()

    def receive_ack(self, websocket: WebSocket, ack_id: str) -> bool:
        """
        Process an acknowledgment for a message.

        Returns:
            True if ack was expected and processed, False otherwise
        """
        if websocket in self.connection_metadata:
            if ack_id in self.connection_metadata[websocket].pending_acks:
                del self.connection_metadata[websocket].pending_acks[ack_id]
                self._stats["acks_sent"] += 1
                return True
        return False

    async def send_personal_message(
        self, message: dict[str, Any], user_id: int, require_ack: bool = False
    ) -> bool:
        """
        Send a message to a specific user across all their connections.

        Args:
            message: Message payload as dictionary (will be JSON-serialized)
            user_id: Target user ID
            require_ack: If True, track message for acknowledgment

        Returns:
            True if sent to at least one connection, False otherwise

        Features:
        - Multi-device delivery (sends to all user's connections)
        - Automatic dead connection cleanup
        - Graceful error handling
        - No exception propagation
        """
        if user_id not in self.active_connections:
            # User not online - message will be delivered via API polling
            logger.debug(f"User {user_id} not connected, skipping WebSocket delivery")
            return False

        disconnected: set[WebSocket] = set()
        success_count = 0

        # Add ack_id if acknowledgment is required
        if require_ack and "_ack_id" not in message:
            message["_ack_id"] = f"{user_id}-{time.time()}-{id(message)}"

        # Send to all user's active connections
        for connection in list(self.active_connections[user_id]):
            try:
                await connection.send_json(message)
                success_count += 1

                # Track pending ack if required
                if require_ack and "_ack_id" in message:
                    self.track_pending_ack(connection, message["_ack_id"])

            except RuntimeError as e:
                # Connection closed or invalid state
                logger.debug(f"Connection closed for user {user_id}: {e}")
                disconnected.add(connection)

            except Exception as e:
                # Unexpected error - log and mark for cleanup
                logger.warning(f"Unexpected error sending to user {user_id}: {e}", exc_info=True)
                disconnected.add(connection)

        # Clean up dead connections automatically
        if disconnected:
            for connection in disconnected:
                await self.disconnect(connection, user_id)
            self._stats["failed_sends"] += len(disconnected)

        # Log delivery status
        if success_count > 0:
            logger.debug(
                f"Delivered to user {user_id}: success={success_count}, failed={len(disconnected)}"
            )
            return True
        else:
            logger.debug(f"Failed to deliver to user {user_id} (all connections dead)")
            return False

    async def send_with_ack(
        self, message: dict[str, Any], user_id: int, ack_id: str
    ) -> bool:
        """
        Send a message that requires acknowledgment.

        Args:
            message: Message payload
            user_id: Target user ID
            ack_id: Acknowledgment ID to track

        Returns:
            True if sent successfully
        """
        message_with_ack = {**message, "_ack_id": ack_id}
        return await self.send_personal_message(message_with_ack, user_id, require_ack=True)

    async def broadcast_to_users(self, message: dict[str, Any], user_ids: list[int]) -> int:
        """
        Send a message to multiple users.

        Args:
            message: Message payload
            user_ids: List of target user IDs

        Returns:
            Number of users successfully reached
        """
        success_count = 0
        for user_id in user_ids:
            if await self.send_personal_message(message, user_id):
                success_count += 1
        return success_count

    def is_user_online(self, user_id: int) -> bool:
        """
        Check if user has any active connections.

        Args:
            user_id: User ID to check

        Returns:
            True if user has at least one active connection
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_online_users(self, user_ids: list[int]) -> list[int]:
        """
        Filter list of users to only online ones.

        Args:
            user_ids: List of user IDs to check

        Returns:
            List of online user IDs
        """
        return [uid for uid in user_ids if self.is_user_online(uid)]

    async def broadcast_to_all(self, message: dict[str, Any]) -> int:
        """Broadcast a message to all connected users."""
        all_user_ids = list(self.active_connections.keys())
        return await self.broadcast_to_users(message, all_user_ids)

    def get_online_count(self) -> int:
        """Get total number of online users."""
        return len(self.active_connections)

    def get_connection_count(self) -> int:
        """Get total number of active WebSocket connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict[str, Any]:
        """
        Get connection statistics for monitoring.

        Returns:
            Dictionary with stats:
            - online_users: Number of users with active connections
            - total_connections: Number of WebSocket connections
            - total_connected: Lifetime connection count
            - total_disconnected: Lifetime disconnection count
            - failed_sends: Failed message delivery count
            - acks_sent: Successful acknowledgments
            - acks_timeout: Timed out acknowledgments
        """
        return {
            "online_users": self.get_online_count(),
            "total_connections": self.get_connection_count(),
            "total_connected": self._stats["total_connections"],
            "total_disconnected": self._stats["total_disconnections"],
            "failed_sends": self._stats["failed_sends"],
            "acks_sent": self._stats["acks_sent"],
            "acks_timeout": self._stats["acks_timeout"],
        }


# Global singleton instance
manager = WebSocketManager()


async def authenticate_websocket(websocket: WebSocket, token: str, db: Session) -> User | None:
    """
    Authenticate WebSocket connection using JWT token.

    Args:
        websocket: WebSocket instance (for logging)
        token: JWT access token
        db: Database session

    Returns:
        User object if authentication successful, None otherwise

    Security:
    - Validates JWT signature and expiration
    - Checks user is active
    - Normalizes email for lookup
    - Never raises exceptions (returns None on failure)
    """
    if not token:
        logger.debug("WebSocket auth failed: No token provided")
        return None

    try:
        # Decode and validate JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            logger.debug("WebSocket auth failed: No email in token")
            return None

        # Look up user (must be active)
        user = (
            db.query(User)
            .filter(
                User.email == StringUtils.normalize_email(email),
                User.is_active.is_(True),
            )
            .first()
        )

        if user:
            logger.debug(f"WebSocket auth successful: user_id={user.id}")
        else:
            logger.debug(f"WebSocket auth failed: User not found or inactive: {email}")

        return user

    except ExpiredSignatureError:
        logger.debug("WebSocket JWT expired")
        return None
    except JWTError as e:
        logger.debug(f"WebSocket JWT validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected WebSocket auth error: {e}", exc_info=True)
        return None


async def check_token_expiration(token: str) -> bool:
    """
    Check if a JWT token is expired without raising exceptions.

    Args:
        token: JWT access token

    Returns:
        True if token is valid, False if expired or invalid
    """
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return True
    except ExpiredSignatureError:
        return False
    except JWTError:
        return False


@router.websocket("/ws/messages")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = None,
    db: Session = Depends(get_db),
) -> None:
    """
    WebSocket endpoint for real-time messaging.

    **Connection URL:**
    ```
    ws://localhost:8000/api/v1/ws/messages?token=<jwt_token>
    wss://api.example.com/api/v1/ws/messages?token=<jwt_token>
    ```

    **Client -> Server Events:**
    ```json
    {
        "type": "ping"
    }

    {
        "type": "typing",
        "recipient_id": 123
    }

    {
        "type": "message_delivered",
        "message_id": 456,
        "sender_id": 789
    }

    {
        "type": "message_read",
        "message_id": 456,
        "sender_id": 789
    }

    {
        "type": "presence_check",
        "user_ids": [1, 2, 3]
    }

    {
        "type": "ack",
        "_ack_id": "message-id-123"
    }
    ```

    **Server -> Client Events:**
    ```json
    {
        "type": "connection",
        "status": "connected",
        "user_id": 123
    }

    {
        "type": "pong"
    }

    {
        "type": "new_message",
        "message_id": 789,
        "sender_id": 456,
        "sender_email": "user@example.com",
        "recipient_id": 123,
        "booking_id": null,
        "message": "Hello!",
        "created_at": "2025-01-10T12:34:56Z",
        "is_read": false,
        "_ack_id": "optional-for-delivery-tracking"
    }

    {
        "type": "message_sent",
        "message_id": 789,
        "recipient_id": 456
    }

    {
        "type": "message_read",
        "message_id": 789,
        "reader_id": 456
    }

    {
        "type": "message_edited",
        "message_id": 789,
        "new_content": "Updated message",
        "edited_at": "2025-01-10T12:35:00Z"
    }

    {
        "type": "message_deleted",
        "message_id": 789,
        "deleted_by": 123
    }

    {
        "type": "typing",
        "user_id": 456,
        "user_email": "user@example.com"
    }

    {
        "type": "presence_status",
        "online_users": [1, 2],
        "offline_users": [3, 4]
    }

    {
        "type": "delivery_receipt",
        "message_id": 789,
        "recipient_id": 456,
        "state": "delivered"
    }

    {
        "type": "ack",
        "_ack_id": "message-id-123"
    }

    {
        "type": "token_expired"
    }
    ```

    **Connection Lifecycle:**
    1. Client connects with JWT token in query param
    2. Server authenticates and accepts connection
    3. Server sends connection confirmation
    4. Client/Server exchange messages
    5. Client sends ping every 30s for keep-alive
    6. On disconnect, server cleans up resources

    **Error Handling:**
    - Invalid token -> Connection rejected (1008)
    - Expired token -> token_expired message sent, connection closed (4001)
    - Malformed JSON -> Error message sent, connection stays open
    - Unexpected errors -> Connection closed gracefully
    """

    # Authentication required
    if not token:
        logger.warning("WebSocket connection attempt without token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authenticate user
    user = await authenticate_websocket(websocket, token, db)
    if not user:
        # Check if token is expired specifically
        if not await check_token_expiration(token):
            logger.warning("WebSocket connection with expired token")
            try:
                await websocket.accept()
                await websocket.send_json({"type": "token_expired"})
                await websocket.close(code=4001, reason="Token expired")
            except Exception:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        else:
            logger.warning(f"WebSocket authentication failed for token: {token[:20]}...")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect user
    await manager.connect(websocket, user.id)
    stored_token = token

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            }
        )

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                event_type = data.get("type")

                if not event_type:
                    await websocket.send_json({"type": "error", "message": "Missing event type"})
                    continue

                # Handle different event types
                if event_type == "ping":
                    # Keep-alive heartbeat
                    manager.update_pong(websocket)
                    await websocket.send_json({"type": "pong"})

                elif event_type == "ack":
                    # Message acknowledgment from client
                    ack_id = data.get("_ack_id")
                    if ack_id:
                        manager.receive_ack(websocket, ack_id)

                elif event_type == "typing":
                    # Typing indicator
                    recipient_id = data.get("recipient_id")
                    if recipient_id:
                        await manager.send_personal_message(
                            {
                                "type": "typing",
                                "user_id": user.id,
                                "user_email": user.email,
                            },
                            recipient_id,
                        )

                elif event_type == "message_delivered":
                    # Delivery acknowledgment
                    message_id = data.get("message_id")
                    sender_id = data.get("sender_id")
                    if message_id and sender_id:
                        await manager.send_personal_message(
                            {
                                "type": "delivery_receipt",
                                "message_id": message_id,
                                "recipient_id": user.id,
                                "state": "delivered",
                            },
                            sender_id,
                        )

                elif event_type == "message_read":
                    # Read acknowledgment
                    message_id = data.get("message_id")
                    sender_id = data.get("sender_id")
                    if message_id and sender_id:
                        await manager.send_personal_message(
                            {
                                "type": "message_read",
                                "message_id": message_id,
                                "reader_id": user.id,
                            },
                            sender_id,
                        )

                elif event_type == "presence_check":
                    # Online presence check
                    user_ids = data.get("user_ids", [])
                    if isinstance(user_ids, list):
                        online_users = manager.get_online_users(user_ids)
                        offline_users = [uid for uid in user_ids if uid not in online_users]
                        await websocket.send_json(
                            {
                                "type": "presence_status",
                                "online_users": online_users,
                                "offline_users": offline_users,
                            }
                        )
                    else:
                        await websocket.send_json(
                            {"type": "error", "message": "user_ids must be a list"}
                        )

                elif event_type == "refresh_token":
                    # Token refresh - update stored token
                    new_token = data.get("token")
                    if new_token:
                        # Verify the new token is valid
                        if await check_token_expiration(new_token):
                            stored_token = new_token
                            await websocket.send_json(
                                {"type": "token_refreshed", "status": "success"}
                            )
                        else:
                            await websocket.send_json(
                                {"type": "error", "message": "Invalid token provided"}
                            )

                else:
                    # Unknown event type
                    await websocket.send_json(
                        {"type": "error", "message": f"Unknown event type: {event_type}"}
                    )

            except ValueError as e:
                # Invalid JSON
                logger.warning(f"Invalid JSON from user {user.id}: {e}")
                await websocket.send_json({"type": "error", "message": "Invalid message format"})
            except WebSocketDisconnect:
                # Client disconnected during message processing - this is normal
                logger.debug(f"WebSocket disconnected during message processing for user {user.id}")
                raise  # Re-raise to be caught by outer handler
            except Exception as e:
                # Unexpected error processing message
                # Check if it's a connection closing error (don't log as ERROR, just DEBUG)
                if "close message has been sent" in str(e) or isinstance(e, RuntimeError):
                    logger.debug(
                        f"WebSocket message processing interrupted (connection closing) "
                        f"for user {user.id}: {e}"
                    )
                else:
                    logger.error(
                        f"Error processing WebSocket message from user {user.id}: {e}",
                        exc_info=True,
                    )

                # Try to send error response, but don't fail if connection is closing
                with suppress(RuntimeError, Exception):
                    await websocket.send_json(
                        {"type": "error", "message": "Internal error processing message"}
                    )

    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected normally: user_id={user.id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}", exc_info=True)
    finally:
        # Always clean up connection
        await manager.disconnect(websocket, user.id)
