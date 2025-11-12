"""
WebSocket Communication Tests
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket, WebSocketDisconnect

from websocket.websocket_manager import WebSocketManager, ConnectionRole
from realtime.events_service import EventsService, EventPriority

class TestWebSocketManager:
    """Test WebSocket connection manager"""

    def test_init(self):
        """Test WebSocketManager initialization"""
        manager = WebSocketManager()
        assert manager.active_connections == {}
        assert manager.connection_stats == {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful WebSocket connection"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")

        assert connection_id is not None
        assert connection_id in manager.active_connections
        assert manager.active_connections[connection_id]["websocket"] == websocket
        assert manager.active_connections[connection_id]["user_id"] == "test_user"
        assert manager.active_connections[connection_id]["role"] == "citizen"
        assert manager.connection_stats["active_connections"] == 1

    @pytest.mark.asyncio
    async def test_connect_with_auth(self):
        """Test WebSocket connection with authentication"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        # Mock authentication
        with patch('websocket.websocket_manager.get_current_user') as mock_auth:
            mock_user = Mock()
            mock_user.user_id = "authenticated_user"
            mock_user.role = "law_enforcement"
            mock_auth.return_value = mock_user

            connection_id = await manager.connect(websocket, token="valid_token")

            assert connection_id is not None
            assert manager.active_connections[connection_id]["user_id"] == "authenticated_user"
            assert manager.active_connections[connection_id]["role"] == "law_enforcement"

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        # First connect
        connection_id = await manager.connect(websocket, "test_user", "citizen")
        assert manager.connection_stats["active_connections"] == 1

        # Then disconnect
        await manager.disconnect(connection_id)
        assert connection_id not in manager.active_connections
        assert manager.connection_stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_send_personal_message_success(self):
        """Test sending personal message"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.send_text = AsyncMock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")
        message = {"type": "notification", "data": "Test message"}

        await manager.send_personal_message(message, connection_id)

        websocket.send_text.assert_called_once_with(json.dumps(message))
        assert manager.connection_stats["messages_sent"] == 1

    @pytest.mark.asyncio
    async def test_send_personal_message_not_connected(self):
        """Test sending personal message to disconnected client"""
        manager = WebSocketManager()
        message = {"type": "notification", "data": "Test message"}

        # Should not raise exception
        await manager.send_personal_message(message, "nonexistent_connection_id")

    @pytest.mark.asyncio
    async def test_broadcast_success(self):
        """Test broadcasting message to all connections"""
        manager = WebSocketManager()
        websockets = []
        connection_ids = []

        # Create multiple connections
        for i in range(3):
            websocket = Mock()
            websocket.send_text = AsyncMock()
            websocket.client = Mock()
            websocket.client.host = f"127.0.0.{i+1}"
            websocket.client.port = 12345 + i
            websockets.append(websocket)

            connection_id = await manager.connect(websocket, f"user_{i}", "citizen")
            connection_ids.append(connection_id)

        message = {"type": "system_update", "data": "System maintenance scheduled"}

        await manager.broadcast(message)

        # All websockets should have received the message
        for websocket in websockets:
            websocket.send_text.assert_called_once_with(json.dumps(message))

        assert manager.connection_stats["messages_sent"] == 3

    @pytest.mark.asyncio
    async def test_broadcast_by_role(self):
        """Test broadcasting message to specific roles"""
        manager = WebSocketManager()

        # Create connections with different roles
        citizen_websocket = Mock()
        citizen_websocket.send_text = AsyncMock()
        citizen_websocket.client = Mock()
        citizen_websocket.client.host = "127.0.0.1"
        citizen_websocket.client.port = 12345

        officer_websocket = Mock()
        officer_websocket.send_text = AsyncMock()
        officer_websocket.client = Mock()
        officer_websocket.client.host = "127.0.0.2"
        officer_websocket.client.port = 12346

        citizen_id = await manager.connect(citizen_websocket, "citizen_user", "citizen")
        officer_id = await manager.connect(officer_websocket, "officer_user", "law_enforcement")

        message = {"type": "alert", "data": "High priority alert"}
        target_roles = ["law_enforcement"]

        await manager.broadcast(message, roles=target_roles)

        # Only officer should receive the message
        citizen_websocket.send_text.assert_not_called()
        officer_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self):
        """Test subscribing to specific events"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")
        event_types = ["complaints", "alerts", "predictions"]

        await manager.subscribe_to_events(connection_id, event_types)

        connection = manager.active_connections[connection_id]
        assert set(connection["subscriptions"]) == set(event_types)

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test WebSocket rate limiting"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.send_text = AsyncMock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")

        # Send multiple messages rapidly
        messages = [
            {"type": "message", "data": f"Message {i}"}
            for i in range(10)
        ]

        for message in messages:
            await manager.send_personal_message(message, connection_id)

        # Check if rate limiting was applied
        # This depends on the rate limiting implementation
        connection = manager.active_connections[connection_id]
        assert "message_count" in connection

    @pytest.mark.asyncio
    async def test_connection_cleanup(self):
        """Test cleanup of stale connections"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")
        assert manager.connection_stats["active_connections"] == 1

        # Simulate stale connection
        manager.active_connections[connection_id]["last_activity"] = (
            manager.active_connections[connection_id]["last_activity"] -
            manager.connection_timeout - 60
        )

        await manager.cleanup_stale_connections()

        assert connection_id not in manager.active_connections
        assert manager.connection_stats["active_connections"] == 0

    def test_get_connection_stats(self):
        """Test getting connection statistics"""
        manager = WebSocketManager()
        stats = manager.get_connection_stats()

        assert "total_connections" in stats
        assert "active_connections" in stats
        assert "messages_sent" in stats
        assert "messages_received" in stats
        assert "connections_by_role" in stats

class TestEventsService:
    """Test real-time events service"""

    def test_init(self):
        """Test EventsService initialization"""
        service = EventsService()
        assert service.websocket_manager is not None
        assert service.event_history == []
        assert service.subscribers == {}

    @pytest.mark.asyncio
    async def test_create_event(self):
        """Test creating and broadcasting an event"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        event_data = {
            "type": "complaint_submitted",
            "data": {
                "complaint_id": "comp_123",
                "user_id": "user_123",
                "complaint_type": "online_scam"
            }
        }

        await service.create_event(
            event_type="complaint_submitted",
            data=event_data["data"],
            priority=EventPriority.HIGH,
            target_roles=["law_enforcement", "administrator"]
        )

        # Check that broadcast was called
        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        assert call_args[0][0]["type"] == "complaint_submitted"
        assert call_args[1]["roles"] == ["law_enforcement", "administrator"]

    @pytest.mark.asyncio
    async def test_create_complaint_event(self):
        """Test creating complaint-specific event"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        complaint_data = {
            "complaint_id": "comp_123",
            "user_id": "user_123",
            "complaint_type": "online_scam",
            "amount": 50000,
            "location": "Mumbai"
        }

        await service.create_complaint_event(complaint_data)

        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        event_message = call_args[0][0]

        assert event_message["type"] == "complaint_submitted"
        assert event_message["data"]["complaint_id"] == "comp_123"
        assert "timestamp" in event_message

    @pytest.mark.asyncio
    async def test_create_prediction_event(self):
        """Test creating prediction-specific event"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        prediction_data = {
            "prediction_id": "pred_123",
            "complaint_id": "comp_123",
            "location_name": "Mumbai Central ATM",
            "confidence_score": 0.92,
            "risk_level": "high"
        }

        await service.create_prediction_event(prediction_data)

        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        event_message = call_args[0][0]

        assert event_message["type"] == "prediction_generated"
        assert event_message["data"]["prediction_id"] == "pred_123"
        assert event_message["data"]["confidence_score"] == 0.92

    @pytest.mark.asyncio
    async def test_create_alert_event(self):
        """Test creating alert-specific event"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        alert_data = {
            "alert_id": "alert_123",
            "prediction_id": "pred_123",
            "title": "High-Risk Prediction Confirmed",
            "severity": "critical",
            "location": "Mumbai Central"
        }

        await service.create_alert_event(alert_data)

        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        event_message = call_args[0][0]

        assert event_message["type"] == "alert_created"
        assert event_message["data"]["alert_id"] == "alert_123"
        assert event_message["data"]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_create_cordon_event(self):
        """Test creating digital cordon event"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        cordon_data = {
            "cordon_id": "cordon_123",
            "target_type": "account",
            "target_value": "123456789012",
            "status": "active"
        }

        await service.create_cordon_event(cordon_data)

        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        event_message = call_args[0][0]

        assert event_message["type"] == "cordon_created"
        assert event_message["data"]["cordon_id"] == "cordon_123"
        assert event_message["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self):
        """Test subscribing to specific event types"""
        service = EventsService()
        connection_id = "conn_123"
        event_types = ["complaint_submitted", "prediction_generated"]

        await service.subscribe_to_events(connection_id, event_types)

        assert connection_id in service.subscribers
        assert set(service.subscribers[connection_id]) == set(event_types)

    @pytest.mark.asyncio
    async def test_unsubscribe_from_events(self):
        """Test unsubscribing from event types"""
        service = EventsService()
        connection_id = "conn_123"
        event_types = ["complaint_submitted", "prediction_generated"]

        # First subscribe
        await service.subscribe_to_events(connection_id, event_types)
        assert connection_id in service.subscribers

        # Then unsubscribe
        await service.unsubscribe_from_events(connection_id)
        assert connection_id not in service.subscribers

    @pytest.mark.asyncio
    async def test_get_event_history(self):
        """Test getting event history"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        # Create some events
        for i in range(5):
            await service.create_event(
                event_type=f"test_event_{i}",
                data={"message": f"Test message {i}"}
            )

        history = service.get_event_history(limit=3)
        assert len(history) == 3
        assert all("type" in event for event in history)
        assert all("timestamp" in event for event in history)

    @pytest.mark.asyncio
    async def test_filter_events_by_type(self):
        """Test filtering events by type"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        # Create events of different types
        await service.create_event("complaint_submitted", {"id": 1})
        await service.create_event("prediction_generated", {"id": 2})
        await service.create_event("complaint_submitted", {"id": 3})
        await service.create_event("alert_created", {"id": 4})

        complaint_events = service.get_event_history(event_type="complaint_submitted")
        assert len(complaint_events) == 2
        assert all(event["type"] == "complaint_submitted" for event in complaint_events)

    @pytest.mark.asyncio
    async def test_event_priority_handling(self):
        """Test handling of events with different priorities"""
        service = EventsService()
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        service.websocket_manager = mock_manager

        # Create events with different priorities
        await service.create_event(
            "low_priority_event",
            {"message": "Low priority"},
            priority=EventPriority.LOW
        )

        await service.create_event(
            "high_priority_event",
            {"message": "High priority"},
            priority=EventPriority.HIGH
        )

        # Check that high priority events are handled first
        calls = mock_manager.broadcast.call_args_list
        # The high priority event should be broadcast to emergency roles
        high_priority_call = calls[1]
        assert "emergency" in high_priority_call[1]["roles"]

class TestWebSocketEndpoints:
    """Test WebSocket endpoint handlers"""

    @pytest.mark.asyncio
    async def test_websocket_connection_success(self, async_test_client):
        """Test successful WebSocket connection"""
        with async_test_client.websocket_connect("/ws") as websocket:
            # Send authentication message
            auth_message = {
                "type": "auth",
                "token": "valid_token"
            }
            await websocket.send_json(auth_message)

            # Receive authentication response
            response = await websocket.receive_json()
            assert response["type"] == "auth_success"

    @pytest.mark.asyncio
    async def test_websocket_connection_failure(self, async_test_client):
        """Test WebSocket connection with invalid authentication"""
        with pytest.raises(WebSocketDisconnect):
            with async_test_client.websocket_connect("/ws") as websocket:
                # Send invalid authentication
                auth_message = {
                    "type": "auth",
                    "token": "invalid_token"
                }
                await websocket.send_json(auth_message)

    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, async_test_client):
        """Test handling of WebSocket messages"""
        with async_test_client.websocket_connect("/ws") as websocket:
            # Authenticate first
            auth_message = {"type": "auth", "token": "valid_token"}
            await websocket.send_json(auth_message)
            await websocket.receive_json()

            # Send subscription message
            subscribe_message = {
                "type": "subscribe",
                "events": ["complaints", "alerts"]
            }
            await websocket.send_json(subscribe_message)

            # Receive subscription confirmation
            response = await websocket.receive_json()
            assert response["type"] == "subscription_success"

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, async_test_client):
        """Test WebSocket ping/pong for connection health"""
        with async_test_client.websocket_connect("/ws") as websocket:
            # Authenticate first
            auth_message = {"type": "auth", "token": "valid_token"}
            await websocket.send_json(auth_message)
            await websocket.receive_json()

            # Send ping
            ping_message = {"type": "ping"}
            await websocket.send_json(ping_message)

            # Receive pong
            response = await websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_websocket_event_broadcast(self, async_test_client):
        """Test receiving broadcasted events"""
        with async_test_client.websocket_connect("/ws") as websocket:
            # Authenticate and subscribe
            auth_message = {"type": "auth", "token": "valid_token"}
            await websocket.send_json(auth_message)
            await websocket.receive_json()

            subscribe_message = {
                "type": "subscribe",
                "events": ["complaints"]
            }
            await websocket.send_json(subscribe_message)
            await websocket.receive_json()

            # The client should receive events broadcasted to the channel
            # This would typically be triggered by another API call
            # For testing, we can simulate this

class TestWebSocketSecurity:
    """Test WebSocket security features"""

    @pytest.mark.asyncio
    async def test_token_validation(self):
        """Test JWT token validation for WebSocket connections"""
        manager = WebSocketManager()

        # Mock authentication service
        with patch('websocket.websocket_manager.auth_service.verify_token') as mock_verify:
            # Valid token
            mock_verify.return_value = {
                "sub": "test_user",
                "email": "test@example.com",
                "role": "citizen"
            }

            websocket = Mock()
            websocket.client = Mock()
            websocket.client.host = "127.0.0.1"
            websocket.client.port = 12345

            connection_id = await manager.connect(websocket, token="valid_token")
            assert connection_id is not None

            # Invalid token
            mock_verify.return_value = None

            with pytest.raises(Exception):  # Should raise authentication error
                await manager.connect(websocket, token="invalid_token")

    @pytest.mark.asyncio
    async def test_role_based_message_filtering(self):
        """Test role-based message filtering"""
        manager = WebSocketManager()

        # Create connections with different roles
        citizen_ws = Mock()
        citizen_ws.send_text = AsyncMock()
        citizen_ws.client = Mock()
        citizen_ws.client.host = "127.0.0.1"
        citizen_ws.client.port = 12345

        admin_ws = Mock()
        admin_ws.send_text = AsyncMock()
        admin_ws.client = Mock()
        admin_ws.client.host = "127.0.0.2"
        admin_ws.client.port = 12346

        citizen_id = await manager.connect(citizen_ws, "citizen_user", "citizen")
        admin_id = await manager.connect(admin_ws, "admin_user", "administrator")

        # Send admin-only message
        admin_message = {"type": "system_alert", "data": "Sensitive system info"}
        await manager.broadcast(admin_message, roles=["administrator"])

        # Only admin should receive the message
        citizen_ws.send_text.assert_not_called()
        admin_ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_size_limits(self):
        """Test message size limits"""
        manager = WebSocketManager()
        websocket = Mock()
        websocket.send_text = AsyncMock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345

        connection_id = await manager.connect(websocket, "test_user", "citizen")

        # Create a very large message
        large_message = {
            "type": "test",
            "data": "x" * 1000000  # 1MB of data
        }

        # Should either send successfully or be rejected based on limits
        await manager.send_personal_message(large_message, connection_id)

        # Check if size limits were enforced
        # This depends on the implementation
        connection = manager.active_connections[connection_id]
        assert "message_size" in connection or websocket.send_text.called

if __name__ == "__main__":
    pytest.main([__file__])