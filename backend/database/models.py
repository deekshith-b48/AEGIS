"""
Database Models for Project AEGIS
SQLAlchemy models for all database tables
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, JSON, ARRAY, DECIMAL, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.sql import func

from .database import Base

# Enum definitions
class ComplaintType(str, Enum):
    ONLINE_SCAM = "online_scam"
    BANK_FRAUD = "bank_fraud"
    UPI_FRAUD = "upi_fraud"
    INVESTMENT_SCAM = "investment_scam"
    PHISHING = "phishing"
    JOB_SCAM = "job_scam"
    MATRIMONIAL_SCAM = "matrimonial_scam"
    OTHER = "other"

class ComplaintStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserRole(str, Enum):
    CITIZEN = "citizen"
    LAW_ENFORCEMENT = "law_enforcement"
    ANALYST = "analyst"
    ADMINISTRATOR = "administrator"
    SYSTEM = "system"

class CordonStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    FAILED = "failed"

class AlertSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

# Core Models

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    department = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_login = Column(DateTime(timezone=True))
    permissions = Column(JSONB)
    phone = Column(String(20))
    badge_number = Column(String(50))
    designation = Column(String(100))

    # Relationships
    complaints = relationship("Complaint", back_populates="user")
    digital_cordons = relationship("DigitalCordon", back_populates="created_by_user")
    alerts = relationship("Alert", back_populates="user")

class Complaint(Base):
    """Main complaints table"""
    __tablename__ = "complaints"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_type = Column(Enum(ComplaintType), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    victim_location = Column(String(255), nullable=False)
    victim_contact_encrypted = Column(Text)
    scammer_details = Column(JSONB)
    transaction_details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.PENDING, index=True)
    priority = Column(String(20), default="medium", index=True)
    metadata = Column(JSONB)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))

    # Additional fields
    scam_date = Column(DateTime(timezone=True))
    platform_details = Column(JSONB)
    victim_statement = Column(Text)
    evidence_attachments = Column(JSONB)
    location_coordinates = Column(JSONB)  # lat, lon

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="complaints")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    predictions = relationship("Prediction", back_populates="complaint")
    alerts = relationship("Alert", back_populates="complaint")

class Location(Base):
    """Locations table with geospatial capabilities"""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    address = Column(Text)
    latitude = Column(DECIMAL(10, 8), nullable=False, index=True)
    longitude = Column(DECIMAL(11, 8), nullable=False, index=True)
    postal_code = Column(String(20), index=True)
    city = Column(String(100), index=True)
    state = Column(String(100), index=True)
    country = Column(String(100), default="India")
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Geospatial column
    geometry = Column(Geometry('POINT', srid=4326))

    # Additional location data
    location_type = Column(String(50))  # bank, atm, post_office, etc.
    risk_score = Column(DECIMAL(5, 4))
    last_activity = Column(DateTime(timezone=True))

    # Relationships
    predictions = relationship("Prediction", back_populates="location")
    hotspots = relationship("Hotspot", back_populates="location")

class Prediction(Base):
    """AI predictions for complaint outcomes"""
    __tablename__ = "predictions"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(50), ForeignKey("complaint.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"))
    location_name = Column(String(255), nullable=False)
    location_lat = Column(DECIMAL(10, 8))
    location_lon = Column(DECIMAL(11, 8))
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    time_window_start = Column(DateTime(timezone=True))
    time_window_end = Column(DateTime(timezone=True))
    prediction_models = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)

    # Enhanced AI fields
    ai_insights = Column(JSONB)
    behavioral_factors = Column(JSONB)
    temporal_patterns = Column(JSONB)
    spatial_factors = Column(JSONB)
    confidence_factors = Column(JSONB)

    # Relationships
    complaint = relationship("Complaint", back_populates="predictions")
    location = relationship("Location", back_populates="predictions")

class DigitalCordon(Base):
    """Digital payment cordons"""
    __tablename__ = "digital_cordons"

    cordon_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String(50), nullable=False)
    target_value = Column(String(255), nullable=False)
    action = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False, index=True)
    status = Column(Enum(CordonStatus), default=CordonStatus.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    created_by = Column(String(100))
    evidence = Column(JSONB)
    npcii_reference = Column(String(100))
    affected_accounts = Column(ARRAY(String))

    # Enhanced cordon fields
    geographic_area = Column(JSONB)  # geofence coordinates
    transaction_limits = Column(JSONB)
    notification_sent = Column(Boolean, default=False)
    effectiveness_metrics = Column(JSONB)
    compliance_data = Column(JSONB)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    created_by_user = relationship("User", back_populates="digital_cordons")
    executions = relationship("CordonExecution", back_populates="cordon")

class CordonExecution(Base):
    """Digital cordon execution logs"""
    __tablename__ = "cordon_executions"

    id = Column(Integer, primary_key=True, index=True)
    cordon_id = Column(String(50), ForeignKey("digital_cordons.cordon_id"), nullable=False)
    execution_id = Column(String(100), nullable=False)
    npcii_response = Column(JSONB)
    success = Column(Boolean, nullable=False)
    execution_time = Column(DateTime(timezone=True), default=func.now())
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    affected_accounts = Column(ARRAY(String))
    affected_transactions = Column(ARRAY(String))

    # Enhanced execution data
    bank_responses = Column(JSONB)
    payment_processor_responses = Column(JSONB)
    compliance_checks = Column(JSONB)

    # Relationships
    cordon = relationship("DigitalCordon", back_populates="executions")

class Alert(Base):
    """Alert system table"""
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    channels = Column(ARRAY(String))
    recipients = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    status = Column(String(50), default="active", index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    metadata = Column(JSONB)

    # Enhanced alert fields
    escalation_rules = Column(JSONB)
    delivery_status = Column(JSONB)
    response_metrics = Column(JSONB)
    auto_resolve_after = Column(Integer)  # hours

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    complaint_id = Column(String(50), ForeignKey("complaint.id"))

    # Relationships
    user = relationship("User", back_populates="alerts")
    complaint = relationship("Complaint", back_populates="alerts")

# AI and Learning Models

class BehavioralProfile(Base):
    """Behavioral digital twin profiles"""
    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_anon_id = Column(String(100), nullable=False, index=True)
    behavior_patterns = Column(JSONB)
    risk_score = Column(DECIMAL(5, 4), index=True)
    predicted_behaviors = Column(JSONB)
    last_updated = Column(DateTime(timezone=True), default=func.now(), index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Enhanced behavioral data
    personality_traits = Column(JSONB)
    decision_patterns = Column(JSONB)
    temporal_preferences = Column(JSONB)
    spatial_preferences = Column(JSONB)
    communication_patterns = Column(JSONB)

    # Model metadata
    model_version = Column(String(50))
    confidence_interval = Column(JSONB)
    training_data_count = Column(Integer)

class FederatedCausalNode(Base):
    """Federated causal graph nodes"""
    __tablename__ = "federated_causal_graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(String(50), nullable=False, index=True)
    node_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Enhanced node data
    node_attributes = Column(JSONB)
    temporal_features = Column(JSONB)
    source_institution = Column(String(100))
    confidence_score = Column(DECIMAL(5, 4))

    # Relationships
    outgoing_edges = relationship("FederatedCausalEdge", foreign_keys="source_node_id", back_populates="source_node")
    incoming_edges = relationship("FederatedCausalEdge", foreign_keys="target_node_id", back_populates="target_node")

class FederatedCausalEdge(Base):
    """Federated causal graph edges"""
    __tablename__ = "federated_causal_graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("federated_causal_graph_nodes.id"), index=True)
    target_node_id = Column(Integer, ForeignKey("federated_causal_graph_nodes.id"), index=True)
    relationship_type = Column(String(50), nullable=False, index=True)
    weight = Column(DECIMAL(10, 4))
    confidence = Column(DECIMAL(5, 4))
    temporal_constraint = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Enhanced edge data
    causal_strength = Column(DECIMAL(5, 4))
    temporal_lag = Column(JSONB)
    mediation_factors = Column(JSONB)
    counterfactual_data = Column(JSONB)

    # Relationships
    source_node = relationship("FederatedCausalNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("FederatedCausalNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

class LearningData(Base):
    """Continuous learning system data"""
    __tablename__ = "learning_data"

    data_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    features = Column(JSONB, nullable=False)
    labels = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    source = Column(String(100), nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)
    quality_score = Column(DECIMAL(5, 4), index=True)
    metadata = Column(JSONB)

    # Enhanced learning data
    feature_importance = Column(JSONB)
    preprocessing_applied = Column(JSONB)
    validation_status = Column(String(50))
    model_feedback = Column(JSONB)

class ModelDeployment(Base):
    """AI model deployment tracking"""
    __tablename__ = "model_deployments"

    model_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_type = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False, index=True)
    performance_metrics = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())
    model_path = Column(String(255))
    metadata = Column(JSONB)

    # Enhanced deployment data
    hyperparameters = Column(JSONB)
    training_config = Column(JSONB)
    deployment_environment = Column(String(50))
    rollback_version = Column(Integer)
    feature_schema = Column(JSONB)

# Analytics and Monitoring

class AnalyticsMetric(Base):
    """Analytics metrics storage"""
    __tablename__ = "analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(DECIMAL(15, 6), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    dimensions = Column(JSONB)

    # Enhanced metric data
    aggregation_type = Column(String(50))
    time_bucket = Column(String(50))
    source_system = Column(String(100))
    quality_score = Column(DECIMAL(5, 4))

class DashboardData(Base):
    """Dashboard widget data"""
    __tablename__ = "dashboard_data"

    id = Column(Integer, primary_key=True, index=True)
    widget_type = Column(String(50), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    is_current = Column(Boolean, default=True, index=True)

    # Enhanced dashboard data
    widget_config = Column(JSONB)
    refresh_interval = Column(Integer)  # seconds
    access_permissions = Column(JSONB)

class SystemHealth(Base):
    """System health monitoring"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    component_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    metadata = Column(JSONB)

    # Enhanced health data
    health_score = Column(DECIMAL(5, 4))
    dependencies = Column(JSONB)
    resource_usage = Column(JSONB)
    last_checkin = Column(DateTime(timezone=True))

# Geospatial Features

class Hotspot(Base):
    """Geospatial hotspots for cybercrime"""
    __tablename__ = "gis_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    hotspot_type = Column(String(50), nullable=False)
    severity_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    confidence = Column(DECIMAL(5, 4))
    radius_meters = Column(Integer)
    detected_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    is_active = Column(Boolean, default=True, index=True)
    metadata = Column(JSONB)

    # Geospatial column
    geometry = Column(Geometry('POINT', srid=4326))

    # Enhanced hotspot data
    prediction_sources = Column(JSONB)
    contributing_factors = Column(JSONB)
    temporal_patterns = Column(JSONB)
    spatial_patterns = Column(JSONB)

    # Relationships
    location = relationship("Location", back_populates="hotspots")

class Geofence(Base):
    """Geofenced areas for monitoring"""
    __tablename__ = "geofences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    fence_type = Column(String(50), nullable=False)  # 'circle', 'polygon', 'rectangle'
    coordinates = Column(JSONB, nullable=False)
    radius_meters = Column(DECIMAL(10, 2))  # for circle fences
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, default=True, index=True)
    metadata = Column(JSONB)

    # Geospatial column
    geometry = Column(Geometry('POLYGON', srid=4326))

    # Enhanced geofence data
    alert_rules = Column(JSONB)
    monitoring_config = Column(JSONB)
    compliance_requirements = Column(JSONB)

# Audit and Logging

class AuditLog(Base):
    """Comprehensive audit logging"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), index=True)
    user_id = Column(String(100), nullable=False, index=True)
    user_role = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    ip_address = Column(INET)
    user_agent = Column(Text)
    status = Column(String(20), nullable=False, index=True)  # 'success', 'failed', 'denied'
    error_message = Column(Text)
    metadata = Column(JSONB)

    # Enhanced audit data
    session_id = Column(String(100))
    correlation_id = Column(String(100))
    request_id = Column(String(100))
    processing_time_ms = Column(Integer)
    data_before = Column(JSONB)
    data_after = Column(JSONB)

class DataAccessLog(Base):
    """Data access logging for compliance"""
    __tablename__ = "data_access_log"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    operation = Column(String(20), nullable=False, index=True)  # 'read', 'write', 'delete'
    record_id = Column(String(255), index=True)
    user_id = Column(String(100), nullable=False, index=True)
    access_time = Column(DateTime(timezone=True), default=func.now(), index=True)
    was_authorized = Column(Boolean, nullable=False)
    details = Column(JSONB)

    # Enhanced access data
    access_purpose = Column(String(100))
    legal_basis = Column(String(100))
    data_retention_period = Column(Integer)
    anonymization_applied = Column(JSONB)

# Integration and External Systems

class ApiIntegration(Base):
    """External API integration configurations"""
    __tablename__ = "api_integrations"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), unique=True, nullable=False)
    api_base_url = Column(String(500), nullable=False)
    api_version = Column(String(20))
    auth_method = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_check = Column(DateTime(timezone=True), default=func.now())
    status = Column(String(50), default="unknown", index=True)
    error_message = Column(Text)
    configuration = Column(JSONB)

    # Enhanced integration data
    rate_limits = Column(JSONB)
    retry_config = Column(JSONB)
    monitoring_config = Column(JSONB)
    compliance_requirements = Column(JSONB)

class ApiCallLog(Base):
    """API call logging for external integrations"""
    __tablename__ = "api_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("api_integrations.id"), index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_data = Column(JSONB)
    response_data = Column(JSONB)
    status_code = Column(Integer, index=True)
    response_time_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    error_message = Column(Text)

    # Enhanced call data
    retry_count = Column(Integer)
    timeout_occurred = Column(Boolean)
    cache_hit = Column(Boolean)
    correlation_id = Column(String(100))

# Performance Monitoring

class PerformanceMetric(Base):
    """System performance metrics"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(DECIMAL(15, 6), nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    dimensions = Column(JSONB)

    # Enhanced performance data
    percentile_50 = Column(DECIMAL(15, 6))
    percentile_95 = Column(DECIMAL(15, 6))
    percentile_99 = Column(DECIMAL(15, 6))
    sample_count = Column(Integer)

class QueryPerformance(Base):
    """Database query performance tracking"""
    __tablename__ = "query_performance"

    id = Column(Integer, primary_key=True, index=True)
    query_type = Column(String(50), nullable=False, index=True)
    execution_time_ms = Column(DECIMAL(10, 4), index=True)
    rows_affected = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    user_id = Column(String(100))
    query_details = Column(JSONB)

    # Enhanced query data
    query_hash = Column(String(64))
    execution_plan = Column(JSONB)
    indexes_used = Column(JSONB)
    optimization_suggestions = Column(JSONB)

# Index definitions
Index("idx_complaints_created_status", Complaint.c.created_at, Complaint.status)
Index("idx_predictions_confidence_risk", Prediction.confidence_score, Prediction.risk_level)
Index("idx_alerts_severity_created", Alert.severity, Alert.created_at)
Index("idx_learning_data_type_timestamp", LearningData.data_type, LearningData.timestamp)
Index("idx_health_component_timestamp", SystemHealth.component_name, SystemHealth.timestamp)

# Full-text search indexes (PostgreSQL specific)
# These would be created in migrations
# CREATE INDEX idx_complaints_fulltext ON complaints USING GIN(to_tsvector('english', complaint_type || ' ' || COALESCE(victim_location, '')))
# CREATE INDEX idx_locations_fulltext ON locations USING GIN(to_tsvector('english', name || ' ' || COALESCE(address, '') || ' ' || COALESCE(city, '') || ' ' || COALESCE(state, '')))