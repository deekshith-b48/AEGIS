from sqlalchemy import create_engine, Column, String, Numeric, DateTime, Integer, Float, Boolean, Text, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geography
import os
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aegis.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scam_type = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    victim_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class HighRiskATM(Base):
    __tablename__ = "high_risk_atms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    tags = Column(ARRAY(String))
    city = Column(String(100), nullable=False)

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), nullable=False)
    hotspot_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    location_name = Column(String(200), nullable=False)
    confidence = Column(Float, nullable=False)
    time_window_mins = Column(Integer, nullable=False)
    predicted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")  # active, interdicted, false_alert

class Cordon(Base):
    __tablename__ = "cordons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    center_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    radius_meters = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")  # active, expired

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hotspot_id = Column(UUID(as_uuid=True), nullable=False)
    lea_action = Column(String(20), nullable=False)  # confirmed, false, interdicted
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(DateTime, nullable=False)
    total_predictions = Column(Integer, nullable=False, default=0)
    confirmed_predictions = Column(Integer, nullable=False, default=0)
    false_predictions = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)