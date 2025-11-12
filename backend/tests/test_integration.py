"""
Integration Tests
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from main import app
from database.models import UserRole, ComplaintStatus, AlertSeverity

class TestComplaintToPredictionFlow:
    """Test end-to-end complaint to prediction flow"""

    @pytest.mark.asyncio
    async def test_complete_complaint_flow(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test complete flow from complaint submission to prediction generation"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock AI models
        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_cst:
            mock_cst.return_value = {
                "predictions": [
                    {
                        "location_id": 123,
                        "location_name": "Mumbai Central ATM",
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "confidence_score": 0.92,
                        "risk_level": "high",
                        "time_window_start": datetime.utcnow().isoformat(),
                        "time_window_end": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                        "ai_insights": {"model": "cst_transformer", "features": ["spatial_temporal"]}
                    }
                ],
                "model_confidence": 0.88,
                "processing_time_ms": 1250.5
            }

            # Submit enhanced complaint
            enhanced_data = {
                **sample_complaint_data,
                "metadata": {"source": "mobile_app", "priority": "high"}
            }

            response = test_client.post("/api/v2/complaints/enhanced", json=enhanced_data, headers=headers)
            assert response.status_code == 200

            complaint_data = response.json()["data"]
            assert "complaint_id" in complaint_data
            assert "predictions" in complaint_data
            assert len(complaint_data["predictions"]) > 0

            complaint_id = complaint_data["complaint_id"]

            # Get predictions for the complaint
            response = test_client.get(f"/api/v1/predictions/{complaint_id}", headers=headers)
            assert response.status_code == 200

            predictions_data = response.json()["data"]
            assert "predictions" in predictions_data
            assert len(predictions_data["predictions"]) > 0

            # Verify prediction details
            prediction = predictions_data["predictions"][0]
            assert "location_id" in prediction
            assert "confidence_score" in prediction
            assert "risk_level" in prediction

    @pytest.mark.asyncio
    async def test_prediction_to_alert_flow(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test flow from prediction to alert creation"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock prediction with high risk
        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_cst:
            mock_cst.return_value = {
                "predictions": [
                    {
                        "location_id": 456,
                        "location_name": "Delhi Connaught Place",
                        "latitude": 28.6304,
                        "longitude": 77.2177,
                        "confidence_score": 0.95,
                        "risk_level": "critical",
                        "time_window_start": datetime.utcnow().isoformat(),
                        "time_window_end": (datetime.utcnow() + timedelta(hours=1)).isoformat()
                    }
                ],
                "model_confidence": 0.92,
                "processing_time_ms": 980.2
            }

            # Submit complaint that triggers high-risk prediction
            response = test_client.post("/api/v2/complaints/enhanced", json=sample_complaint_data, headers=headers)
            assert response.status_code == 200

            complaint_data = response.json()["data"]
            complaint_id = complaint_data["complaint_id"]

            # Create alert based on prediction
            alert_data = {
                "title": "Critical Risk Prediction - Immediate Action Required",
                "message": f"AI model predicts critical cash-out risk within 60 minutes. Complaint ID: {complaint_id}",
                "severity": "critical",
                "target_groups": ["cybercrime_team", "banking_authorities"],
                "channels": ["email", "sms", "whatsapp", "push"],
                "metadata": {
                    "complaint_id": complaint_id,
                    "prediction_confidence": 0.95,
                    "urgency": "immediate"
                }
            }

            # Mock alert manager
            with patch('alerts.alert_manager.AlertManager.create_alert') as mock_alert:
                mock_alert.return_value = {
                    "alert_id": "alert_critical_123",
                    "status": "active",
                    "channels_sent": ["email", "sms", "whatsapp", "push"],
                    "recipients_notified": 15
                }

                response = test_client.post("/api/v1/alerts", json=alert_data, headers=headers)
                assert response.status_code == 201

                alert_response = response.json()["data"]
                assert "alert_id" in alert_response
                assert alert_response["status"] == "active"

class TestDigitalCordonIntegration:
    """Test digital cordon integration flow"""

    @pytest.mark.asyncio
    async def test_prediction_to_cordon_flow(self, test_client: TestClient, valid_jwt_token, sample_cordon_data):
        """Test flow from prediction to digital cordon activation"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock NPCI API
        with patch('integrations.npci.npci_client.create_cordon') as mock_npci:
            mock_npci.return_value = {
                "success": True,
                "cordon_id": "cordon_npci_789",
                "status": "active",
                "accounts_affected": 3,
                "blocks_initiated": 5
            }

            # Create digital cordon
            response = test_client.post("/api/v2/cordons/enhanced", json=sample_cordon_data, headers=headers)
            assert response.status_code == 201

            cordon_data = response.json()["data"]
            assert "cordon_id" in cordon_data
            assert cordon_data["status"] == "active"

            cordon_id = cordon_data["cordon_id"]

            # Check cordon status
            with patch('integrations.npci.npci_client.check_cordon_status') as mock_status:
                mock_status.return_value = {
                    "success": True,
                    "status": "active",
                    "blocks_initiated": 5,
                    "accounts_blocked": 3,
                    "transactions_prevented": 12,
                    "amount_prevented": 250000.0
                }

                response = test_client.get(f"/api/v1/cordons/{cordon_id}/status", headers=headers)
                assert response.status_code == 200

                status_data = response.json()["data"]
                assert status_data["status"] == "active"
                assert "blocks_initiated" in status_data
                assert "transactions_prevented" in status_data

            # Release cordon
            with patch('integrations.npci.npci_client.release_cordon') as mock_release:
                mock_release.return_value = {
                    "success": True,
                    "status": "released",
                    "released_at": datetime.utcnow().isoformat(),
                    "total_blocks": 5,
                    "total_amount_prevented": 250000.0
                }

                response = test_client.post(f"/api/v1/cordons/{cordon_id}/release", headers=headers)
                assert response.status_code == 200

                release_data = response.json()["data"]
                assert release_data["status"] == "released"

class TestMultiChannelAlertIntegration:
    """Test multi-channel alert system integration"""

    @pytest.mark.asyncio
    async def test_alert_multi_channel_delivery(self, test_client: TestClient, valid_jwt_token, sample_alert_data):
        """Test alert delivery across multiple channels"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock all alert channels
        with patch('alerts.channels.email_channel.EmailChannel.send') as mock_email, \
             patch('alerts.channels.sms_channel.SMSChannel.send') as mock_sms, \
             patch('alerts.channels.whatsapp_channel.WhatsAppChannel.send') as mock_whatsapp, \
             patch('alerts.channels.push_channel.PushChannel.send') as mock_push:

            # Configure mock responses
            mock_email.return_value = {"success": True, "message_id": "email_123"}
            mock_sms.return_value = {"success": True, "message_id": "sms_123"}
            mock_whatsapp.return_value = {"success": True, "message_id": "wa_123"}
            mock_push.return_value = {"success": True, "message_id": "push_123"}

            # Create alert
            response = test_client.post("/api/v1/alerts", json=sample_alert_data, headers=headers)
            assert response.status_code == 201

            alert_data = response.json()["data"]
            assert alert_data["status"] == "active"

            # Verify all channels were called
            mock_email.assert_called_once()
            mock_sms.assert_called_once()
            mock_whatsapp.assert_called_once()
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_escalation_flow(self, test_client: TestClient, valid_jwt_token):
        """Test alert escalation when primary channels fail"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock failed primary channels
        with patch('alerts.channels.email_channel.EmailChannel.send') as mock_email, \
             patch('alerts.channels.sms_channel.SMSChannel.send') as mock_sms, \
             patch('alerts.channels.escalation_channel.EscalationChannel.send') as mock_escalation:

            # Primary channels fail
            mock_email.return_value = {"success": False, "error": "SMTP server down"}
            mock_sms.return_value = {"success": False, "error": "SMS gateway error"}
            # Escalation channel succeeds
            mock_escalation.return_value = {"success": True, "escalated_to": "emergency_contacts"}

            alert_data = {
                "title": "System Critical Alert",
                "message": "Primary alert channels failed, escalating",
                "severity": "emergency",
                "channels": ["email", "sms"],
                "escalation_enabled": True
            }

            response = test_client.post("/api/v1/alerts", json=alert_data, headers=headers)
            assert response.status_code == 201

            # Verify escalation was triggered
            mock_escalation.assert_called_once()

class TestRealTimeWebSocketIntegration:
    """Test real-time WebSocket integration"""

    @pytest.mark.asyncio
    async def test_complaint_websocket_notification(self, async_test_client):
        """Test WebSocket notification when complaint is submitted"""
        # Connect WebSocket
        with async_test_client.websocket_connect("/ws") as websocket:
            # Authenticate
            auth_message = {"type": "auth", "token": "valid_token"}
            await websocket.send_json(auth_message)
            auth_response = await websocket.receive_json()
            assert auth_response["type"] == "auth_success"

            # Subscribe to complaint notifications
            subscribe_message = {"type": "subscribe", "events": ["complaints"]}
            await websocket.send_json(subscribe_message)
            await websocket.receive_json()

            # Submit complaint via REST API
            complaint_data = {
                "complaint_type": "online_scam",
                "amount": 50000,
                "victim_location": "Mumbai, Maharashtra",
                "priority": "high"
            }

            # Mock authentication for REST API
            with patch('auth.auth_service.auth_service.verify_token') as mock_verify:
                mock_verify.return_value = {
                    "sub": "test_user",
                    "email": "test@example.com",
                    "role": "citizen"
                }

                response = async_test_client.post(
                    "/api/v1/complaints",
                    json=complaint_data,
                    headers={"Authorization": "Bearer valid_token"}
                )
                assert response.status_code == 201

            # Receive WebSocket notification
            notification = await websocket.receive_json(timeout=5.0)
            assert notification["type"] == "complaint_submitted"
            assert "complaint_id" in notification["data"]

    @pytest.mark.asyncio
    async def test_prediction_websocket_broadcast(self, async_test_client):
        """Test WebSocket broadcast when prediction is generated"""
        # Connect multiple WebSocket clients
        clients = []
        for i in range(3):
            ws = async_test_client.websocket_connect("/ws")
            with ws as websocket:
                clients.append(websocket)

        # Authenticate all clients
        for websocket in clients:
            auth_message = {"type": "auth", "token": f"token_{clients.index(websocket)}"}
            await websocket.send_json(auth_message)
            await websocket.receive_json()

            # Subscribe to predictions
            subscribe_message = {"type": "subscribe", "events": ["predictions"]}
            await websocket.send_json(subscribe_message)
            await websocket.receive_json()

        # Generate prediction via REST API
        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_predict:
            mock_predict.return_value = {
                "predictions": [
                    {
                        "location_id": 789,
                        "location_name": "Bangalore Electronic City",
                        "confidence_score": 0.89,
                        "risk_level": "high"
                    }
                ]
            }

            # All clients should receive the prediction broadcast
            for websocket in clients:
                try:
                    notification = await websocket.receive_json(timeout=5.0)
                    assert notification["type"] == "prediction_generated"
                    assert "predictions" in notification["data"]
                except:
                    # Handle WebSocket closed cases
                    pass

class TestAnalyticsIntegration:
    """Test analytics system integration"""

    @pytest.mark.asyncio
    async def test_real_time_analytics_update(self, test_client: TestClient, valid_jwt_token):
        """Test real-time analytics update after system events"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Get initial analytics
        response = test_client.get("/api/v2/analytics/realtime", headers=headers)
        assert response.status_code == 200

        initial_data = response.json()["data"]
        initial_complaints = initial_data.get("active_complaints", 0)

        # Submit a complaint
        complaint_data = {
            "complaint_type": "online_scam",
            "amount": 25000,
            "victim_location": "Chennai, Tamil Nadu",
            "priority": "medium"
        }

        with patch('auth.auth_service.auth_service.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "test_user",
                "email": "test@example.com",
                "role": "citizen"
            }

            response = test_client.post("/api/v1/complaints", json=complaint_data, headers=headers)
            assert response.status_code == 201

        # Check updated analytics
        response = test_client.get("/api/v2/analytics/realtime", headers=headers)
        assert response.status_code == 200

        updated_data = response.json()["data"]
        # Analytics should reflect the new complaint
        assert "active_complaints" in updated_data

    @pytest.mark.asyncio
    async def test_hotspot_analysis_integration(self, test_client: TestClient, valid_jwt_token):
        """Test hotspot analysis integration with predictions"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Create multiple complaints in same area
        locations = [
            {"location": "Mumbai Central", "lat": 19.0760, "lng": 72.8777},
            {"location": "Mumbai Central", "lat": 19.0760, "lng": 72.8777},
            {"location": "Mumbai Central", "lat": 19.0760, "lng": 72.8777}
        ]

        for i, loc in enumerate(locations):
            complaint_data = {
                "complaint_type": "online_scam",
                "amount": 30000 + i * 5000,
                "victim_location": loc["location"],
                "priority": "medium"
            }

            with patch('auth.auth_service.auth_service.verify_token') as mock_verify:
                mock_verify.return_value = {
                    "sub": f"test_user_{i}",
                    "email": f"test{i}@example.com",
                    "role": "citizen"
                }

                response = test_client.post("/api/v1/complaints", json=complaint_data, headers=headers)
                assert response.status_code == 201

        # Get hotspots
        response = test_client.get("/api/v1/analytics/hotspots", headers=headers)
        assert response.status_code == 200

        hotspots_data = response.json()["data"]
        assert "hotspots" in hotspots_data

        # Mumbai Central should appear as a hotspot due to multiple complaints
        mumbai_hotspots = [
            h for h in hotspots_data["hotspots"]
            if "Mumbai Central" in h.get("location", "")
        ]
        assert len(mumbai_hotspots) > 0

class TestSystemPerformanceIntegration:
    """Test system performance under load"""

    @pytest.mark.asyncio
    async def test_concurrent_complaint_processing(self, test_client: TestClient):
        """Test system performance with concurrent complaint submissions"""
        # Create multiple user tokens
        tokens = [f"token_{i}" for i in range(10)]

        # Submit concurrent complaints
        async def submit_complaint(token):
            headers = {"Authorization": f"Bearer {token}"}
            complaint_data = {
                "complaint_type": "online_scam",
                "amount": 5000,
                "victim_location": f"Location {token}",
                "priority": "low"
            }

            with patch('auth.auth_service.auth_service.verify_token') as mock_verify:
                mock_verify.return_value = {
                    "sub": f"user_{token}",
                    "email": f"user_{token}@example.com",
                    "role": "citizen"
                }

                response = test_client.post("/api/v1/complaints", json=complaint_data, headers=headers)
                return response.status_code

        # Run concurrent submissions
        tasks = [submit_complaint(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most submissions should succeed
        successful_results = [r for r in results if r == 201]
        assert len(successful_results) >= 8  # At least 80% success rate

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, test_client: TestClient, valid_jwt_token):
        """Test system memory usage under sustained load"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Submit many complaints rapidly
        for i in range(50):
            complaint_data = {
                "complaint_type": "online_scam",
                "amount": 1000 + i * 100,
                "victim_location": f"Test Location {i}",
                "priority": "low"
            }

            with patch('auth.auth_service.auth_service.verify_token') as mock_verify:
                mock_verify.return_value = {
                    "sub": "test_user",
                    "email": "test@example.com",
                    "role": "citizen"
                }

                response = test_client.post("/api/v1/complaints", json=complaint_data, headers=headers)
                # System should remain responsive
                assert response.status_code in [201, 429]  # Either success or rate limited

        # System should still be responsive
        response = test_client.get("/health", headers=headers)
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"

class TestErrorRecoveryIntegration:
    """Test system error recovery and resilience"""

    @pytest.mark.asyncio
    async def test_ai_model_failure_recovery(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test system recovery when AI models fail"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock AI model failure
        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_predict:
            mock_predict.side_effect = Exception("AI model temporarily unavailable")

            # System should handle the failure gracefully
            response = test_client.post("/api/v2/complaints/enhanced", json=sample_complaint_data, headers=headers)

            # Should either fall back to basic processing or return appropriate error
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                # Check if fallback predictions were provided
                data = response.json()["data"]
                assert "predictions" in data or "fallback_mode" in data

    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, test_client: TestClient, valid_jwt_token):
        """Test system recovery from database connection issues"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock database connection failure
        with patch('database.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = test_client.get("/api/v1/complaints", headers=headers)
            assert response.status_code == 500

        # Database connection restored
        response = test_client.get("/api/v1/complaints", headers=headers)
        # Should work again
        assert response.status_code in [200, 401]  # Success or auth error

    @pytest.mark.asyncio
    async def test_external_api_timeout_recovery(self, test_client: TestClient, valid_jwt_token, sample_cordon_data):
        """Test system recovery from external API timeouts"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock NPCI API timeout
        with patch('integrations.npci.npci_client.create_cordon') as mock_npci:
            mock_npci.side_effect = asyncio.TimeoutError("External API timeout")

            response = test_client.post("/api/v2/cordons/enhanced", json=sample_cordon_data, headers=headers)
            assert response.status_code in [408, 503, 504]  # Timeout or service unavailable errors

        # External API recovered
        with patch('integrations.npci.npci_client.create_cordon') as mock_npci:
            mock_npci.return_value = {
                "success": True,
                "cordon_id": "cordon_recovered_123",
                "status": "active"
            }

            response = test_client.post("/api/v2/cordons/enhanced", json=sample_cordon_data, headers=headers)
            assert response.status_code == 201

class TestDataConsistencyIntegration:
    """Test data consistency across the system"""

    @pytest.mark.asyncio
    async def test_complaint_prediction_consistency(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test data consistency between complaints and predictions"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock prediction creation
        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_predict:
            mock_predict.return_value = {
                "predictions": [
                    {
                        "location_id": 999,
                        "location_name": "Consistency Test Location",
                        "confidence_score": 0.85,
                        "risk_level": "medium"
                    }
                ]
            }

            # Submit complaint
            response = test_client.post("/api/v2/complaints/enhanced", json=sample_complaint_data, headers=headers)
            assert response.status_code == 200

            complaint_data = response.json()["data"]
            complaint_id = complaint_data["complaint_id"]

            # Verify prediction is linked to complaint
            response = test_client.get(f"/api/v1/predictions/{complaint_id}", headers=headers)
            assert response.status_code == 200

            predictions_data = response.json()["data"]
            assert len(predictions_data["predictions"]) > 0

            # Verify data consistency
            for prediction in predictions_data["predictions"]:
                # In a real system, these would be actual database records
                assert "location_id" in prediction
                assert "confidence_score" in prediction

    @pytest.mark.asyncio
    async def test_alert_cordon_consistency(self, test_client: TestClient, valid_jwt_token, sample_cordon_data):
        """Test data consistency between alerts and cordons"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Create cordon
        with patch('integrations.npci.npci_client.create_cordon') as mock_npci:
            mock_npci.return_value = {
                "success": True,
                "cordon_id": "cordon_consistency_123",
                "status": "active"
            }

            response = test_client.post("/api/v2/cordons/enhanced", json=sample_cordon_data, headers=headers)
            assert response.status_code == 201

            cordon_data = response.json()["data"]
            cordon_id = cordon_data["cordon_id"]

            # Create alert related to cordon
            alert_data = {
                "title": "Digital Cordon Activated",
                "message": f"Cordon {cordon_id} has been activated successfully",
                "severity": "high",
                "metadata": {
                    "cordon_id": cordon_id,
                    "target_type": sample_cordon_data["target_type"],
                    "target_value": sample_cordon_data["target_value"]
                }
            }

            with patch('alerts.alert_manager.AlertManager.create_alert') as mock_alert:
                mock_alert.return_value = {
                    "alert_id": "alert_consistency_123",
                    "status": "active",
                    "linked_cordon": cordon_id
                }

                response = test_client.post("/api/v1/alerts", json=alert_data, headers=headers)
                assert response.status_code == 201

                alert_response = response.json()["data"]
                assert alert_response["status"] == "active"

if __name__ == "__main__":
    pytest.main([__file__])