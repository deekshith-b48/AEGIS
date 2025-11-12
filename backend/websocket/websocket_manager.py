"""
WebSocket Manager for Project AEGIS
Real-time communication system for live updates and notifications
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    # System messages
    CONNECTION_ESTABLISHED = "connection_established"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

    # Data updates
    NEW_PREDICTION = "new_prediction"
    PREDICTION_UPDATED = "prediction_updated"
    CORDON_ACTIVATED = "cordon_activated"
    CORDON_UPDATED = "cordon_updated"
    CORDON_EXPIRED = "cordon_expired"

    # Alerts
    ALERT_CREATED = "alert_created"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"

    # Analytics
    ANALYTICS_UPDATE = "analytics_update"
    SYSTEM_STATUS = "system_status"
    MODEL_PERFORMANCE = "model_performance"

    # GIS updates
    LOCATION_UPDATE = "location_update"
    HOTSPOT_DETECTED = "hotspot_detected"

    # Learning
    MODEL_RETRAINED = "model_retrained"
    PERFORMANCE_IMPROVED = "performance_improved"

class ClientRole(Enum):
    """Client roles for authorization"""
    CITIZEN = "citizen"
    LAW_ENFORCEMENT = "law_enforcement"
    ANALYST = "analyst"
    ADMINISTRATOR = "administrator"
    SYSTEM = "system"

class SubscriptionType(Enum):
    """Subscription types for filtering messages"""
    ALL = "all"
    PREDICTIONS = "predictions"
    CORDONS = "cordons"
    ALERTS = "alerts"
    ANALYTICS = "analytics"
    GIS = "gis"
    LEARNING = "learning"

@dataclass
class WebSocketClient:
    """WebSocket client information"""
    client_id: str
    websocket: WebSocket
    user_id: str
    role: ClientRole
    connected_at: datetime
    last_activity: datetime
    subscriptions: Set[SubscriptionType]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if not hasattr(self.websocket, '_ref'):
            self.websocket._ref = weakref.ref(self.websocket)

class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str = None
    client_id: Optional[str] = None
    subscription_type: Optional[SubscriptionType] = None
    priority: str = "normal"  # low, normal, high, critical

    class Config:
        use_enum_values = True

class WebSocketManager:
    """
    Advanced WebSocket connection manager for Project AEGIS
    Handles real-time communication with clients
    """

    def __init__(self):
        # Active connections
        self.clients: Dict[str, WebSocketClient] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> client_ids

        # Message queues
        self.message_queue = asyncio.Queue()
        self.high_priority_queue = asyncio.Queue()

        # Broadcasting
        self.broadcast_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "peak_connections": 0
        }

        # Rate limiting
        self.client_message_counts: Dict[str, Dict[str, int]] = {}
        self.rate_limits = {
            "citizen": 10,      # messages per minute
            "law_enforcement": 30,
            "analyst": 60,
            "administrator": 100,
            "system": 1000
        }

        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {}

    async def start_background_tasks(self):
        """Start background tasks for message processing"""
        if not self.broadcast_task:
            self.broadcast_task = asyncio.create_task(self._broadcast_messages())

        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self.broadcast_task:
            self.broadcast_task.cancel()
            self.broadcast_task = None

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None

    async def connect_client(self, websocket: WebSocket, user_id: str,
                           role: ClientRole, subscriptions: List[SubscriptionType] = None,
                           metadata: Dict[str, Any] = None) -> str:
        """
        Accept and register a new WebSocket client
        """
        try:
            await websocket.accept()

            client_id = str(uuid.uuid4())
            subscriptions_set = set(subscriptions or [SubscriptionType.ALL])

            client = WebSocketClient(
                client_id=client_id,
                websocket=websocket,
                user_id=user_id,
                role=role,
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                subscriptions=subscriptions_set,
                metadata=metadata or {}
            )

            # Register client
            self.clients[client_id] = client

            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)

            # Initialize rate limiting
            self.client_message_counts[client_id] = {
                "count": 0,
                "window_start": datetime.utcnow()
            }

            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.clients)
            self.stats["peak_connections"] = max(self.stats["peak_connections"], self.stats["active_connections"])

            # Send welcome message
            await self._send_to_client(client, WebSocketMessage(
                type=MessageType.CONNECTION_ESTABLISHED,
                data={
                    "client_id": client_id,
                    "role": role.value,
                    "subscriptions": [sub.value for sub in subscriptions_set],
                    "server_time": datetime.utcnow().isoformat(),
                    "message": "Connected to Project AEGIS real-time updates"
                },
                timestamp=datetime.utcnow(),
                message_id=str(uuid.uuid4())
            ))

            logger.info(f"📡 WebSocket client connected: {client_id} (User: {user_id}, Role: {role.value})")

            # Start background tasks if not already running
            await self.start_background_tasks()

            return client_id

        except Exception as e:
            logger.error(f"❌ Error connecting WebSocket client: {str(e)}")
            raise

    async def disconnect_client(self, client_id: str) -> None:
        """
        Disconnect and clean up a WebSocket client
        """
        if client_id not in self.clients:
            return

        client = self.clients[client_id]

        try:
            # Remove from user connections
            if client.user_id in self.user_connections:
                self.user_connections[client.user_id].discard(client_id)
                if not self.user_connections[client.user_id]:
                    del self.user_connections[client.user_id]

            # Remove from clients
            del self.clients[client_id]

            # Clean up rate limiting
            if client_id in self.client_message_counts:
                del self.client_message_counts[client_id]

            # Update statistics
            self.stats["active_connections"] = len(self.clients)

            logger.info(f"📡 WebSocket client disconnected: {client_id}")

        except Exception as e:
            logger.error(f"❌ Error disconnecting client {client_id}: {str(e)}")

    async def send_message(self, message: WebSocketMessage,
                         target_clients: List[str] = None,
                         target_roles: List[ClientRole] = None,
                         target_users: List[str] = None,
                         subscription_type: SubscriptionType = None) -> int:
        """
        Send a message to specific clients based on various criteria
        """
        sent_count = 0

        try:
            # Determine target clients
            if target_clients:
                # Specific client IDs
                recipients = [cid for cid in target_clients if cid in self.clients]
            elif target_users:
                # Specific user IDs
                recipients = []
                for user_id in target_users:
                    if user_id in self.user_connections:
                        recipients.extend(self.user_connections[user_id])
            elif target_roles:
                # Specific roles
                recipients = [
                    cid for cid, client in self.clients.items()
                    if client.role in target_roles
                ]
            elif subscription_type:
                # Clients subscribed to specific type
                recipients = [
                    cid for cid, client in self.clients.items()
                    if subscription_type in client.subscriptions or SubscriptionType.ALL in client.subscriptions
                ]
            else:
                # All clients
                recipients = list(self.clients.keys())

            # Filter by subscriptions if specified
            if message.subscription_type and recipients:
                recipients = [
                    cid for cid in recipients
                    if cid in self.clients and (
                        message.subscription_type in self.clients[cid].subscriptions or
                        SubscriptionType.ALL in self.clients[cid].subscriptions
                    )
                ]

            # Send to recipients
            for client_id in recipients:
                client = self.clients.get(client_id)
                if client:
                    await self._send_to_client(client, message)
                    sent_count += 1

            # Update statistics
            self.stats["messages_sent"] += sent_count

            return sent_count

        except Exception as e:
            logger.error(f"❌ Error sending message: {str(e)}")
            self.stats["errors"] += 1
            return 0

    async def broadcast(self, message_type: MessageType, data: Dict[str, Any],
                        subscription_type: SubscriptionType = None,
                        priority: str = "normal") -> int:
        """
        Broadcast a message to all subscribed clients
        """
        message = WebSocketMessage(
            type=message_type,
            data=data,
            timestamp=datetime.utcnow(),
            message_id=str(uuid.uuid4()),
            subscription_type=subscription_type,
            priority=priority
        )

        # Queue based on priority
        if priority in ["high", "critical"]:
            await self.high_priority_queue.put(message)
        else:
            await self.message_queue.put(message)

        return len(self.clients)

    async def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """
        Register a message handler for specific message types
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    async def handle_client_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """
        Handle incoming message from a client
        """
        try:
            # Update activity
            if client_id in self.clients:
                self.clients[client_id].last_activity = datetime.utcnow()

            # Rate limiting check
            if not await self._check_rate_limit(client_id):
                await self._send_error(client_id, "Rate limit exceeded")
                return

            # Parse message
            message_type = message.get("type")
            if message_type:
                try:
                    msg_type = MessageType(message_type)

                    # Call registered handlers
                    if msg_type in self.message_handlers:
                        for handler in self.message_handlers[msg_type]:
                            try:
                                await handler(client_id, message)
                            except Exception as e:
                                logger.error(f"❌ Error in message handler: {str(e)}")

                except ValueError:
                    logger.warning(f"⚠️ Unknown message type: {message_type}")

            self.stats["messages_received"] += 1

        except Exception as e:
            logger.error(f"❌ Error handling client message: {str(e)}")
            self.stats["errors"] += 1

    async def _send_to_client(self, client: WebSocketClient, message: WebSocketMessage) -> bool:
        """
        Send a message to a specific client
        """
        try:
            await client.websocket.send_text(message.model_dump_json())
            client.last_activity = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"❌ Error sending to client {client.client_id}: {str(e)}")
            # Schedule disconnection
            asyncio.create_task(self.disconnect_client(client.client_id))
            return False

    async def _send_error(self, client_id: str, error_message: str) -> None:
        """
        Send an error message to a client
        """
        if client_id in self.clients:
            await self._send_to_client(self.clients[client_id], WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": error_message},
                timestamp=datetime.utcnow(),
                message_id=str(uuid.uuid4()),
                priority="high"
            ))

    async def _check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit
        """
        if client_id not in self.clients or client_id not in self.client_message_counts:
            return True

        client = self.clients[client_id]
        rate_info = self.client_message_counts[client_id]
        rate_limit = self.rate_limits.get(client.role.value, 10)

        now = datetime.utcnow()
        window_start = rate_info["window_start"]

        # Reset window if more than a minute has passed
        if now - window_start > timedelta(minutes=1):
            rate_info["count"] = 0
            rate_info["window_start"] = now

        # Check rate limit
        if rate_info["count"] >= rate_limit:
            return False

        rate_info["count"] += 1
        return True

    async def _broadcast_messages(self) -> None:
        """
        Background task to broadcast queued messages
        """
        while True:
            try:
                # Process high priority messages first
                while not self.high_priority_queue.empty():
                    message = await self.high_priority_queue.get()
                    await self.send_message(message)

                # Process normal priority messages
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.send_message(message)

            except asyncio.TimeoutError:
                # No messages, continue
                continue
            except Exception as e:
                logger.error(f"❌ Error in broadcast task: {str(e)}")
                await asyncio.sleep(1)

    async def _heartbeat_monitor(self) -> None:
        """
        Background task to monitor client connections and send heartbeats
        """
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                current_time = datetime.utcnow()
                disconnected_clients = []

                for client_id, client in self.clients.items():
                    # Check for timeout (5 minutes of inactivity)
                    if current_time - client.last_activity > timedelta(minutes=5):
                        disconnected_clients.append(client_id)
                    else:
                        # Send heartbeat
                        try:
                            await self._send_to_client(client, WebSocketMessage(
                                type=MessageType.HEARTBEAT,
                                data={"timestamp": current_time.isoformat()},
                                timestamp=current_time,
                                message_id=str(uuid.uuid4())
                            ))
                        except:
                            disconnected_clients.append(client_id)

                # Disconnect timed out clients
                for client_id in disconnected_clients:
                    await self.disconnect_client(client_id)

            except Exception as e:
                logger.error(f"❌ Error in heartbeat monitor: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get WebSocket manager statistics
        """
        role_counts = {}
        for client in self.clients.values():
            role_counts[client.role.value] = role_counts.get(client.role.value, 0) + 1

        subscription_counts = {}
        for client in self.clients.values():
            for sub in client.subscriptions:
                subscription_counts[sub.value] = subscription_counts.get(sub.value, 0) + 1

        return {
            **self.stats,
            "connections_by_role": role_counts,
            "connections_by_subscription": subscription_counts,
            "active_connections": len(self.clients),
            "background_tasks_running": {
                "broadcast": self.broadcast_task is not None,
                "heartbeat": self.heartbeat_task is not None
            }
        }

    async def cleanup(self) -> None:
        """
        Clean up all connections and stop background tasks
        """
        logger.info("🧹 Cleaning up WebSocket manager...")

        # Disconnect all clients
        client_ids = list(self.clients.keys())
        for client_id in client_ids:
            await self.disconnect_client(client_id)

        # Stop background tasks
        await self.stop_background_tasks()

        logger.info("✅ WebSocket manager cleanup completed")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()