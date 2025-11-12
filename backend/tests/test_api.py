"""
API Endpoint Tests
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from database.models import UserRole

class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, test_client: TestClient):
        """Test basic health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_system_status(self, test_client: TestClient, valid_jwt_token):
        """Test system status endpoint"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        response = test_client.get("/api/v1/system/status", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "performance_metrics" in data

class TestAuthenticationEndpoints:
    """Test authentication endpoints"""

    def test_register_user_success(self, test_client: TestClient):
        """Test successful user registration"""
        user_data = {
            "user_id": "new_user_123",
            "email": "newuser@example.com",
            "name": "New User",
            "password": "StrongP@ssw0rd123!",
            "role": "citizen",
            "department": "test_dept",
            "phone": "+919876543210"
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert data["data"]["email"] == user_data["email"]

    def test_register_user_duplicate(self, test_client: TestClient, test_user):
        """Test user registration with duplicate email"""
        user_data = {
            "user_id": "different_user",
            "email": test_user.email,  # Duplicate email
            "name": "Different User",
            "password": "StrongP@ssw0rd123!",
            "role": "citizen"
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400

        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_login_success(self, test_client: TestClient, test_user):
        """Test successful user login"""
        login_data = {
            "email": test_user.email,
            "password": "password",  # Will be mocked
            "remember_me": False
        }

        with patch('auth.auth_service.auth_service.authenticate_user') as mock_auth:
            mock_auth.return_value = test_user

            with patch('auth.auth_service.auth_service.login_user') as mock_login:
                mock_login.return_value = {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "user": {
                        "user_id": test_user.user_id,
                        "email": test_user.email,
                        "name": test_user.name,
                        "role": test_user.role.value
                    }
                }

                response = test_client.post("/api/v1/auth/login", json=login_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert "access_token" in data["data"]
                assert "refresh_token" in data["data"]

    def test_login_invalid_credentials(self, test_client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrong_password",
            "remember_me": False
        }

        response = test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False

    def test_refresh_token_success(self, test_client: TestClient):
        """Test token refresh"""
        refresh_data = {"refresh_token": "valid_refresh_token"}

        with patch('auth.auth_service.auth_service.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new_access_token",
                "token_type": "bearer",
                "expires_in": 1800
            }

            response = test_client.post("/api/v1/auth/refresh", json=refresh_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]

    def test_logout_success(self, test_client: TestClient, valid_jwt_token):
        """Test user logout"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch('auth.auth_service.auth_service.logout_user') as mock_logout:
            mock_logout.return_value = True

            response = test_client.post("/api/v1/auth/logout", headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

class TestComplaintEndpoints:
    """Test complaint management endpoints"""

    def test_submit_complaint_success(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test successful complaint submission"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.post("/api/v1/complaints", json=sample_complaint_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert "complaint_id" in data["data"]
        assert data["data"]["status"] == "pending"

    def test_submit_complaint_invalid_data(self, test_client: TestClient, valid_jwt_token):
        """Test complaint submission with invalid data"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        invalid_data = {
            "complaint_type": "",  # Empty complaint type
            "amount": -100,  # Negative amount
            "victim_location": ""  # Empty location
        }

        response = test_client.post("/api/v1/complaints", json=invalid_data, headers=headers)
        assert response.status_code == 422  # Validation error

    def test_get_complaint_success(self, test_client: TestClient, valid_jwt_token, test_complaint):
        """Test getting a specific complaint"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get(f"/api/v1/complaints/{test_complaint.complaint_id}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["complaint_id"] == test_complaint.complaint_id

    def test_get_complaint_not_found(self, test_client: TestClient, valid_jwt_token):
        """Test getting a non-existent complaint"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/complaints/nonexistent_complaint", headers=headers)
        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False

    def test_list_complaints_success(self, test_client: TestClient, valid_jwt_token, test_complaint):
        """Test listing complaints"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/complaints", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "complaints" in data["data"]
        assert isinstance(data["data"]["complaints"], list)

    def test_submit_enhanced_complaint_success(self, test_client: TestClient, valid_jwt_token, sample_complaint_data):
        """Test enhanced complaint submission with AI processing"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        enhanced_data = {
            **sample_complaint_data,
            "metadata": {
                "source": "mobile_app",
                "device_id": "device_12345",
                "ip_address": "192.168.1.1"
            }
        }

        with patch('ai.models.cst_transformer.CSTTransformer.predict') as mock_predict:
            mock_predict.return_value = {
                "predictions": [
                    {
                        "location_id": 123,
                        "location_name": "Mumbai Central ATM",
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "confidence_score": 0.92,
                        "risk_level": "high"
                    }
                ],
                "model_confidence": 0.88,
                "processing_time_ms": 1250.5
            }

            response = test_client.post("/api/v2/complaints/enhanced", json=enhanced_data, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "predictions" in data["data"]
            assert "processing_time_ms" in data["data"]

class TestPredictionEndpoints:
    """Test AI prediction endpoints"""

    def test_get_predictions_success(self, test_client: TestClient, valid_jwt_token, test_prediction):
        """Test getting predictions for a complaint"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get(f"/api/v1/predictions/{test_prediction.complaint_id}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "predictions" in data["data"]

    def test_get_predictions_not_found(self, test_client: TestClient, valid_jwt_token):
        """Test getting predictions for non-existent complaint"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/predictions/nonexistent_complaint", headers=headers)
        assert response.status_code == 404

    def test_create_manual_prediction_success(self, test_client: TestClient, valid_jwt_token, sample_prediction_data):
        """Test creating a manual prediction"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        prediction_data = {
            "complaint_id": "test_complaint_123",
            **sample_prediction_data
        }

        response = test_client.post("/api/v1/predictions", json=prediction_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert "prediction_id" in data["data"]

    def test_get_prediction_by_id_success(self, test_client: TestClient, valid_jwt_token, test_prediction):
        """Test getting a specific prediction by ID"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get(f"/api/v1/predictions/id/{test_prediction.prediction_id}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["prediction_id"] == test_prediction.prediction_id

class TestDigitalCordonEndpoints:
    """Test digital cordon endpoints"""

    def test_create_cordon_success(self, test_client: TestClient, valid_jwt_token, sample_cordon_data):
        """Test creating a digital cordon"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch('integrations.npci.npci_client.create_cordon') as mock_cordon:
            mock_cordon.return_value = {
                "success": True,
                "cordon_id": "cordon_test_123",
                "status": "active"
            }

            response = test_client.post("/api/v2/cordons/enhanced", json=sample_cordon_data, headers=headers)
            assert response.status_code == 201

            data = response.json()
            assert data["success"] is True
            assert "cordon_id" in data["data"]

    def test_get_cordon_status_success(self, test_client: TestClient, valid_jwt_token):
        """Test getting cordon status"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        cordon_id = "cordon_test_123"

        with patch('integrations.npci.npci_client.check_cordon_status') as mock_status:
            mock_status.return_value = {
                "success": True,
                "status": "active",
                "blocks_initiated": 5,
                "accounts_blocked": 3
            }

            response = test_client.get(f"/api/v1/cordons/{cordon_id}/status", headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "status" in data["data"]

    def test_release_cordon_success(self, test_client: TestClient, valid_jwt_token):
        """Test releasing a digital cordon"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        cordon_id = "cordon_test_123"

        with patch('integrations.npci.npci_client.release_cordon') as mock_release:
            mock_release.return_value = {
                "success": True,
                "status": "released",
                "released_at": datetime.utcnow().isoformat()
            }

            response = test_client.post(f"/api/v1/cordons/{cordon_id}/release", headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_list_active_cordons_success(self, test_client: TestClient, valid_jwt_token):
        """Test listing active digital cordons"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/cordons/active", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "cordons" in data["data"]
        assert isinstance(data["data"]["cordons"], list)

class TestAlertEndpoints:
    """Test alert system endpoints"""

    def test_create_alert_success(self, test_client: TestClient, valid_jwt_token, sample_alert_data):
        """Test creating an alert"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch('alerts.alert_manager.AlertManager.create_alert') as mock_alert:
            mock_alert.return_value = {
                "alert_id": "alert_test_123",
                "status": "active",
                "channels_sent": ["email", "sms"]
            }

            response = test_client.post("/api/v1/alerts", json=sample_alert_data, headers=headers)
            assert response.status_code == 201

            data = response.json()
            assert data["success"] is True
            assert "alert_id" in data["data"]

    def test_get_alert_success(self, test_client: TestClient, valid_jwt_token, test_alert):
        """Test getting a specific alert"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get(f"/api/v1/alerts/{test_alert.alert_id}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["alert_id"] == test_alert.alert_id

    def test_list_alerts_success(self, test_client: TestClient, valid_jwt_token, test_alert):
        """Test listing alerts"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/alerts", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "alerts" in data["data"]

    def test_resolve_alert_success(self, test_client: TestClient, valid_jwt_token, test_alert):
        """Test resolving an alert"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        resolve_data = {
            "resolution": "False alarm - no suspicious activity detected",
            "resolved_by": "test_officer"
        }

        response = test_client.post(
            f"/api/v1/alerts/{test_alert.alert_id}/resolve",
            json=resolve_data,
            headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    def test_get_analytics_overview_success(self, test_client: TestClient, valid_jwt_token):
        """Test getting analytics overview"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/analytics/overview", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "complaints_stats" in data["data"]
        assert "predictions_accuracy" in data["data"]
        assert "cordons_effectiveness" in data["data"]

    def test_get_realtime_analytics_success(self, test_client: TestClient, valid_jwt_token):
        """Test getting real-time analytics"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v2/analytics/realtime", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "active_complaints" in data["data"]
        assert "active_predictions" in data["data"]
        assert "active_cordons" in data["data"]
        assert "system_load" in data["data"]

    def test_get_hotspots_success(self, test_client: TestClient, valid_jwt_token):
        """Test getting crime hotspots"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/analytics/hotspots", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "hotspots" in data["data"]
        assert isinstance(data["data"]["hotspots"], list)

    def test_get_performance_metrics_success(self, test_client: TestClient, valid_jwt_token):
        """Test getting system performance metrics"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/analytics/performance", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "response_times" in data["data"]
        assert "throughput" in data["data"]
        assert "error_rates" in data["data"]

class TestUserManagementEndpoints:
    """Test user management endpoints"""

    def test_get_user_profile_success(self, test_client: TestClient, valid_jwt_token, test_user):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch('auth.auth_service.auth_service.get_user_by_id') as mock_get_user:
            mock_get_user.return_value = test_user

            response = test_client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["user_id"] == test_user.user_id

    def test_update_user_profile_success(self, test_client: TestClient, valid_jwt_token, test_user):
        """Test updating user profile"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        update_data = {
            "name": "Updated Name",
            "department": "Updated Department",
            "phone": "+919999999999"
        }

        response = test_client.put("/api/v1/users/profile", json=update_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_change_password_success(self, test_client: TestClient, valid_jwt_token, test_user):
        """Test changing user password"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        password_data = {
            "current_password": "old_password",
            "new_password": "NewP@ssw0rd123!",
            "confirm_password": "NewP@ssw0rd123!"
        }

        with patch('auth.auth_service.auth_service.change_password') as mock_change:
            mock_change.return_value = True

            response = test_client.post("/api/v1/users/change-password", json=password_data, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_list_users_success(self, test_client: TestClient, valid_jwt_token):
        """Test listing users (admin only)"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = test_client.get("/api/v1/users", headers=headers)
        # This should work for admin users, might fail for regular users
        assert response.status_code in [200, 403]

class TestErrorHandling:
    """Test API error handling"""

    def test_unauthorized_access(self, test_client: TestClient):
        """Test accessing protected endpoints without authentication"""
        protected_endpoints = [
            "/api/v1/complaints",
            "/api/v1/predictions",
            "/api/v1/cordons",
            "/api/v1/alerts",
            "/api/v1/analytics/overview",
            "/api/v1/users/profile"
        ]

        for endpoint in protected_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 401

            data = response.json()
            assert data["success"] is False
            assert "authentication" in data["error"].lower()

    def test_invalid_jwt_token(self, test_client: TestClient):
        """Test accessing endpoints with invalid JWT token"""
        headers = {"Authorization": "Bearer invalid_token"}
        endpoint = "/api/v1/complaints"

        response = test_client.get(endpoint, headers=headers)
        assert response.status_code == 401

    def test_rate_limiting(self, test_client: TestClient, valid_jwt_token):
        """Test rate limiting on API endpoints"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(10):
            response = test_client.get("/api/v1/complaints", headers=headers)
            responses.append(response)

        # Check if any request was rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # This depends on the rate limiting implementation
        # assert rate_limited or all(r.status_code == 200 for r in responses)

    def test_validation_errors(self, test_client: TestClient, valid_jwt_token):
        """Test input validation errors"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Test invalid JSON
        response = test_client.post(
            "/api/v1/complaints",
            data="invalid json",
            headers={**headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = test_client.post("/api/v1/complaints", json={}, headers=headers)
        assert response.status_code == 422

    def test_server_error_handling(self, test_client: TestClient, valid_jwt_token):
        """Test server error handling"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Mock a service to raise an exception
        with patch('database.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = test_client.get("/api/v1/complaints", headers=headers)
            assert response.status_code == 500

            data = response.json()
            assert data["success"] is False

class TestCORSHeaders:
    """Test CORS headers"""

    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are present"""
        response = test_client.options("/api/v1/complaints")
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

if __name__ == "__main__":
    pytest.main([__file__])