"""
Test configuration and fixtures for Project AEGIS
"""

import pytest
import asyncio
import os
import tempfile
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import json

# Import modules to test
from database.database import Base, get_db
from database.models import User, Complaint, Prediction, Alert
from auth.auth_service import AuthenticationService, auth_service
from main import app

# Test configuration
TEST_DATABASE_URL = "sqlite:///./test_aegis.db"
TEST_JWT_SECRET = "test-secret-key-for-testing-only"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator:
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_client(test_db_session) -> Generator:
    """Create a test client for FastAPI app"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_auth_service():
    """Create a mock authentication service"""
    mock_service = Mock(spec=AuthenticationService)
    mock_service.secret_key = TEST_JWT_SECRET
    mock_service.algorithm = "HS256"
    mock_service.access_token_expire_minutes = 30
    mock_service.refresh_token_expire_days = 7

    # Mock token methods
    mock_service.create_access_token = Mock(return_value="test_access_token")
    mock_service.create_refresh_token = Mock(return_value="test_refresh_token")
    mock_service.verify_token = Mock(return_value={
        "sub": "test_user_id",
        "email": "test@example.com",
        "role": "citizen",
        "permissions": ["read_complaints", "create_complaints"],
        "exp": datetime.utcnow().timestamp() + 1800
    })

    # Mock user methods
    mock_service.authenticate_user = AsyncMock(return_value=Mock(
        user_id="test_user_id",
        email="test@example.com",
        name="Test User",
        role="citizen",
        is_active=True
    ))

    mock_service.login_user = AsyncMock(return_value={
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "user_id": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
            "role": "citizen"
        }
    })

    return mock_service

@pytest.fixture(scope="function")
def test_user(test_db_session):
    """Create a test user"""
    user = User(
        user_id="test_user_123",
        email="test@example.com",
        name="Test User",
        password="hashed_password",
        role="citizen",
        department="test_dept",
        phone="+919876543210",
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_complaint(test_db_session, test_user):
    """Create a test complaint"""
    complaint = Complaint(
        complaint_id="comp_test_123",
        user_id=test_user.user_id,
        complaint_type="online_scam",
        amount=50000.0,
        victim_location="Mumbai, Maharashtra",
        victim_contact={"name": "Test Victim", "phone": "+919876543210"},
        scammer_details={"phone": "+918765432109", "upi_id": "scammer@paytm"},
        transaction_details={"bank_name": "Test Bank", "amount": 50000.0},
        scam_date=datetime.utcnow(),
        status="pending",
        priority="medium",
        created_at=datetime.utcnow()
    )
    test_db_session.add(complaint)
    test_db_session.commit()
    test_db_session.refresh(complaint)
    return complaint

@pytest.fixture(scope="function")
def test_prediction(test_db_session, test_complaint):
    """Create a test prediction"""
    prediction = Prediction(
        prediction_id="pred_test_123",
        complaint_id=test_complaint.complaint_id,
        location_id=123,
        location_name="Mumbai Central ATM",
        latitude=19.0760,
        longitude=72.8777,
        confidence_score=0.92,
        risk_level="high",
        time_window_start=datetime.utcnow(),
        time_window_end=datetime.utcnow(),
        ai_insights={"model": "test_model", "features": ["feature1", "feature2"]},
        created_at=datetime.utcnow()
    )
    test_db_session.add(prediction)
    test_db_session.commit()
    test_db_session.refresh(prediction)
    return prediction

@pytest.fixture(scope="function")
def test_alert(test_db_session, test_prediction):
    """Create a test alert"""
    alert = Alert(
        alert_id="alert_test_123",
        prediction_id=test_prediction.prediction_id,
        title="Test Alert",
        message="Test alert message",
        severity="high",
        status="active",
        channels=["email", "sms"],
        recipients=["test@example.com"],
        metadata={"source": "test"},
        created_at=datetime.utcnow()
    )
    test_db_session.add(alert)
    test_db_session.commit()
    test_db_session.refresh(alert)
    return alert

@pytest.fixture(scope="function")
def valid_jwt_token(mock_auth_service):
    """Create a valid JWT token for testing"""
    return mock_auth_service.create_access_token({
        "sub": "test_user_id",
        "email": "test@example.com",
        "role": "citizen",
        "permissions": ["read_complaints", "create_complaints"]
    })

@pytest.fixture(scope="function")
def expired_jwt_token(mock_auth_service):
    """Create an expired JWT token for testing"""
    return "expired_token_for_testing"

@pytest.fixture(scope="function")
def sample_complaint_data():
    """Sample complaint data for testing"""
    return {
        "complaint_type": "online_scam",
        "amount": 50000.0,
        "victim_location": "Mumbai, Maharashtra",
        "victim_contact": {
            "name": "Test Victim",
            "email": "victim@example.com",
            "phone": "+919876543210"
        },
        "scammer_details": {
            "name": "Unknown Scammer",
            "phone": "+918765432109",
            "upi_id": "scammer@paytm"
        },
        "transaction_details": {
            "bank_name": "Test Bank",
            "account_number": "1234567890",
            "ifsc_code": "TEST0001234",
            "transaction_amount": 50000.0,
            "transaction_date": datetime.utcnow().isoformat(),
            "payment_method": "UPI"
        },
        "scam_date": datetime.utcnow().isoformat(),
        "victim_statement": "I was scammed through a fake investment scheme.",
        "priority": "medium"
    }

@pytest.fixture(scope="function")
def sample_prediction_data():
    """Sample prediction data for testing"""
    return {
        "location_id": 123,
        "location_name": "Mumbai Central ATM",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "confidence_score": 0.92,
        "risk_level": "high",
        "time_window_start": datetime.utcnow().isoformat(),
        "time_window_end": datetime.utcnow().isoformat(),
        "ai_insights": {
            "model": "cst_transformer",
            "features": ["historical_patterns", "geospatial_proximity"],
            "risk_factors": ["high_amount", "recent_complaints"]
        },
        "probability_score": 0.95,
        "distance_km": 2.5
    }

@pytest.fixture(scope="function")
def sample_cordon_data():
    """Sample digital cordon data for testing"""
    return {
        "target_type": "account",
        "target_value": "123456789012",
        "cordon_type": "account_block",
        "priority": "high",
        "duration_hours": 24,
        "evidence": {
            "complaint_id": "comp_test_123",
            "risk_score": 0.95,
            "fraud_indicators": ["suspicious_transactions", "multiple_complaints"]
        },
        "geographic_area": {
            "latitude": 19.0760,
            "longitude": 72.8777,
            "radius_km": 5.0
        },
        "transaction_limits": {
            "daily_limit": 10000.0,
            "per_transaction_limit": 5000.0
        }
    }

@pytest.fixture(scope="function")
def sample_alert_data():
    """Sample alert data for testing"""
    return {
        "title": "High-Risk Prediction Confirmed",
        "message": "AI model predicts high probability of cash-out at Mumbai Central within 30 minutes",
        "severity": "critical",
        "target_groups": ["cybercrime_team", "banking_authorities"],
        "recipients": [
            {"email": "officer1@police.gov.in", "phone": "+919876543210"},
            {"email": "bank1@security.bank.in", "phone": "+919876543211"}
        ],
        "channels": ["email", "sms", "whatsapp", "push"],
        "auto_resolve_after": 24,
        "metadata": {
            "prediction_id": "pred_test_123",
            "location": "Mumbai Central ATM",
            "urgency": "immediate"
        }
    }

@pytest.fixture(scope="function")
def mock_kafka_producer():
    """Create a mock Kafka producer"""
    producer = Mock()
    producer.send = Mock(return_value=Mock())
    producer.flush = Mock()
    producer.close = Mock()
    return producer

@pytest.fixture(scope="function")
def mock_redis_client():
    """Create a mock Redis client"""
    redis_client = Mock()
    redis_client.set = Mock(return_value=True)
    redis_client.get = Mock(return_value='{"test": "data"}')
    redis_client.delete = Mock(return_value=1)
    redis_client.exists = Mock(return_value=True)
    redis_client.expire = Mock(return_value=True)
    return redis_client

@pytest.fixture(scope="function")
def mock_websocket_manager():
    """Create a mock WebSocket manager"""
    manager = Mock()
    manager.connect = Mock(return_value="test_connection_id")
    manager.disconnect = Mock()
    manager.broadcast = Mock()
    manager.send_personal_message = Mock()
    manager.get_connection_count = Mock(return_value=5)
    return manager

@pytest.fixture(scope="function")
def temp_upload_dir():
    """Create a temporary directory for file uploads"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="function")
def mock_file_upload(temp_upload_dir):
    """Create a mock uploaded file"""
    file_path = os.path.join(temp_upload_dir, "test_evidence.pdf")
    with open(file_path, "wb") as f:
        f.write(b"Test PDF content for evidence")
    return file_path

# Environment variables for testing
@pytest.fixture(scope="function", autouse=True)
def set_test_env_vars(monkeypatch):
    """Set environment variables for testing"""
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("DB_NAME", "test_aegis_db")
    monkeypatch.setenv("DB_ECHO", "false")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("NPCI_API_KEY", "test_npci_key")
    monkeypatch.setenv("NPCI_API_SECRET", "test_npci_secret")

# Mock external services
@pytest.fixture(scope="function")
def mock_ncpi_api():
    """Create a mock NPCI API client"""
    npci_client = Mock()
    npci_client.create_cordon = AsyncMock(return_value={
        "success": True,
        "cordon_id": "cordon_test_123",
        "status": "active"
    })
    npci_client.check_cordon_status = AsyncMock(return_value={
        "success": True,
        "status": "active",
        "blocks_initiated": 5
    })
    npci_client.release_cordon = AsyncMock(return_value={
        "success": True,
        "status": "released"
    })
    return npci_client

@pytest.fixture(scope="function")
def mock_ai_models():
    """Create mock AI models"""
    models = {
        "cst_transformer": Mock(),
        "federated_causal_graph": Mock(),
        "behavioral_digital_twin": Mock(),
        "risk_scoring_engine": Mock()
    }

    # Mock predictions
    for model_name, model in models.items():
        model.predict = Mock(return_value={
            "predictions": [
                {
                    "location_id": 123,
                    "confidence_score": 0.92,
                    "risk_level": "high"
                }
            ],
            "model_confidence": 0.88,
            "processing_time_ms": 1250.5
        })

    return models

# Async test fixtures
@pytest.fixture(scope="function")
async def async_test_client():
    """Create an async test client for WebSocket testing"""
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def mock_websocket():
    """Create a mock WebSocket connection"""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock(return_value='{"type": "ping"}')
    websocket.close = AsyncMock()
    websocket.client = Mock()
    websocket.client.host = "127.0.0.1"
    websocket.client.port = 12345
    return websocket