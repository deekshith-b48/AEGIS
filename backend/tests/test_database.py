"""
Database Tests
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from database.database import Base, DatabaseManager, get_db, database_manager
from database.models import (
    User, Complaint, Prediction, Alert, Cordon, AuditLog,
    UserRole, ComplaintStatus, AlertSeverity, CordonStatus
)

class TestDatabaseManager:
    """Test DatabaseManager class"""

    def test_init(self):
        """Test DatabaseManager initialization"""
        manager = DatabaseManager()
        assert manager.engine is not None
        assert manager.SessionLocal is not None
        assert isinstance(manager.connection_stats, dict)

    def test_get_session(self):
        """Test getting database session"""
        manager = DatabaseManager()
        session = manager.get_session()
        assert session is not None
        session.close()

    @pytest.mark.asyncio
    async def test_check_connection_success(self, test_db_engine):
        """Test successful database connection check"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        health = await manager.check_connection()
        assert health["status"] == "healthy"
        assert "database_url" in health
        assert "connection_pool" in health
        assert "database_stats" in health

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """Test database connection check failure"""
        manager = DatabaseManager()
        # Use invalid database URL
        manager.engine = create_engine("postgresql://invalid:invalid@localhost:9999/invalid")

        health = await manager.check_connection()
        assert health["status"] == "unhealthy"
        assert "error" in health

    @pytest.mark.asyncio
    async def test_execute_query_success(self, test_db_engine):
        """Test successful query execution"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        result = await manager.execute_query("SELECT 1 as test_value")
        assert len(result) == 1
        assert result[0].test_value == 1

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, test_db_engine):
        """Test query execution with parameters"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        result = await manager.execute_query(
            "SELECT :value as test_value",
            {"value": "test_param"}
        )
        assert len(result) == 1
        assert result[0].test_value == "test_param"

    @pytest.mark.asyncio
    async def test_execute_transaction_success(self, test_db_engine):
        """Test successful transaction execution"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        queries = [
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)",
            "INSERT INTO test_table (id) VALUES (1)",
            "SELECT * FROM test_table WHERE id = 1"
        ]

        result = await manager.execute_transaction(queries)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_transaction_failure(self, test_db_engine):
        """Test transaction execution with failure"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        queries = [
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)",
            "INSERT INTO test_table (id) VALUES (1)",
            "INVALID SQL QUERY"  # This should cause rollback
        ]

        result = await manager.execute_transaction(queries)
        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_postgis(self, test_db_engine):
        """Test PostGIS initialization"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        # Mock PostgreSQL-specific functionality for SQLite
        with pytest.raises(Exception):
            # This will fail in SQLite test environment
            result = await manager.initialize_postgis()

    def test_get_connection_stats(self, test_db_engine):
        """Test getting connection statistics"""
        manager = DatabaseManager()
        manager.engine = test_db_engine

        stats = manager.get_connection_stats()
        assert "total_queries" in stats
        assert "failed_queries" in stats
        assert "average_query_time" in stats
        assert "pool_status" in stats

class TestUserModel:
    """Test User model"""

    def test_create_user(self, test_db_session):
        """Test creating a user"""
        user = User(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            password="hashed_password",
            role=UserRole.CITIZEN,
            department="test_dept",
            phone="+919876543210",
            is_active=True
        )

        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.user_id == "test_user_123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.CITIZEN
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_constraints(self, test_db_session):
        """Test user unique constraints"""
        # Create first user
        user1 = User(
            user_id="user_123",
            email="test@example.com",
            name="User 1",
            password="hashed_password",
            role=UserRole.CITIZEN
        )
        test_db_session.add(user1)
        test_db_session.commit()

        # Try to create user with same email
        user2 = User(
            user_id="user_456",
            email="test@example.com",  # Duplicate email
            name="User 2",
            password="hashed_password",
            role=UserRole.CITIZEN
        )
        test_db_session.add(user2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_user_role_enum(self, test_db_session):
        """Test user role enum values"""
        for role in UserRole:
            user = User(
                user_id=f"user_{role.value}",
                email=f"{role.value}@example.com",
                name=f"User {role.value}",
                password="hashed_password",
                role=role
            )
            test_db_session.add(user)

        test_db_session.commit()

        # Verify all roles were saved correctly
        users = test_db_session.query(User).all()
        assert len(users) == len(UserRole)
        assert all(user.role in UserRole for user in users)

    def test_user_soft_delete(self, test_db_session):
        """Test user soft delete via is_active flag"""
        user = User(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            password="hashed_password",
            role=UserRole.CITIZEN,
            is_active=True
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Soft delete
        user.is_active = False
        test_db_session.commit()

        # Check user is soft deleted
        active_user = test_db_session.query(User).filter(
            User.user_id == "test_user_123",
            User.is_active == True
        ).first()
        assert active_user is None

        # But user still exists in database
        all_user = test_db_session.query(User).filter(
            User.user_id == "test_user_123"
        ).first()
        assert all_user is not None
        assert all_user.is_active is False

class TestComplaintModel:
    """Test Complaint model"""

    def test_create_complaint(self, test_db_session, test_user):
        """Test creating a complaint"""
        complaint = Complaint(
            complaint_id="comp_123",
            user_id=test_user.user_id,
            complaint_type="online_scam",
            amount=50000.0,
            victim_location="Mumbai, Maharashtra",
            victim_contact={"name": "Victim", "phone": "+919876543210"},
            scammer_details={"phone": "+918765432109"},
            transaction_details={"bank": "Test Bank", "amount": 50000.0},
            scam_date=datetime.utcnow(),
            status=ComplaintStatus.PENDING,
            priority="medium"
        )

        test_db_session.add(complaint)
        test_db_session.commit()
        test_db_session.refresh(complaint)

        assert complaint.complaint_id == "comp_123"
        assert complaint.user_id == test_user.user_id
        assert complaint.complaint_type == "online_scam"
        assert complaint.amount == 50000.0
        assert complaint.status == ComplaintStatus.PENDING
        assert complaint.created_at is not None

    def test_complaint_json_fields(self, test_db_session, test_user):
        """Test JSON fields in complaint model"""
        victim_contact = {
            "name": "Test Victim",
            "email": "victim@example.com",
            "phone": "+919876543210"
        }
        scammer_details = {
            "name": "Unknown Scammer",
            "phone": "+918765432109",
            "upi_id": "scammer@paytm"
        }

        complaint = Complaint(
            complaint_id="comp_123",
            user_id=test_user.user_id,
            complaint_type="online_scam",
            amount=25000.0,
            victim_location="Delhi, NCR",
            victim_contact=victim_contact,
            scammer_details=scammer_details,
            status=ComplaintStatus.PENDING
        )

        test_db_session.add(complaint)
        test_db_session.commit()
        test_db_session.refresh(complaint)

        assert complaint.victim_contact == victim_contact
        assert complaint.scammer_details == scammer_details
        assert isinstance(complaint.victim_contact, dict)
        assert isinstance(complaint.scammer_details, dict)

    def test_complaint_status_enum(self, test_db_session, test_user):
        """Test complaint status enum values"""
        for status in ComplaintStatus:
            complaint = Complaint(
                complaint_id=f"comp_{status.value}",
                user_id=test_user.user_id,
                complaint_type="test_scam",
                amount=1000.0,
                victim_location="Test Location",
                status=status
            )
            test_db_session.add(complaint)

        test_db_session.commit()

        complaints = test_db_session.query(Complaint).all()
        assert len(complaints) == len(ComplaintStatus)
        assert all(complaint.status in ComplaintStatus for complaint in complaints)

    def test_complaint_user_relationship(self, test_db_session, test_user):
        """Test complaint-user relationship"""
        complaint = Complaint(
            complaint_id="comp_123",
            user_id=test_user.user_id,
            complaint_type="online_scam",
            amount=10000.0,
            victim_location="Test Location",
            status=ComplaintStatus.PENDING
        )

        test_db_session.add(complaint)
        test_db_session.commit()
        test_db_session.refresh(complaint)

        # Test relationship
        assert complaint.user.user_id == test_user.user_id
        assert complaint.user.email == test_user.email

        # Test reverse relationship
        user_complaints = test_db_session.query(User).filter(
            User.user_id == test_user.user_id
        ).first().complaints
        assert len(user_complaints) == 1
        assert user_complaints[0].complaint_id == complaint.complaint_id

class TestPredictionModel:
    """Test Prediction model"""

    def test_create_prediction(self, test_db_session, test_complaint):
        """Test creating a prediction"""
        prediction = Prediction(
            prediction_id="pred_123",
            complaint_id=test_complaint.complaint_id,
            location_id=123,
            location_name="Mumbai Central ATM",
            latitude=19.0760,
            longitude=72.8777,
            confidence_score=0.92,
            risk_level="high",
            time_window_start=datetime.utcnow(),
            time_window_end=datetime.utcnow() + timedelta(hours=2),
            ai_insights={"model": "cst_transformer", "confidence": 0.95}
        )

        test_db_session.add(prediction)
        test_db_session.commit()
        test_db_session.refresh(prediction)

        assert prediction.prediction_id == "pred_123"
        assert prediction.complaint_id == test_complaint.complaint_id
        assert prediction.location_name == "Mumbai Central ATM"
        assert prediction.confidence_score == 0.92
        assert prediction.risk_level == "high"

    def test_prediction_complaint_relationship(self, test_db_session, test_complaint):
        """Test prediction-complaint relationship"""
        prediction = Prediction(
            prediction_id="pred_123",
            complaint_id=test_complaint.complaint_id,
            location_id=123,
            location_name="Test Location",
            latitude=19.0760,
            longitude=72.8777,
            confidence_score=0.85,
            risk_level="medium"
        )

        test_db_session.add(prediction)
        test_db_session.commit()
        test_db_session.refresh(prediction)

        # Test relationship
        assert prediction.complaint.complaint_id == test_complaint.complaint_id
        assert prediction.complaint.amount == test_complaint.amount

    def test_prediction_confidence_validation(self, test_db_session, test_complaint):
        """Test confidence score validation"""
        # Valid confidence scores
        valid_scores = [0.0, 0.5, 0.85, 1.0]
        for score in valid_scores:
            prediction = Prediction(
                prediction_id=f"pred_{int(score * 100)}",
                complaint_id=test_complaint.complaint_id,
                location_id=123,
                location_name="Test Location",
                latitude=19.0760,
                longitude=72.8777,
                confidence_score=score,
                risk_level="medium"
            )
            test_db_session.add(prediction)

        test_db_session.commit()
        predictions = test_db_session.query(Prediction).all()
        assert len(predictions) == len(valid_scores)
        assert all(0.0 <= pred.confidence_score <= 1.0 for pred in predictions)

class TestAlertModel:
    """Test Alert model"""

    def test_create_alert(self, test_db_session, test_prediction):
        """Test creating an alert"""
        alert = Alert(
            alert_id="alert_123",
            prediction_id=test_prediction.prediction_id,
            title="High-Risk Prediction Confirmed",
            message="AI model predicts high probability of cash-out",
            severity=AlertSeverity.CRITICAL,
            status="active",
            channels=["email", "sms", "whatsapp"],
            recipients=["officer1@police.gov.in", "bank1@security.bank.in"],
            metadata={"priority": "immediate", "location": "Mumbai Central"}
        )

        test_db_session.add(alert)
        test_db_session.commit()
        test_db_session.refresh(alert)

        assert alert.alert_id == "alert_123"
        assert alert.prediction_id == test_prediction.prediction_id
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == "active"
        assert "email" in alert.channels
        assert len(alert.recipients) == 2

    def test_alert_prediction_relationship(self, test_db_session, test_prediction):
        """Test alert-prediction relationship"""
        alert = Alert(
            alert_id="alert_123",
            prediction_id=test_prediction.prediction_id,
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.HIGH,
            status="active"
        )

        test_db_session.add(alert)
        test_db_session.commit()
        test_db_session.refresh(alert)

        # Test relationship
        assert alert.prediction.prediction_id == test_prediction.prediction_id
        assert alert.prediction.location_name == test_prediction.location_name

    def test_alert_severity_enum(self, test_db_session, test_prediction):
        """Test alert severity enum values"""
        for severity in AlertSeverity:
            alert = Alert(
                alert_id=f"alert_{severity.value}",
                prediction_id=test_prediction.prediction_id,
                title=f"Alert {severity.value}",
                message=f"Message with {severity.value} severity",
                severity=severity,
                status="active"
            )
            test_db_session.add(alert)

        test_db_session.commit()

        alerts = test_db_session.query(Alert).all()
        assert len(alerts) == len(AlertSeverity)
        assert all(alert.severity in AlertSeverity for alert in alerts)

class TestCordonModel:
    """Test Digital Cordon model"""

    def test_create_cordon(self, test_db_session, test_complaint):
        """Test creating a digital cordon"""
        cordon = Cordon(
            cordon_id="cordon_123",
            complaint_id=test_complaint.complaint_id,
            target_type="account",
            target_value="123456789012",
            cordon_type="account_block",
            priority="high",
            status=CordonStatus.ACTIVE,
            duration_hours=24,
            evidence={"complaint_id": test_complaint.complaint_id, "risk_score": 0.95},
            geographic_area={"latitude": 19.0760, "longitude": 72.8777, "radius_km": 5.0}
        )

        test_db_session.add(cordon)
        test_db_session.commit()
        test_db_session.refresh(cordon)

        assert cordon.cordon_id == "cordon_123"
        assert cordon.complaint_id == test_complaint.complaint_id
        assert cordon.target_type == "account"
        assert cordon.status == CordonStatus.ACTIVE
        assert cordon.duration_hours == 24

    def test_cordon_complaint_relationship(self, test_db_session, test_complaint):
        """Test cordon-complaint relationship"""
        cordon = Cordon(
            cordon_id="cordon_123",
            complaint_id=test_complaint.complaint_id,
            target_type="upi_id",
            target_value="scammer@paytm",
            cordon_type="payment_block",
            priority="medium",
            status=CordonStatus.ACTIVE
        )

        test_db_session.add(cordon)
        test_db_session.commit()
        test_db_session.refresh(cordon)

        # Test relationship
        assert cordon.complaint.complaint_id == test_complaint.complaint_id
        assert cordon.complaint.complaint_type == test_complaint.complaint_type

    def test_cordon_status_enum(self, test_db_session, test_complaint):
        """Test cordon status enum values"""
        for status in CordonStatus:
            cordon = Cordon(
                cordon_id=f"cordon_{status.value}",
                complaint_id=test_complaint.complaint_id,
                target_type="test_target",
                target_value="test_value",
                cordon_type="test_type",
                priority="medium",
                status=status
            )
            test_db_session.add(cordon)

        test_db_session.commit()

        cordons = test_db_session.query(Cordon).all()
        assert len(cordons) == len(CordonStatus)
        assert all(cordon.status in CordonStatus for cordon in cordons)

class TestAuditLogModel:
    """Test AuditLog model"""

    def test_create_audit_log(self, test_db_session, test_user):
        """Test creating an audit log entry"""
        audit_log = AuditLog(
            action="complaint_created",
            resource_type="complaint",
            resource_id="comp_123",
            user_id=test_user.user_id,
            user_role=test_user.role.value,
            timestamp=datetime.utcnow(),
            status="success",
            metadata={"ip_address": "192.168.1.1", "user_agent": "Mozilla/5.0"}
        )

        test_db_session.add(audit_log)
        test_db_session.commit()
        test_db_session.refresh(audit_log)

        assert audit_log.action == "complaint_created"
        assert audit_log.resource_type == "complaint"
        assert audit_log.resource_id == "comp_123"
        assert audit_log.user_id == test_user.user_id
        assert audit_log.status == "success"

    def test_audit_log_user_relationship(self, test_db_session, test_user):
        """Test audit log-user relationship"""
        audit_log = AuditLog(
            action="login",
            resource_type="user",
            resource_id=test_user.user_id,
            user_id=test_user.user_id,
            user_role=test_user.role.value,
            timestamp=datetime.utcnow(),
            status="success"
        )

        test_db_session.add(audit_log)
        test_db_session.commit()
        test_db_session.refresh(audit_log)

        # Test relationship
        assert audit_log.user.user_id == test_user.user_id
        assert audit_log.user.email == test_user.email

    def test_audit_log_querying(self, test_db_session, test_user):
        """Test querying audit logs"""
        # Create multiple audit entries
        actions = ["login", "complaint_created", "prediction_generated", "alert_created"]
        for i, action in enumerate(actions):
            audit_log = AuditLog(
                action=action,
                resource_type="test",
                resource_id=f"resource_{i}",
                user_id=test_user.user_id,
                user_role=test_user.role.value,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                status="success"
            )
            test_db_session.add(audit_log)

        test_db_session.commit()

        # Query recent logs
        recent_logs = test_db_session.query(AuditLog).filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=2)
        ).all()
        assert len(recent_logs) >= 2

        # Query by user
        user_logs = test_db_session.query(AuditLog).filter(
            AuditLog.user_id == test_user.user_id
        ).all()
        assert len(user_logs) == len(actions)

class TestDatabaseConstraints:
    """Test database constraints and relationships"""

    def test_foreign_key_constraints(self, test_db_session):
        """Test foreign key constraints"""
        # Try to create complaint with non-existent user
        complaint = Complaint(
            complaint_id="comp_invalid",
            user_id="nonexistent_user",
            complaint_type="test_scam",
            amount=1000.0,
            victim_location="Test Location",
            status=ComplaintStatus.PENDING
        )

        test_db_session.add(complaint)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_cascade_delete_behavior(self, test_db_session, test_user):
        """Test cascade delete behavior"""
        # Create related records
        complaint = Complaint(
            complaint_id="comp_123",
            user_id=test_user.user_id,
            complaint_type="test_scam",
            amount=1000.0,
            victim_location="Test Location",
            status=ComplaintStatus.PENDING
        )
        test_db_session.add(complaint)
        test_db_session.commit()

        prediction = Prediction(
            prediction_id="pred_123",
            complaint_id=complaint.complaint_id,
            location_id=123,
            location_name="Test Location",
            latitude=19.0760,
            longitude=72.8777,
            confidence_score=0.85,
            risk_level="medium"
        )
        test_db_session.add(prediction)
        test_db_session.commit()

        alert = Alert(
            alert_id="alert_123",
            prediction_id=prediction.prediction_id,
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.HIGH,
            status="active"
        )
        test_db_session.add(alert)
        test_db_session.commit()

        # Delete user (if cascade is configured)
        test_db_session.delete(test_user)
        test_db_session.commit()

        # Check related records are handled appropriately
        # This depends on the cascade configuration in the models

class TestDatabaseIndexes:
    """Test database indexes and performance"""

    def test_complaint_indexes(self, test_db_session, test_user):
        """Test complaint-related indexes"""
        # Create multiple complaints for testing
        for i in range(10):
            complaint = Complaint(
                complaint_id=f"comp_{i:03d}",
                user_id=test_user.user_id,
                complaint_type="online_scam",
                amount=1000.0 * (i + 1),
                victim_location=f"Location {i}",
                status=ComplaintStatus.PENDING
            )
            test_db_session.add(complaint)

        test_db_session.commit()

        # Test indexed queries
        complaints_by_user = test_db_session.query(Complaint).filter(
            Complaint.user_id == test_user.user_id
        ).all()
        assert len(complaints_by_user) == 10

        complaints_by_status = test_db_session.query(Complaint).filter(
            Complaint.status == ComplaintStatus.PENDING
        ).all()
        assert len(complaints_by_status) == 10

    def test_prediction_indexes(self, test_db_session, test_complaint):
        """Test prediction-related indexes"""
        # Create multiple predictions
        for i in range(5):
            prediction = Prediction(
                prediction_id=f"pred_{i}",
                complaint_id=test_complaint.complaint_id,
                location_id=100 + i,
                location_name=f"Location {i}",
                latitude=19.0760 + i * 0.01,
                longitude=72.8777 + i * 0.01,
                confidence_score=0.8 + i * 0.04,
                risk_level="medium" if i < 3 else "high"
            )
            test_db_session.add(prediction)

        test_db_session.commit()

        # Test indexed queries
        predictions_by_complaint = test_db_session.query(Prediction).filter(
            Prediction.complaint_id == test_complaint.complaint_id
        ).all()
        assert len(predictions_by_complaint) == 5

        high_risk_predictions = test_db_session.query(Prediction).filter(
            Prediction.risk_level == "high"
        ).all()
        assert len(high_risk_predictions) == 2

class TestDatabaseTransactions:
    """Test database transaction handling"""

    def test_transaction_rollback(self, test_db_session, test_user):
        """Test transaction rollback on error"""
        # Start a transaction
        original_count = test_db_session.query(Complaint).filter(
            Complaint.user_id == test_user.user_id
        ).count()

        # Create a valid complaint
        complaint1 = Complaint(
            complaint_id="comp_valid",
            user_id=test_user.user_id,
            complaint_type="test_scam",
            amount=1000.0,
            victim_location="Test Location",
            status=ComplaintStatus.PENDING
        )
        test_db_session.add(complaint1)

        # Try to create an invalid complaint (missing required field)
        complaint2 = Complaint(
            complaint_id="comp_invalid",
            user_id=test_user.user_id,
            # Missing complaint_type
            amount=1000.0,
            victim_location="Test Location"
        )
        test_db_session.add(complaint2)

        # Commit should fail and rollback
        try:
            test_db_session.commit()
        except:
            test_db_session.rollback()

        # Check that neither complaint was saved
        final_count = test_db_session.query(Complaint).filter(
            Complaint.user_id == test_user.user_id
        ).count()
        assert final_count == original_count

    def test_nested_transactions(self, test_db_session, test_user):
        """Test nested transaction behavior"""
        # Create a savepoint
        savepoint = test_db_session.begin_nested()

        # Create a complaint within savepoint
        complaint = Complaint(
            complaint_id="comp_nested",
            user_id=test_user.user_id,
            complaint_type="test_scam",
            amount=1000.0,
            victim_location="Test Location",
            status=ComplaintStatus.PENDING
        )
        test_db_session.add(complaint)
        savepoint.commit()

        # Complaint should be saved
        saved_complaint = test_db_session.query(Complaint).filter(
            Complaint.complaint_id == "comp_nested"
        ).first()
        assert saved_complaint is not None

        # Rollback main transaction
        test_db_session.rollback()

        # Complaint should still be there (savepoint was committed)
        saved_complaint = test_db_session.query(Complaint).filter(
            Complaint.complaint_id == "comp_nested"
        ).first()
        assert saved_complaint is not None

if __name__ == "__main__":
    pytest.main([__file__])