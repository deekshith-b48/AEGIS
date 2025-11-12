"""
Advanced Data Warehouse for Cybercrime Intelligence
Manages data aggregation, analytics, and reporting with OLAP capabilities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine, MetaData, Table, Column, String, Float, Integer, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

class AggregationLevel(Enum):
    """
    Data aggregation levels
    """
    RAW = "raw"                    # Individual records
    HOURLY = "hourly"             # Hourly aggregates
    DAILY = "daily"               # Daily aggregates
    WEEKLY = "weekly"             # Weekly aggregates
    MONTHLY = "monthly"           # Monthly aggregates
    QUARTERLY = "quarterly"       # Quarterly aggregates

class MetricType(Enum):
    """
    Types of metrics in data warehouse
    """
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD_DEV = "std_dev"
    PERCENTILE = "percentile"

@dataclass
class MetricDefinition:
    """
    Metric definition for data warehouse
    """
    name: str
    metric_type: MetricType
    source_table: str
    source_column: str
    aggregation_level: AggregationLevel
    description: str
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class ReportDefinition:
    """
    Report definition for automated reporting
    """
    name: str
    description: str
    metrics: List[str]
    dimensions: List[str]
    filters: Dict[str, Any]
    schedule: str
    recipients: List[str]
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class DataWarehouse:
    """
    Advanced data warehouse for cybercrime intelligence
    """

    def __init__(self):
        self.engine = None
        self.metadata = MetaData()
        self.metric_definitions = {}
        self.report_definitions = {}
        self.materialized_views = {}

        # Warehouse tables
        self.fact_tables = {}
        self.dimension_tables = {}

    async def initialize(self) -> bool:
        """
        Initialize data warehouse
        """
        try:
            logger.info("[Data Warehouse] Initializing data warehouse...")

            # Initialize database connection
            self.engine = create_engine("postgresql://user:password@localhost/aegis_warehouse")

            # Create warehouse schema
            await self._create_warehouse_schema()

            # Define metrics
            await self._define_metrics()

            # Define reports
            await self._define_reports()

            # Create materialized views
            await self._create_materialized_views()

            logger.info("[Data Warehouse] Data warehouse initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Data Warehouse] Error initializing data warehouse: {str(e)}")
            return False

    async def _create_warehouse_schema(self) -> None:
        """
        Create data warehouse schema
        """
        try:
            with SessionLocal() as db:
                # Create warehouse schema
                db.execute(text("CREATE SCHEMA IF NOT EXISTS dw"))

                # Create fact tables
                await self._create_fact_tables(db)

                # Create dimension tables
                await self._create_dimension_tables(db)

                # Create aggregation tables
                await self._create_aggregation_tables(db)

                db.commit()

        except Exception as e:
            logger.error(f"[Data Warehouse] Error creating warehouse schema: {str(e)}")

    async def _create_fact_tables(self, db: Session) -> None:
        """
        Create fact tables for data warehouse
        """
        try:
            # Complaints fact table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.fact_complaints (
                    fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    complaint_id VARCHAR(255),
                    date_key INTEGER,
                    time_key INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    victim_demographics_key INTEGER,
                    amount DECIMAL(15,2),
                    digital_footprint_key INTEGER,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Transactions fact table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.fact_transactions (
                    fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    transaction_id VARCHAR(255),
                    date_key INTEGER,
                    time_key INTEGER,
                    location_key INTEGER,
                    bank_key INTEGER,
                    transaction_type_key INTEGER,
                    amount DECIMAL(15,2),
                    risk_score DECIMAL(5,4),
                    is_suspicious BOOLEAN,
                    fraud_signals JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # I4C crimes fact table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.fact_i4c_crimes (
                    fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    crime_id VARCHAR(255),
                    date_key INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    criminal_network_key INTEGER,
                    severity_score INTEGER,
                    conviction_rate DECIMAL(5,4),
                    outcome VARCHAR(50),
                    victim_profile_key INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Alerts fact table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.fact_alerts (
                    fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    alert_id VARCHAR(255),
                    date_key INTEGER,
                    time_key INTEGER,
                    location_key INTEGER,
                    alert_type_key INTEGER,
                    severity VARCHAR(20),
                    source_system VARCHAR(50),
                    resolution_status VARCHAR(50),
                    response_time_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            logger.info("[Data Warehouse] Fact tables created")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error creating fact tables: {str(e)}")

    async def _create_dimension_tables(self, db: Session) -> None:
        """
        Create dimension tables
        """
        try:
            # Date dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_date (
                    date_key INTEGER PRIMARY KEY,
                    date_value DATE,
                    day_of_week INTEGER,
                    day_of_month INTEGER,
                    day_of_year INTEGER,
                    week_of_year INTEGER,
                    month INTEGER,
                    quarter INTEGER,
                    year INTEGER,
                    is_weekend BOOLEAN,
                    is_holiday BOOLEAN,
                    season VARCHAR(20)
                )
            """))

            # Time dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_time (
                    time_key INTEGER PRIMARY KEY,
                    hour INTEGER,
                    minute INTEGER,
                    time_of_day VARCHAR(20),
                    is_business_hours BOOLEAN,
                    is_peak_hours BOOLEAN
                )
            """))

            # Location dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_location (
                    location_key SERIAL PRIMARY KEY,
                    latitude DECIMAL(10,8),
                    longitude DECIMAL(11,8),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    country VARCHAR(100),
                    postal_code VARCHAR(20),
                    urban_density VARCHAR(20),
                    region_type VARCHAR(50),
                    transport_proximity VARCHAR(20)
                )
            """))

            # Scam type dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_scam_type (
                    scam_type_key SERIAL PRIMARY KEY,
                    scam_type VARCHAR(100),
                    category VARCHAR(50),
                    severity_level INTEGER,
                    description TEXT,
                    common_methods JSON
                )
            """))

            # Bank dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_bank (
                    bank_key SERIAL PRIMARY KEY,
                    bank_code VARCHAR(20),
                    bank_name VARCHAR(200),
                    bank_type VARCHAR(50),
                    region VARCHAR(100),
                    is_pso BOOLEAN
                )
            """))

            # Victim demographics dimension
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.dim_victim_demographics (
                    demographics_key SERIAL PRIMARY KEY,
                    age_group VARCHAR(20),
                    gender VARCHAR(20),
                    occupation VARCHAR(100),
                    education_level VARCHAR(50),
                    digital_literacy VARCHAR(20),
                    urban_rural VARCHAR(20),
                    income_bracket VARCHAR(20)
                )
            """))

            logger.info("[Data Warehouse] Dimension tables created")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error creating dimension tables: {str(e)}")

    async def _create_aggregation_tables(self, db: Session) -> None:
        """
        Create aggregation tables for different time periods
        """
        try:
            # Hourly aggregations
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.aggregations_hourly (
                    agg_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    date_key INTEGER,
                    hour_key INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    complaint_count INTEGER DEFAULT 0,
                    total_amount DECIMAL(15,2) DEFAULT 0,
                    avg_amount DECIMAL(15,2) DEFAULT 0,
                    suspicious_transaction_count INTEGER DEFAULT 0,
                    avg_risk_score DECIMAL(5,4) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Daily aggregations
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.aggregations_daily (
                    agg_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    date_key INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    complaint_count INTEGER DEFAULT 0,
                    total_amount DECIMAL(15,2) DEFAULT 0,
                    avg_amount DECIMAL(15,2) DEFAULT 0,
                    suspicious_transaction_count INTEGER DEFAULT 0,
                    avg_risk_score DECIMAL(5,4) DEFAULT 0,
                    new_cases INTEGER DEFAULT 0,
                    resolved_cases INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Weekly aggregations
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.aggregations_weekly (
                    agg_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    year INTEGER,
                    week_number INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    complaint_count INTEGER DEFAULT 0,
                    total_amount DECIMAL(15,2) DEFAULT 0,
                    avg_amount DECIMAL(15,2) DEFAULT 0,
                    trend_percentage DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Monthly aggregations
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS dw.aggregations_monthly (
                    agg_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    year INTEGER,
                    month INTEGER,
                    location_key INTEGER,
                    scam_type_key INTEGER,
                    complaint_count INTEGER DEFAULT 0,
                    total_amount DECIMAL(15,2) DEFAULT 0,
                    avg_amount DECIMAL(15,2) DEFAULT 0,
                    month_over_month_change DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            logger.info("[Data Warehouse] Aggregation tables created")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error creating aggregation tables: {str(e)}")

    async def _define_metrics(self) -> None:
        """
        Define metrics for data warehouse
        """
        try:
            # Complaint metrics
            self.metric_definitions['total_complaints'] = MetricDefinition(
                name="total_complaints",
                metric_type=MetricType.COUNT,
                source_table="dw.fact_complaints",
                source_column="fact_id",
                aggregation_level=AggregationLevel.DAILY,
                description="Total number of complaints"
            )

            self.metric_definitions['total_amount_lost'] = MetricDefinition(
                name="total_amount_lost",
                metric_type=MetricType.SUM,
                source_table="dw.fact_complaints",
                source_column="amount",
                aggregation_level=AggregationLevel.DAILY,
                description="Total amount lost across all complaints"
            )

            self.metric_definitions['avg_complaint_amount'] = MetricDefinition(
                name="avg_complaint_amount",
                metric_type=MetricType.AVERAGE,
                source_table="dw.fact_complaints",
                source_column="amount",
                aggregation_level=AggregationLevel.DAILY,
                description="Average amount per complaint"
            )

            # Transaction metrics
            self.metric_definitions['suspicious_transactions'] = MetricDefinition(
                name="suspicious_transactions",
                metric_type=MetricType.COUNT,
                source_table="dw.fact_transactions",
                source_column="fact_id",
                aggregation_level=AggregationLevel.HOURLY,
                description="Number of suspicious transactions"
            )

            self.metric_definitions['avg_risk_score'] = MetricDefinition(
                name="avg_risk_score",
                metric_type=MetricType.AVERAGE,
                source_table="dw.fact_transactions",
                source_column="risk_score",
                aggregation_level=AggregationLevel.HOURLY,
                description="Average risk score across transactions"
            )

            # Response metrics
            self.metric_definitions['avg_response_time'] = MetricDefinition(
                name="avg_response_time",
                metric_type=MetricType.AVERAGE,
                source_table="dw.fact_alerts",
                source_column="response_time_minutes",
                aggregation_level=AggregationLevel.DAILY,
                description="Average response time for alerts"
            )

            # Geographic metrics
            self.metric_definitions['hotspot_intensity'] = MetricDefinition(
                name="hotspot_intensity",
                metric_type=MetricType.SUM,
                source_table="dw.aggregations_daily",
                source_column="complaint_count",
                aggregation_level=AggregationLevel.DAILY,
                description="Intensity of cybercrime hotspots"
            )

            logger.info(f"[Data Warehouse] Defined {len(self.metric_definitions)} metrics")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error defining metrics: {str(e)}")

    async def _define_reports(self) -> None:
        """
        Define automated reports
        """
        try:
            # Daily summary report
            self.report_definitions['daily_summary'] = ReportDefinition(
                name="daily_summary",
                description="Daily cybercrime summary report",
                metrics=["total_complaints", "total_amount_lost", "avg_complaint_amount", "suspicious_transactions"],
                dimensions=["date", "scam_type", "location"],
                filters={"date_range": "last_24_hours"},
                schedule="0 8 * * *",  # Daily at 8 AM
                recipients=["analytics@cybercrime.gov.in", "director@ncrp.gov.in"]
            )

            # Weekly trends report
            self.report_definitions['weekly_trends'] = ReportDefinition(
                name="weekly_trends",
                description="Weekly cybercrime trends analysis",
                metrics=["total_complaints", "avg_risk_score", "hotspot_intensity"],
                dimensions=["week", "scam_type", "state"],
                filters={"date_range": "last_7_days"},
                schedule="0 9 * * 1",  # Monday at 9 AM
                recipients=["analytics@cybercrime.gov.in", "intelligence@i4c.gov.in"]
            )

            # Hotspot analysis report
            self.report_definitions['hotspot_analysis'] = ReportDefinition(
                name="hotspot_analysis",
                description="Geographic hotspot analysis report",
                metrics=["hotspot_intensity", "total_amount_lost"],
                dimensions=["location", "date"],
                filters={"date_range": "last_7_days", "min_complaints": 5},
                schedule="0 10 * * 1,4",  # Monday and Thursday at 10 AM
                recipients=["field_officers@cybercrime.gov.in", "analytics@cybercrime.gov.in"]
            )

            # Bank performance report
            self.report_definitions['bank_performance'] = ReportDefinition(
                name="bank_performance",
                description="Bank transaction monitoring performance",
                metrics=["suspicious_transactions", "avg_risk_score"],
                dimensions=["bank", "date", "transaction_type"],
                filters={"date_range": "last_24_hours"},
                schedule="0 */6 * * *",  # Every 6 hours
                recipients=["banking@fcfrms.gov.in", "compliance@rbi.gov.in"]
            )

            logger.info(f"[Data Warehouse] Defined {len(self.report_definitions)} reports")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error defining reports: {str(e)}")

    async def _create_materialized_views(self) -> None:
        """
        Create materialized views for performance
        """
        try:
            with SessionLocal() as db:
                # Latest complaints view
                db.execute(text("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS dw.mv_latest_complaints AS
                    SELECT
                        fc.complaint_id,
                        fc.amount,
                        dd.date_value,
                        dl.city,
                        dst.scam_type,
                        fc.status
                    FROM dw.fact_complaints fc
                    JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                    JOIN dw.dim_location dl ON fc.location_key = dl.location_key
                    JOIN dw.dim_scam_type dst ON fc.scam_type_key = dst.scam_type_key
                    WHERE fc.date_key >= (SELECT MAX(date_key) - 7 FROM dw.dim_date)
                    ORDER BY dd.date_value DESC
                """))

                # Risk hotspot view
                db.execute(text("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS dw.mv_risk_hotspots AS
                    SELECT
                        dl.city,
                        dl.state,
                        dd.date_value,
                        COUNT(fc.complaint_id) as complaint_count,
                        SUM(fc.amount) as total_amount,
                        AVG(ft.risk_score) as avg_risk_score
                    FROM dw.fact_complaints fc
                    JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                    JOIN dw.dim_location dl ON fc.location_key = dl.location_key
                    LEFT JOIN dw.fact_transactions ft ON fc.location_key = ft.location_key
                        AND fc.date_key = ft.date_key
                    WHERE fc.date_key >= (SELECT MAX(date_key) - 30 FROM dw.dim_date)
                    GROUP BY dl.city, dl.state, dd.date_value
                    HAVING COUNT(fc.complaint_id) >= 3
                    ORDER BY complaint_count DESC, total_amount DESC
                """))

                # Scam type trends view
                db.execute(text("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS dw.mv_scam_trends AS
                    SELECT
                        dst.scam_type,
                        dst.category,
                        dd.year,
                        dd.month,
                        COUNT(fc.complaint_id) as complaint_count,
                        SUM(fc.amount) as total_amount,
                        AVG(fc.amount) as avg_amount,
                        LAG(COUNT(fc.complaint_id), 1) OVER (
                            PARTITION BY dst.scam_type
                            ORDER BY dd.year, dd.month
                        ) as prev_month_count
                    FROM dw.fact_complaints fc
                    JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                    JOIN dw.dim_scam_type dst ON fc.scam_type_key = dst.scam_type_key
                    WHERE dd.date_key >= (SELECT MAX(date_key) - 365 FROM dw.dim_date)
                    GROUP BY dst.scam_type, dst.category, dd.year, dd.month
                    ORDER BY dst.scam_type, dd.year, dd.month
                """))

                # Bank risk metrics view
                db.execute(text("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS dw.mv_bank_risk_metrics AS
                    SELECT
                        db.bank_code,
                        db.bank_name,
                        dd.date_value,
                        COUNT(ft.transaction_id) as total_transactions,
                        COUNT(CASE WHEN ft.is_suspicious THEN 1 END) as suspicious_transactions,
                        AVG(ft.risk_score) as avg_risk_score,
                        MAX(ft.risk_score) as max_risk_score,
                        SUM(ft.amount) as total_amount
                    FROM dw.fact_transactions ft
                    JOIN dw.dim_date dd ON ft.date_key = dd.date_key
                    JOIN dw.dim_bank db ON ft.bank_key = db.bank_key
                    WHERE ft.date_key >= (SELECT MAX(date_key) - 30 FROM dw.dim_date)
                    GROUP BY db.bank_code, db.bank_name, dd.date_value
                    ORDER BY dd.date_value DESC, suspicious_transactions DESC
                """))

                db.commit()

            logger.info("[Data Warehouse] Materialized views created")

        except Exception as e:
            logger.error(f"[Data Warehouse] Error creating materialized views: {str(e)}")

    async def populate_dimensions(self) -> int:
        """
        Populate dimension tables with data
        """
        try:
            with SessionLocal() as db:
                populated_count = 0

                # Populate date dimension (next 365 days)
                await self._populate_date_dimension(db)

                # Populate time dimension
                await self._populate_time_dimension(db)

                # Populate location dimension from existing data
                await self._populate_location_dimension(db)

                # Populate scam type dimension
                await self._populate_scam_type_dimension(db)

                # Populate bank dimension
                await self._populate_bank_dimension(db)

                db.commit()
                populated_count = 365 + 24 + 100 + 20 + 10  # Estimated counts

                logger.info(f"[Data Warehouse] Populated {populated_count} dimension records")
                return populated_count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating dimensions: {str(e)}")
            return 0

    async def _populate_date_dimension(self, db: Session) -> None:
        """
        Populate date dimension
        """
        try:
            # Clear existing dates
            db.execute(text("DELETE FROM dw.dim_date"))

            # Generate dates for next 365 days
            base_date = datetime.utcnow().date()
            for i in range(365):
                current_date = base_date + timedelta(days=i)

                date_key = int(current_date.strftime("%Y%m%d"))
                day_of_week = current_date.weekday() + 1  # Monday=1
                day_of_month = current_date.day
                day_of_year = (current_date - datetime(current_date.year, 1, 1).date()).days + 1
                week_of_year = current_date.isocalendar()[1]
                month = current_date.month
                quarter = (month - 1) // 3 + 1
                year = current_date.year
                is_weekend = day_of_week in [6, 7]  # Saturday, Sunday

                # Determine season
                if month in [12, 1, 2]:
                    season = "winter"
                elif month in [3, 4, 5]:
                    season = "spring"
                elif month in [6, 7, 8]:
                    season = "summer"
                else:
                    season = "monsoon"

                db.execute(text("""
                    INSERT INTO dw.dim_date (
                        date_key, date_value, day_of_week, day_of_month,
                        day_of_year, week_of_year, month, quarter, year,
                        is_weekend, is_holiday, season
                    ) VALUES (
                        :date_key, :date_value, :day_of_week, :day_of_month,
                        :day_of_year, :week_of_year, :month, :quarter, :year,
                        :is_weekend, false, :season
                    )
                """), {
                    'date_key': date_key,
                    'date_value': current_date,
                    'day_of_week': day_of_week,
                    'day_of_month': day_of_month,
                    'day_of_year': day_of_year,
                    'week_of_year': week_of_year,
                    'month': month,
                    'quarter': quarter,
                    'year': year,
                    'is_weekend': is_weekend,
                    'season': season
                })

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating date dimension: {str(e)}")

    async def _populate_time_dimension(self, db: Session) -> None:
        """
        Populate time dimension
        """
        try:
            # Clear existing times
            db.execute(text("DELETE FROM dw.dim_time"))

            # Generate time keys for each hour
            for hour in range(24):
                time_key = hour * 100  # Simple time key
                minute = 0

                # Determine time of day
                if 6 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 17:
                    time_of_day = "afternoon"
                elif 17 <= hour < 21:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"

                is_business_hours = 9 <= hour <= 17
                is_peak_hours = hour in [8, 9, 13, 14, 18, 19, 20]

                db.execute(text("""
                    INSERT INTO dw.dim_time (
                        time_key, hour, minute, time_of_day,
                        is_business_hours, is_peak_hours
                    ) VALUES (
                        :time_key, :hour, :minute, :time_of_day,
                        :is_business_hours, :is_peak_hours
                    )
                """), {
                    'time_key': time_key,
                    'hour': hour,
                    'minute': minute,
                    'time_of_day': time_of_day,
                    'is_business_hours': is_business_hours,
                    'is_peak_hours': is_peak_hours
                })

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating time dimension: {str(e)}")

    async def _populate_location_dimension(self, db: Session) -> None:
        """
        Populate location dimension from existing data
        """
        try:
            # Get unique locations from source tables
            result = db.execute(text("""
                SELECT DISTINCT
                    ST_Y(victim_location) as lat,
                    ST_X(victim_location) as lon
                FROM ncrp_complaints
                WHERE victim_location IS NOT NULL
                LIMIT 100
            """))

            for row in result:
                lat, lon = row.lat, row.lon

                # Simple location classification
                if lat is not None and lon is not None:
                    # Determine urban density (simplified)
                    urban_density = "high" if (28.4 <= lat <= 28.7 and 76.9 <= lon <= 77.4) else "medium"

                    # Determine region type
                    region_type = "metro" if urban_density == "high" else "urban"

                    # Determine transport proximity (simplified)
                    transport_proximity = "high" if urban_density == "high" else "medium"

                    db.execute(text("""
                        INSERT INTO dw.dim_location (
                            latitude, longitude, urban_density, region_type,
                            transport_proximity
                        ) VALUES (
                            :lat, :lon, :urban_density, :region_type,
                            :transport_proximity
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        'lat': lat,
                        'lon': lon,
                        'urban_density': urban_density,
                        'region_type': region_type,
                        'transport_proximity': transport_proximity
                    })

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating location dimension: {str(e)}")

    async def _populate_scam_type_dimension(self, db: Session) -> None:
        """
        Populate scam type dimension
        """
        try:
            scam_types = [
                ("UPI_PHISHING", "digital_fraud", 4, "UPI-based phishing scams"),
                ("FAKE_LOAN_APP", "financial_fraud", 5, "Fake loan application scams"),
                ("IMPERSONATION", "social_engineering", 3, "Impersonation scams"),
                ("LOTTERY_SCAM", "financial_fraud", 4, "Lottery prize scams"),
                ("INVESTMENT_FRAUD", "financial_fraud", 5, "Investment fraud schemes"),
                ("JOB_SCAM", "employment_fraud", 3, "Fake job offer scams"),
                ("MATRIMONIAL_SCAM", "social_fraud", 4, "Matrimonial fraud"),
                ("OLX_SCAM", "marketplace_fraud", 3, "Online marketplace scams"),
                ("BANKING_FRAUD", "financial_fraud", 4, "Banking related fraud"),
                ("OTHER", "other", 2, "Other types of scams")
            ]

            for scam_type, category, severity, description in scam_types:
                common_methods = json.dumps({
                    "contact_methods": ["phone", "email", "sms", "whatsapp"],
                    "payment_methods": ["upi", "bank_transfer", "cryptocurrency"],
                    "platforms": ["mobile", "web", "social_media"]
                })

                db.execute(text("""
                    INSERT INTO dw.dim_scam_type (
                        scam_type, category, severity_level, description, common_methods
                    ) VALUES (
                        :scam_type, :category, :severity_level, :description, :common_methods
                    )
                    ON CONFLICT (scam_type) DO UPDATE SET
                        description = EXCLUDED.description,
                        common_methods = EXCLUDED.common_methods
                """), {
                    'scam_type': scam_type,
                    'category': category,
                    'severity_level': severity,
                    'description': description,
                    'common_methods': common_methods
                })

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating scam type dimension: {str(e)}")

    async def _populate_bank_dimension(self, db: Session) -> None:
        """
        Populate bank dimension
        """
        try:
            banks = [
                ("SBIN", "State Bank of India", "public_sector", "national", True),
                ("HDFC", "HDFC Bank", "private_sector", "national", True),
                ("ICIC", "ICICI Bank", "private_sector", "national", True),
                ("AXIS", "Axis Bank", "private_sector", "national", True),
                ("PUNB", "Punjab National Bank", "public_sector", "national", True),
                ("UBIN", "Union Bank of India", "public_sector", "national", True),
                ("BKID", "Bank of India", "public_sector", "national", True),
                ("CORP", "Corporation Bank", "public_sector", "national", True)
            ]

            for bank_code, bank_name, bank_type, region, is_pso in banks:
                db.execute(text("""
                    INSERT INTO dw.dim_bank (
                        bank_code, bank_name, bank_type, region, is_pso
                    ) VALUES (
                        :bank_code, :bank_name, :bank_type, :region, :is_pso
                    )
                    ON CONFLICT (bank_code) DO UPDATE SET
                        bank_name = EXCLUDED.bank_name,
                        bank_type = EXCLUDED.bank_type
                """), {
                    'bank_code': bank_code,
                    'bank_name': bank_name,
                    'bank_type': bank_type,
                    'region': region,
                    'is_pso': is_pso
                })

        except Exception as e:
            logger.error(f"[Data Warehouse] Error populating bank dimension: {str(e)}")

    async def load_fact_data(self, hours_back: int = 24) -> Dict[str, int]:
        """
        Load recent data into fact tables
        """
        try:
            load_counts = {}

            with SessionLocal() as db:
                # Load complaints fact data
                complaint_count = await self._load_complaint_facts(db, hours_back)
                load_counts['complaints'] = complaint_count

                # Load transactions fact data
                transaction_count = await self._load_transaction_facts(db, hours_back)
                load_counts['transactions'] = transaction_count

                # Load I4C crime fact data
                i4c_count = await self._load_i4c_facts(db, hours_back)
                load_counts['i4c_crimes'] = i4c_count

                db.commit()

            logger.info(f"[Data Warehouse] Loaded fact data: {load_counts}")
            return load_counts

        except Exception as e:
            logger.error(f"[Data Warehouse] Error loading fact data: {str(e)}")
            return {}

    async def _load_complaint_facts(self, db: Session, hours_back: int) -> int:
        """
        Load complaint data into fact table
        """
        try:
            # Get recent complaints
            result = db.execute(text("""
                SELECT
                    c.complaint_id,
                    c.scam_type,
                    c.amount,
                    c.created_at,
                    ST_Y(c.victim_location) as lat,
                    ST_X(c.victim_location) as lon,
                    c.status
                FROM ncrp_complaints c
                WHERE c.created_at >= NOW() - INTERVAL ':hours_back hours'
                AND c.complaint_id NOT IN (
                    SELECT complaint_id FROM dw.fact_complaints WHERE complaint_id IS NOT NULL
                )
            """), {'hours_back': hours_back})

            loaded_count = 0

            for row in result:
                # Get dimension keys
                date_key = int(row.created_at.strftime("%Y%m%d"))
                time_key = (row.created_at.hour) * 100

                # Get or create location key
                location_key = await self._get_location_key(db, row.lat, row.lon)

                # Get scam type key
                scam_type_key = await self._get_scam_type_key(db, row.scam_type)

                # Insert into fact table
                db.execute(text("""
                    INSERT INTO dw.fact_complaints (
                        complaint_id, date_key, time_key, location_key,
                        scam_type_key, amount, status
                    ) VALUES (
                        :complaint_id, :date_key, :time_key, :location_key,
                        :scam_type_key, :amount, :status
                    )
                """), {
                    'complaint_id': row.complaint_id,
                    'date_key': date_key,
                    'time_key': time_key,
                    'location_key': location_key,
                    'scam_type_key': scam_type_key,
                    'amount': row.amount,
                    'status': row.status
                })

                loaded_count += 1

            return loaded_count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error loading complaint facts: {str(e)}")
            return 0

    async def _load_transaction_facts(self, db: Session, hours_back: int) -> int:
        """
        Load transaction data into fact table
        """
        try:
            # Get recent suspicious transactions
            result = db.execute(text("""
                SELECT
                    t.transaction_id,
                    t.bank_code,
                    t.transaction_type,
                    t.amount,
                    t.risk_score,
                    t.is_suspicious,
                    t.fraud_signals,
                    t.timestamp,
                    ST_Y(t.location) as lat,
                    ST_X(t.location) as lon
                FROM bank_transactions t
                WHERE t.timestamp >= NOW() - INTERVAL ':hours_back hours'
                AND t.is_suspicious = true
                AND t.transaction_id NOT IN (
                    SELECT transaction_id FROM dw.fact_transactions WHERE transaction_id IS NOT NULL
                )
            """), {'hours_back': hours_back})

            loaded_count = 0

            for row in result:
                # Get dimension keys
                date_key = int(row.timestamp.strftime("%Y%m%d"))
                time_key = (row.timestamp.hour) * 100

                # Get or create location key
                location_key = await self._get_location_key(db, row.lat, row.lon)

                # Get bank key
                bank_key = await self._get_bank_key(db, row.bank_code)

                # Get transaction type key
                transaction_type_key = await self._get_transaction_type_key(db, row.transaction_type)

                # Insert into fact table
                db.execute(text("""
                    INSERT INTO dw.fact_transactions (
                        transaction_id, date_key, time_key, location_key,
                        bank_key, transaction_type_key, amount, risk_score,
                        is_suspicious, fraud_signals
                    ) VALUES (
                        :transaction_id, :date_key, :time_key, :location_key,
                        :bank_key, :transaction_type_key, :amount, :risk_score,
                        :is_suspicious, :fraud_signals
                    )
                """), {
                    'transaction_id': row.transaction_id,
                    'date_key': date_key,
                    'time_key': time_key,
                    'location_key': location_key,
                    'bank_key': bank_key,
                    'transaction_type_key': transaction_type_key,
                    'amount': row.amount,
                    'risk_score': row.risk_score,
                    'is_suspicious': row.is_suspicious,
                    'fraud_signals': row.fraud_signals
                })

                loaded_count += 1

            return loaded_count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error loading transaction facts: {str(e)}")
            return 0

    async def _load_i4c_facts(self, db: Session, hours_back: int) -> int:
        """
        Load I4C crime data into fact table
        """
        try:
            # Get recent I4C crimes
            result = db.execute(text("""
                SELECT
                    i.crime_id,
                    i.scam_type,
                    i.severity_score,
                    i.conviction_rate,
                    i.outcome,
                    i.date_range_start,
                    ST_Y(i.location) as lat,
                    ST_X(i.location) as lon
                FROM i4c_crime_data i
                WHERE i.imported_at >= NOW() - INTERVAL ':hours_back hours'
                AND i.crime_id NOT IN (
                    SELECT crime_id FROM dw.fact_i4c_crimes WHERE crime_id IS NOT NULL
                )
            """), {'hours_back': hours_back})

            loaded_count = 0

            for row in result:
                # Get dimension keys
                date_key = int(row.date_range_start.strftime("%Y%m%d"))

                # Get or create location key
                location_key = await self._get_location_key(db, row.lat, row.lon)

                # Get scam type key
                scam_type_key = await self._get_scam_type_key(db, row.scam_type)

                # Insert into fact table
                db.execute(text("""
                    INSERT INTO dw.fact_i4c_crimes (
                        crime_id, date_key, location_key, scam_type_key,
                        severity_score, conviction_rate, outcome
                    ) VALUES (
                        :crime_id, :date_key, :location_key, :scam_type_key,
                        :severity_score, :conviction_rate, :outcome
                    )
                """), {
                    'crime_id': row.crime_id,
                    'date_key': date_key,
                    'location_key': location_key,
                    'scam_type_key': scam_type_key,
                    'severity_score': row.severity_score,
                    'conviction_rate': row.conviction_rate,
                    'outcome': row.outcome
                })

                loaded_count += 1

            return loaded_count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error loading I4C facts: {str(e)}")
            return 0

    async def _get_location_key(self, db: Session, lat: float, lon: float) -> int:
        """
        Get or create location key
        """
        try:
            # Try to find existing location
            result = db.execute(text("""
                SELECT location_key FROM dw.dim_location
                WHERE latitude = :lat AND longitude = :lon
            """), {'lat': lat, 'lon': lon}).fetchone()

            if result:
                return result.location_key

            # Create new location
            result = db.execute(text("""
                INSERT INTO dw.dim_location (latitude, longitude, urban_density, region_type)
                VALUES (:lat, :lon, 'medium', 'urban')
                RETURNING location_key
            """), {'lat': lat, 'lon': lon}).fetchone()

            return result.location_key

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting location key: {str(e)}")
            return 1  # Default location key

    async def _get_scam_type_key(self, db: Session, scam_type: str) -> int:
        """
        Get or create scam type key
        """
        try:
            # Try to find existing scam type
            result = db.execute(text("""
                SELECT scam_type_key FROM dw.dim_scam_type
                WHERE scam_type = :scam_type
            """), {'scam_type': scam_type}).fetchone()

            if result:
                return result.scam_type_key

            # Create new scam type
            result = db.execute(text("""
                INSERT INTO dw.dim_scam_type (scam_type, category, severity_level, description)
                VALUES (:scam_type, 'other', 3, 'Other scam type')
                RETURNING scam_type_key
            """), {'scam_type': scam_type}).fetchone()

            return result.scam_type_key

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting scam type key: {str(e)}")
            return 1  # Default scam type key

    async def _get_bank_key(self, db: Session, bank_code: str) -> int:
        """
        Get or create bank key
        """
        try:
            # Try to find existing bank
            result = db.execute(text("""
                SELECT bank_key FROM dw.dim_bank
                WHERE bank_code = :bank_code
            """), {'bank_code': bank_code}).fetchone()

            if result:
                return result.bank_key

            # Create new bank
            result = db.execute(text("""
                INSERT INTO dw.dim_bank (bank_code, bank_name, bank_type, region)
                VALUES (:bank_code, :bank_code, 'unknown', 'unknown')
                RETURNING bank_key
            """), {'bank_code': bank_code}).fetchone()

            return result.bank_key

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting bank key: {str(e)}")
            return 1  # Default bank key

    async def _get_transaction_type_key(self, db: Session, transaction_type: str) -> int:
        """
        Get transaction type key (simplified - using scam type table)
        """
        try:
            # For demo, use transaction type as scam type
            result = db.execute(text("""
                SELECT scam_type_key FROM dw.dim_scam_type
                WHERE scam_type = :transaction_type
            """), {'transaction_type': transaction_type}).fetchone()

            if result:
                return result.scam_type_key

            # Create new transaction type entry
            result = db.execute(text("""
                INSERT INTO dw.dim_scam_type (scam_type, category, severity_level, description)
                VALUES (:transaction_type, 'transaction', 2, 'Transaction type')
                RETURNING scam_type_key
            """), {'transaction_type': transaction_type}).fetchone()

            return result.scam_type_key

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting transaction type key: {str(e)}")
            return 1  # Default transaction type key

    async def calculate_aggregations(self, aggregation_level: AggregationLevel = AggregationLevel.DAILY) -> int:
        """
        Calculate data aggregations
        """
        try:
            with SessionLocal() as db:
                if aggregation_level == AggregationLevel.DAILY:
                    count = await self._calculate_daily_aggregations(db)
                elif aggregation_level == AggregationLevel.HOURLY:
                    count = await self._calculate_hourly_aggregations(db)
                elif aggregation_level == AggregationLevel.WEEKLY:
                    count = await self._calculate_weekly_aggregations(db)
                elif aggregation_level == AggregationLevel.MONTHLY:
                    count = await self._calculate_monthly_aggregations(db)

                db.commit()

            logger.info(f"[Data Warehouse] Calculated {count} {aggregation_level.value} aggregations")
            return count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error calculating aggregations: {str(e)}")
            return 0

    async def _calculate_daily_aggregations(self, db: Session) -> int:
        """
        Calculate daily aggregations
        """
        try:
            # Calculate daily complaint aggregations
            result = db.execute(text("""
                INSERT INTO dw.aggregations_daily (
                    date_key, location_key, scam_type_key,
                    complaint_count, total_amount, avg_amount
                )
                SELECT
                    fc.date_key,
                    fc.location_key,
                    fc.scam_type_key,
                    COUNT(fc.complaint_id),
                    SUM(fc.amount),
                    AVG(fc.amount)
                FROM dw.fact_complaints fc
                WHERE fc.date_key >= (SELECT MAX(date_key) - 7 FROM dw.dim_date)
                GROUP BY fc.date_key, fc.location_key, fc.scam_type_key
                ON CONFLICT (date_key, location_key, scam_type_key) DO UPDATE SET
                    complaint_count = EXCLUDED.complaint_count,
                    total_amount = EXCLUDED.total_amount,
                    avg_amount = EXCLUDED.avg_amount
                RETURNING 1
            """))

            count = result.rowcount or 0

            # Calculate daily transaction aggregations
            result = db.execute(text("""
                UPDATE dw.aggregations_daily ad
                SET
                    suspicious_transaction_count = tx.suspicious_count,
                    avg_risk_score = tx.avg_risk
                FROM (
                    SELECT
                        ft.date_key,
                        ft.location_key,
                        COUNT(CASE WHEN ft.is_suspicious THEN 1 END) as suspicious_count,
                        AVG(ft.risk_score) as avg_risk
                    FROM dw.fact_transactions ft
                    WHERE ft.date_key >= (SELECT MAX(date_key) - 7 FROM dw.dim_date)
                    GROUP BY ft.date_key, ft.location_key
                ) tx
                WHERE ad.date_key = tx.date_key AND ad.location_key = tx.location_key
            """))

            return count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error calculating daily aggregations: {str(e)}")
            return 0

    async def _calculate_hourly_aggregations(self, db: Session) -> int:
        """
        Calculate hourly aggregations
        """
        try:
            result = db.execute(text("""
                INSERT INTO dw.aggregations_hourly (
                    date_key, hour_key, location_key, scam_type_key,
                    complaint_count, total_amount, suspicious_transaction_count, avg_risk_score
                )
                SELECT
                    fc.date_key,
                    fc.time_key as hour_key,
                    fc.location_key,
                    fc.scam_type_key,
                    COUNT(fc.complaint_id),
                    COALESCE(SUM(fc.amount), 0),
                    COALESCE(tx.suspicious_count, 0),
                    COALESCE(tx.avg_risk, 0)
                FROM dw.fact_complaints fc
                LEFT JOIN (
                    SELECT
                        ft.date_key,
                        ft.time_key,
                        ft.location_key,
                        COUNT(CASE WHEN ft.is_suspicious THEN 1 END) as suspicious_count,
                        AVG(ft.risk_score) as avg_risk
                    FROM dw.fact_transactions ft
                    WHERE ft.date_key >= (SELECT MAX(date_key) - 1 FROM dw.dim_date)
                    GROUP BY ft.date_key, ft.time_key, ft.location_key
                ) tx ON fc.date_key = tx.date_key AND fc.time_key = tx.time_key AND fc.location_key = tx.location_key
                WHERE fc.date_key >= (SELECT MAX(date_key) - 1 FROM dw.dim_date)
                GROUP BY fc.date_key, fc.time_key, fc.location_key, fc.scam_type_key,
                         tx.suspicious_count, tx.avg_risk
                ON CONFLICT (date_key, hour_key, location_key, scam_type_key) DO UPDATE SET
                    complaint_count = EXCLUDED.complaint_count,
                    total_amount = EXCLUDED.total_amount,
                    suspicious_transaction_count = EXCLUDED.suspicious_transaction_count,
                    avg_risk_score = EXCLUDED.avg_risk_score
                RETURNING 1
            """))

            return result.rowcount or 0

        except Exception as e:
            logger.error(f"[Data Warehouse] Error calculating hourly aggregations: {str(e)}")
            return 0

    async def _calculate_weekly_aggregations(self, db: Session) -> int:
        """
        Calculate weekly aggregations
        """
        try:
            result = db.execute(text("""
                INSERT INTO dw.aggregations_weekly (
                    year, week_number, location_key, scam_type_key,
                    complaint_count, total_amount, avg_amount
                )
                SELECT
                    dd.year,
                    dd.week_of_year,
                    fc.location_key,
                    fc.scam_type_key,
                    COUNT(fc.complaint_id),
                    SUM(fc.amount),
                    AVG(fc.amount)
                FROM dw.fact_complaints fc
                JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                WHERE fc.date_key >= (SELECT MAX(date_key) - 30 FROM dw.dim_date)
                GROUP BY dd.year, dd.week_of_year, fc.location_key, fc.scam_type_key
                ON CONFLICT (year, week_number, location_key, scam_type_key) DO UPDATE SET
                    complaint_count = EXCLUDED.complaint_count,
                    total_amount = EXCLUDED.total_amount,
                    avg_amount = EXCLUDED.avg_amount
                RETURNING 1
            """))

            return result.rowcount or 0

        except Exception as e:
            logger.error(f"[Data Warehouse] Error calculating weekly aggregations: {str(e)}")
            return 0

    async def _calculate_monthly_aggregations(self, db: Session) -> int:
        """
        Calculate monthly aggregations
        """
        try:
            result = db.execute(text("""
                INSERT INTO dw.aggregations_monthly (
                    year, month, location_key, scam_type_key,
                    complaint_count, total_amount, avg_amount
                )
                SELECT
                    dd.year,
                    dd.month,
                    fc.location_key,
                    fc.scam_type_key,
                    COUNT(fc.complaint_id),
                    SUM(fc.amount),
                    AVG(fc.amount)
                FROM dw.fact_complaints fc
                JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                WHERE fc.date_key >= (SELECT MAX(date_key) - 90 FROM dw.dim_date)
                GROUP BY dd.year, dd.month, fc.location_key, fc.scam_type_key
                ON CONFLICT (year, month, location_key, scam_type_key) DO UPDATE SET
                    complaint_count = EXCLUDED.complaint_count,
                    total_amount = EXCLUDED.total_amount,
                    avg_amount = EXCLUDED.avg_amount
                RETURNING 1
            """))

            return result.rowcount or 0

        except Exception as e:
            logger.error(f"[Data Warehouse] Error calculating monthly aggregations: {str(e)}")
            return 0

    async def refresh_materialized_views(self) -> int:
        """
        Refresh all materialized views
        """
        try:
            with SessionLocal() as db:
                views = [
                    'dw.mv_latest_complaints',
                    'dw.mv_risk_hotspots',
                    'dw.mv_scam_trends',
                    'dw.mv_bank_risk_metrics'
                ]

                refreshed_count = 0

                for view in views:
                    try:
                        db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                        refreshed_count += 1
                        logger.debug(f"[Data Warehouse] Refreshed materialized view: {view}")
                    except Exception as e:
                        logger.warning(f"[Data Warehouse] Could not refresh view {view}: {str(e)}")

                db.commit()

            logger.info(f"[Data Warehouse] Refreshed {refreshed_count} materialized views")
            return refreshed_count

        except Exception as e:
            logger.error(f"[Data Warehouse] Error refreshing materialized views: {str(e)}")
            return 0

    async def get_analytics_dashboard_data(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get data for analytics dashboard
        """
        try:
            with SessionLocal() as db:
                # Get overview metrics
                overview = await self._get_overview_metrics(db, days_back)

                # Get trend data
                trends = await self._get_trend_data(db, days_back)

                # Get hotspot data
                hotspots = await self._get_hotspot_data(db, days_back)

                # Get scam type breakdown
                scam_breakdown = await self._get_scam_breakdown(db, days_back)

                # Get performance metrics
                performance = await self._get_performance_metrics(db, days_back)

                return {
                    'overview': overview,
                    'trends': trends,
                    'hotspots': hotspots,
                    'scam_breakdown': scam_breakdown,
                    'performance': performance,
                    'data_freshness': datetime.utcnow().isoformat(),
                    'period_days': days_back
                }

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting dashboard data: {str(e)}")
            return {}

    async def _get_overview_metrics(self, db: Session, days_back: int) -> Dict[str, Any]:
        """
        Get overview metrics
        """
        try:
            # Total complaints
            result = db.execute(text("""
                SELECT COUNT(*) as total_complaints,
                       SUM(amount) as total_amount,
                       AVG(amount) as avg_amount
                FROM dw.mv_latest_complaints
                WHERE date_value >= CURRENT_DATE - INTERVAL ':days_back days'
            """), {'days_back': days_back}).fetchone()

            # Suspicious transactions
            result2 = db.execute(text("""
                SELECT COUNT(*) as total_transactions,
                       SUM(suspicious_transactions) as suspicious_count,
                       AVG(avg_risk_score) as avg_risk
                FROM dw.mv_bank_risk_metrics
                WHERE date_value >= CURRENT_DATE - INTERVAL ':days_back days'
            """), {'days_back': days_back}).fetchone()

            return {
                'total_complaints': result.total_complaints or 0,
                'total_amount_lost': float(result.total_amount or 0),
                'avg_complaint_amount': float(result.avg_amount or 0),
                'total_transactions': result2.total_transactions or 0,
                'suspicious_transactions': result2.suspicious_count or 0,
                'avg_risk_score': float(result2.avg_risk or 0),
                'suspicious_rate': (result2.suspicious_count / result2.total_transactions * 100) if result2.total_transactions else 0
            }

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting overview metrics: {str(e)}")
            return {}

    async def _get_trend_data(self, db: Session, days_back: int) -> List[Dict]:
        """
        Get trend data
        """
        try:
            result = db.execute(text("""
                SELECT
                    date_value,
                    complaint_count,
                    total_amount
                FROM dw.mv_risk_hotspots
                WHERE date_value >= CURRENT_DATE - INTERVAL ':days_back days'
                GROUP BY date_value, complaint_count, total_amount
                ORDER BY date_value
            """), {'days_back': days_back}).fetchall()

            return [
                {
                    'date': row.date_value.isoformat(),
                    'complaints': row.complaint_count,
                    'amount': float(row.total_amount)
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting trend data: {str(e)}")
            return []

    async def _get_hotspot_data(self, db: Session, days_back: int) -> List[Dict]:
        """
        Get hotspot data
        """
        try:
            result = db.execute(text("""
                SELECT
                    city,
                    state,
                    SUM(complaint_count) as total_complaints,
                    SUM(total_amount) as total_amount,
                    AVG(avg_risk_score) as avg_risk_score
                FROM dw.mv_risk_hotspots
                WHERE date_value >= CURRENT_DATE - INTERVAL ':days_back days'
                GROUP BY city, state
                HAVING SUM(complaint_count) >= 5
                ORDER BY total_complaints DESC
                LIMIT 10
            """), {'days_back': days_back}).fetchall()

            return [
                {
                    'city': row.city,
                    'state': row.state,
                    'complaints': row.total_complaints,
                    'amount': float(row.total_amount),
                    'avg_risk_score': float(row.avg_risk_score)
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting hotspot data: {str(e)}")
            return []

    async def _get_scam_breakdown(self, db: Session, days_back: int) -> List[Dict]:
        """
        Get scam type breakdown
        """
        try:
            result = db.execute(text("""
                SELECT
                    dst.scam_type,
                    dst.category,
                    COUNT(fc.complaint_id) as complaint_count,
                    SUM(fc.amount) as total_amount
                FROM dw.fact_complaints fc
                JOIN dw.dim_date dd ON fc.date_key = dd.date_key
                JOIN dw.dim_scam_type dst ON fc.scam_type_key = dst.scam_type_key
                WHERE dd.date_value >= CURRENT_DATE - INTERVAL ':days_back days'
                GROUP BY dst.scam_type, dst.category
                ORDER BY complaint_count DESC
            """), {'days_back': days_back}).fetchall()

            return [
                {
                    'scam_type': row.scam_type,
                    'category': row.category,
                    'complaints': row.complaint_count,
                    'amount': float(row.total_amount)
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting scam breakdown: {str(e)}")
            return []

    async def _get_performance_metrics(self, db: Session, days_back: int) -> Dict[str, Any]:
        """
        Get performance metrics
        """
        try:
            # Response time metrics
            result = db.execute(text("""
                SELECT AVG(response_time_minutes) as avg_response_time,
                       COUNT(*) as total_alerts
                FROM dw.fact_alerts fa
                JOIN dw.dim_date dd ON fa.date_key = dd.date_key
                WHERE dd.date_value >= CURRENT_DATE - INTERVAL ':days_back days'
            """), {'days_back': days_back}).fetchone()

            # Data freshness
            result2 = db.execute(text("""
                SELECT MAX(fc.date_key) as latest_complaint_date,
                       MAX(ft.date_key) as latest_transaction_date
                FROM dw.fact_complaints fc
                CROSS JOIN dw.fact_transactions ft
            """)).fetchone()

            return {
                'avg_response_time_minutes': float(result.avg_response_time or 0),
                'total_alerts': result.total_alerts or 0,
                'latest_complaint_date': str(result2.latest_complaint_date or 'N/A'),
                'latest_transaction_date': str(result2.latest_transaction_date or 'N/A')
            }

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting performance metrics: {str(e)}")
            return {}

    async def get_warehouse_status(self) -> Dict[str, Any]:
        """
        Get data warehouse status
        """
        try:
            with SessionLocal() as db:
                # Get table counts
                fact_counts = {}
                for table in ['fact_complaints', 'fact_transactions', 'fact_i4c_crimes', 'fact_alerts']:
                    result = db.execute(text(f"SELECT COUNT(*) FROM dw.{table}")).fetchone()
                    fact_counts[table] = result.count if result else 0

                # Get dimension counts
                dim_counts = {}
                for table in ['dim_date', 'dim_location', 'dim_scam_type', 'dim_bank']:
                    result = db.execute(text(f"SELECT COUNT(*) FROM dw.{table}")).fetchone()
                    dim_counts[table] = result.count if result else 0

                # Get aggregation counts
                agg_counts = {}
                for table in ['aggregations_hourly', 'aggregations_daily', 'aggregations_weekly', 'aggregations_monthly']:
                    result = db.execute(text(f"SELECT COUNT(*) FROM dw.{table}")).fetchone()
                    agg_counts[table] = result.count if result else 0

                return {
                    'fact_tables': fact_counts,
                    'dimension_tables': dim_counts,
                    'aggregation_tables': agg_counts,
                    'metrics_defined': len(self.metric_definitions),
                    'reports_defined': len(self.report_definitions),
                    'materialized_views': len(self.materialized_views),
                    'last_updated': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"[Data Warehouse] Error getting warehouse status: {str(e)}")
            return {'error': str(e)}

# Global data warehouse instance
data_warehouse = DataWarehouse()