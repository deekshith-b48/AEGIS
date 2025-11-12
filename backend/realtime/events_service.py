"""
Real-Time Events Service for Project AEGIS
Handles real-time event broadcasting and notifications
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from websocket.websocket_manager import websocket_manager, MessageType, SubscriptionType, ClientRole

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for real-time updates"""
    # Prediction events
    PREDICTION_CREATED = "prediction_created"
    PREDICTION_UPDATED = "prediction_updated"
    PREDICTION_EXPIRED = "prediction_expired"

    # Cordon events
    CORDON_ACTIVATED = "cordon_activated"
    CORDON_UPDATED = "cordon_updated"
    CORDON_EXPIRED = "cordon_expired"
    CORDON_EXTENDED = "cordon_extended"

    # Alert events
    ALERT_CREATED = "alert_created"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_ESCALATED = "alert_escalated"
    ALERT_RESOLVED = "alert_resolved"

    # System events
    SYSTEM_STATUS_CHANGE = "system_status_change"
    MODEL_PERFORMANCE_UPDATE = "model_performance_update"
    DATABASE_UPDATE = "database_update"

    # Analytics events
    METRICS_UPDATE = "metrics_update"
    PERFORMANCE_SPIKE = "performance_spike"
    ANOMALY_DETECTED = "anomaly_detected"

    # GIS events
    LOCATION_HOTSPOT = "location_hotspot"
    PATTERN_DETECTED = "pattern_detected"
    GEO_FENCE_BREACH = "geo_fence_breach"

    # Learning events
    MODEL_RETRAINED = "model_retrained"
    ACCURACY_IMPROVED = "accuracy_improved"
    NEW_INSIGHT_DISCOVERED = "new_insight_discovered"

class EventPriority(Enum):
    """Event priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class RealTimeEvent:
    """Real-time event structure"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    data: Dict[str, Any]
    source: str
    timestamp: datetime
    expires_at: Optional[datetime] = None
    target_roles: List[ClientRole] = None
    target_users: List[str] = None
    subscription_type: SubscriptionType = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.target_roles is None:
            self.target_roles = []
        if self.metadata is None:
            self.metadata = {}

class EventsService:
    """
    Real-time events service for Project AEGIS
    Manages event creation, filtering, and distribution
    """

    def __init__(self):
        # Event storage
        self.active_events: Dict[str, RealTimeEvent] = {}
        self.event_history: List[RealTimeEvent] = []
        self.event_subscribers: Dict[EventType, List[str]] = {}  # event_type -> user_ids

        # Event statistics
        self.event_stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_priority": {},
            "events_by_hour": {},
            "recent_events": []
        }

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None

        # Event processors
        self.event_processors: Dict[EventType, List[callable]] = {}

    async def start(self) -> None:
        """Start the events service"""
        logger.info("🚀 Starting Real-Time Events Service...")

        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_events())

        # Register default event processors
        await self._register_default_processors()

        logger.info("✅ Real-Time Events Service started")

    async def stop(self) -> None:
        """Stop the events service"""
        logger.info("🛑 Stopping Real-Time Events Service...")

        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None

        logger.info("✅ Real-Time Events Service stopped")

    async def create_event(self, event_type: EventType, data: Dict[str, Any],
                          source: str, priority: EventPriority = EventPriority.NORMAL,
                          target_roles: List[ClientRole] = None,
                          target_users: List[str] = None,
                          subscription_type: SubscriptionType = None,
                          expires_in_minutes: int = None,
                          metadata: Dict[str, Any] = None) -> str:
        """
        Create and broadcast a real-time event
        """
        try:
            event_id = f"evt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.active_events):04d}"
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(minutes=expires_in_minutes) if expires_in_minutes else None

            event = RealTimeEvent(
                event_id=event_id,
                event_type=event_type,
                priority=priority,
                data=data,
                source=source,
                timestamp=created_at,
                expires_at=expires_at,
                target_roles=target_roles or [],
                target_users=target_users or [],
                subscription_type=subscription_type,
                metadata=metadata or {}
            )

            # Store event
            self.active_events[event_id] = event
            self.event_history.append(event)

            # Update statistics
            self._update_statistics(event)

            # Process event
            await self._process_event(event)

            # Broadcast event
            await self._broadcast_event(event)

            logger.debug(f"📡 Event created: {event_type.value} - {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"❌ Error creating event: {str(e)}")
            raise

    async def subscribe_to_events(self, user_id: str, event_types: List[EventType]) -> None:
        """
        Subscribe a user to specific event types
        """
        for event_type in event_types:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            if user_id not in self.event_subscribers[event_type]:
                self.event_subscribers[event_type].append(user_id)

        logger.info(f"📝 User {user_id} subscribed to {len(event_types)} event types")

    async def unsubscribe_from_events(self, user_id: str, event_types: List[EventType] = None) -> None:
        """
        Unsubscribe a user from event types
        """
        if event_types is None:
            # Unsubscribe from all events
            for event_type, subscribers in self.event_subscribers.items():
                if user_id in subscribers:
                    subscribers.remove(user_id)
        else:
            # Unsubscribe from specific event types
            for event_type in event_types:
                if event_type in self.event_subscribers and user_id in self.event_subscribers[event_type]:
                    self.event_subscribers[event_type].remove(user_id)

        logger.info(f"📝 User {user_id} unsubscribed from events")

    async def register_event_processor(self, event_type: EventType, processor: callable) -> None:
        """
        Register a processor function for specific event types
        """
        if event_type not in self.event_processors:
            self.event_processors[event_type] = []
        self.event_processors[event_type].append(processor)

        logger.debug(f"📝 Registered processor for {event_type.value}")

    async def get_active_events(self, event_type: EventType = None,
                              priority: EventPriority = None,
                              limit: int = 100) -> List[RealTimeEvent]:
        """
        Get active events with optional filtering
        """
        events = list(self.active_events.values())

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Filter by priority
        if priority:
            events = [e for e in events if e.priority == priority]

        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_event_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get event statistics for the specified time period
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_events = [e for e in self.event_history if e.timestamp >= cutoff_time]

        # Calculate statistics
        stats = {
            "total_events": len(recent_events),
            "events_by_type": {},
            "events_by_priority": {},
            "events_by_hour": {},
            "top_sources": {},
            "average_events_per_hour": len(recent_events) / max(1, hours_back),
            "period_hours": hours_back
        }

        for event in recent_events:
            # By type
            event_type = event.event_type.value
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1

            # By priority
            priority = event.priority.value
            stats["events_by_priority"][priority] = stats["events_by_priority"].get(priority, 0) + 1

            # By hour
            hour = event.timestamp.strftime("%Y-%m-%d %H:00")
            stats["events_by_hour"][hour] = stats["events_by_hour"].get(hour, 0) + 1

            # By source
            source = event.source
            stats["top_sources"][source] = stats["top_sources"].get(source, 0) + 1

        # Sort top sources
        stats["top_sources"] = dict(sorted(stats["top_sources"].items(), key=lambda x: x[1], reverse=True)[:10])

        return stats

    async def _process_event(self, event: RealTimeEvent) -> None:
        """
        Process an event through registered processors
        """
        try:
            # Call registered processors for this event type
            if event.event_type in self.event_processors:
                for processor in self.event_processors[event.event_type]:
                    try:
                        await processor(event)
                    except Exception as e:
                        logger.error(f"❌ Error in event processor: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Error processing event {event.event_id}: {str(e)}")

    async def _broadcast_event(self, event: RealTimeEvent) -> None:
        """
        Broadcast an event to subscribed clients
        """
        try:
            # Determine message type
            message_type_map = {
                EventType.PREDICTION_CREATED: MessageType.NEW_PREDICTION,
                EventType.PREDICTION_UPDATED: MessageType.PREDICTION_UPDATED,
                EventType.CORDON_ACTIVATED: MessageType.CORDON_ACTIVATED,
                EventType.CORDON_UPDATED: MessageType.CORDON_UPDATED,
                EventType.CORDON_EXPIRED: MessageType.CORDON_EXPIRED,
                EventType.ALERT_CREATED: MessageType.ALERT_CREATED,
                EventType.ALERT_ACKNOWLEDGED: MessageType.ALERT_ACKNOWLEDGED,
                EventType.ALERT_RESOLVED: MessageType.ALERT_RESOLVED,
                EventType.SYSTEM_STATUS_CHANGE: MessageType.SYSTEM_STATUS,
                EventType.MODEL_PERFORMANCE_UPDATE: MessageType.MODEL_PERFORMANCE,
                EventType.LOCATION_HOTSPOT: MessageType.HOTSPOT_DETECTED,
                EventType.MODEL_RETRAINED: MessageType.MODEL_RETRAINED,
            }

            message_type = message_type_map.get(event.event_type, MessageType.ANALYTICS_UPDATE)

            # Add subscribers to target users
            if event.event_type in self.event_subscribers:
                event.target_users.extend(self.event_subscribers[event.event_type])

            # Broadcast via WebSocket manager
            await websocket_manager.broadcast(
                message_type=message_type,
                data={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "priority": event.priority.value,
                    "source": event.source,
                    "data": event.data,
                    "metadata": event.metadata
                },
                subscription_type=event.subscription_type,
                priority=event.priority.value
            )

        except Exception as e:
            logger.error(f"❌ Error broadcasting event {event.event_id}: {str(e)}")

    async def _cleanup_expired_events(self) -> None:
        """
        Background task to clean up expired events
        """
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                current_time = datetime.utcnow()
                expired_events = []

                for event_id, event in self.active_events.items():
                    if event.expires_at and event.expires_at <= current_time:
                        expired_events.append(event_id)

                # Remove expired events
                for event_id in expired_events:
                    event = self.active_events.pop(event_id, None)
                    if event:
                        logger.debug(f"🗑️ Expired event cleaned up: {event_id}")

            except Exception as e:
                logger.error(f"❌ Error in event cleanup: {str(e)}")

    def _update_statistics(self, event: RealTimeEvent) -> None:
        """
        Update event statistics
        """
        self.event_stats["total_events"] += 1

        # By type
        event_type = event.event_type.value
        self.event_stats["events_by_type"][event_type] = self.event_stats["events_by_type"].get(event_type, 0) + 1

        # By priority
        priority = event.priority.value
        self.event_stats["events_by_priority"][priority] = self.event_stats["events_by_priority"].get(priority, 0) + 1

        # By hour
        hour = event.timestamp.strftime("%Y-%m-%d %H:00")
        self.event_stats["events_by_hour"][hour] = self.event_stats["events_by_hour"].get(hour, 0) + 1

        # Recent events (keep last 100)
        self.event_stats["recent_events"].append({
            "event_id": event.event_id,
            "type": event.event_type.value,
            "priority": event.priority.value,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })

        if len(self.event_stats["recent_events"]) > 100:
            self.event_stats["recent_events"] = self.event_stats["recent_events"][-100:]

    async def _register_default_processors(self) -> None:
        """
        Register default event processors
        """
        # Critical alert processor
        async def critical_alert_processor(event: RealTimeEvent):
            if event.priority in [EventPriority.CRITICAL, EventPriority.EMERGENCY]:
                # Send immediate high-priority notifications
                await websocket_manager.broadcast(
                    message_type=MessageType.ALERT_CREATED,
                    data={
                        "critical_alert": True,
                        "event_data": event.data,
                        "immediate_action_required": True
                    },
                    priority="critical"
                )

        # System status processor
        async def system_status_processor(event: RealTimeEvent):
            if event.event_type == EventType.SYSTEM_STATUS_CHANGE:
                # Update system status for all clients
                await websocket_manager.broadcast(
                    message_type=MessageType.SYSTEM_STATUS,
                    data=event.data,
                    subscription_type=SubscriptionType.ALL
                )

        # Model performance processor
        async def model_performance_processor(event: RealTimeEvent):
            if event.event_type == EventType.MODEL_PERFORMANCE_UPDATE:
                # Update performance metrics for analytics clients
                await websocket_manager.broadcast(
                    message_type=MessageType.MODEL_PERFORMANCE,
                    data=event.data,
                    subscription_type=SubscriptionType.ANALYTICS
                )

        # Register processors
        await self.register_event_processor(EventType.ALERT_CREATED, critical_alert_processor)
        await self.register_event_processor(EventType.SYSTEM_STATUS_CHANGE, system_status_processor)
        await self.register_event_processor(EventType.MODEL_PERFORMANCE_UPDATE, model_performance_processor)

        logger.info("📝 Default event processors registered")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get events service status
        """
        return {
            "status": "operational",
            "active_events": len(self.active_events),
            "total_events_processed": self.event_stats["total_events"],
            "event_types_supported": len(EventType),
            "subscribers": {
                event_type: len(subscribers) for event_type, subscribers in self.event_subscribers.items()
            },
            "background_tasks": {
                "cleanup_running": self.cleanup_task is not None
            },
            "statistics": self.event_stats
        }

# Global events service instance
events_service = EventsService()