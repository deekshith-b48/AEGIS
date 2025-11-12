"""
Database Migrations for Project AEGIS
Comprehensive database schema with migration support
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

class AEGISDatabaseMigrations:
    """
    Database migration system for Project AEGIS
    Handles schema creation, updates, and data initialization
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Migration version tracking
        self.migration_versions = {
            "001_initial_schema": self._create_initial_schema,
            "002_enhanced_ai_models": self._create_enhanced_ai_tables,
            "003_realtime_features": self._create_realtime_tables,
            "004_learning_system": self._create_learning_tables,
            "005_geospatial_tables": self._create_geospatial_tables,
            "006_analytics_tables": self._create_analytics_tables,
            "007_websocket_tables": self._create_websocket_tables,
            "008_audit_logging": self._create_audit_tables,
            "009_performance_monitoring": self._create_performance_tables,
            "010_integration_tables": self._create_integration_tables
        }

    async def run_migrations(self) -> bool:
        """
        Run all pending database migrations
        """
        try:
            logger.info("🔄 Starting database migrations...")

            # Check if migrations table exists, create if not
            await self._create_migrations_table()

            # Get current migration version
            current_version = await self._get_current_migration_version()

            # Run migrations in order
            migrations_to_run = []
            for migration_id, migration_func in self.migration_versions.items():
                migration_number = int(migration_id.split('_')[0])
                current_number = int(current_version.split('_')[0]) if current_version else 0
                if migration_number > current_number:
                    migrations_to_run.append((migration_id, migration_func))

            if not migrations_to_run:
                logger.info("✅ Database schema is up to date")
                return True

            # Run pending migrations
            for migration_id, migration_func in migrations_to_run:
                logger.info(f"🔄 Running migration: {migration_id}")
                try:
                    await migration_func()
                    await self._record_migration(migration_id)
                    logger.info(f"✅ Migration {migration_id} completed successfully")
                except Exception as e:
                    logger.error(f"❌ Migration {migration_id} failed: {str(e)}")
                    return False

            logger.info("✅ All database migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error running migrations: {str(e)}")
            return False

    async def _create_migrations_table(self) -> None:
        """Create migrations version tracking table"""
        async with self.SessionLocal() as session:
            try:
                # Check if table exists
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'schema_migrations'
                    )
                """))
                table_exists = result.scalar()

                if not table_exists:
                    await session.execute(text("""
                        CREATE TABLE schema_migrations (
                            migration_id VARCHAR(50) PRIMARY KEY,
                            description TEXT,
                            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            status VARCHAR(20) DEFAULT 'completed',
                            duration_seconds INTEGER,
                            checksum VARCHAR(64)
                        )
                    """))
                    await session.commit()
                    logger.info("📝 Created schema_migrations table")

            except Exception as e:
                logger.error(f"❌ Error creating migrations table: {str(e)}")
                raise

    async def _get_current_migration_version(self) -> str:
        """Get the latest applied migration version"""
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT migration_id
                    FROM schema_migrations
                    WHERE status = 'completed'
                    ORDER BY applied_at DESC
                    LIMIT 1
                """))
                row = result.fetchone()
                return row[0] if row else "000_initial"
            except Exception as e:
                logger.warning(f"⚠️ Could not get current migration version: {str(e)}")
                return "000_initial"

    async def _record_migration(self, migration_id: str) -> None:
        """Record a completed migration"""
        async with self.SessionLocal() as session:
            try:
                await session.execute(text("""
                    INSERT INTO schema_migrations (
                        migration_id, description, status, applied_at
                    ) VALUES (
                        :migration_id, :description, 'completed', NOW()
                    )
                """), {
                    "migration_id": migration_id,
                    "description": f"Applied migration {migration_id}"
                })
                await session.commit()
            except Exception as e:
                logger.error(f"❌ Error recording migration {migration_id}: {str(e)}")

    async def _create_initial_schema(self) -> None:
        """Create initial database schema"""
        async with self.SessionLocal() as session:
            try:
                # Complaints table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS complaints (
                        id VARCHAR(50) PRIMARY KEY,
                        complaint_type VARCHAR(100) NOT NULL,
                        amount DECIMAL(15,2) NOT NULL,
                        victim_location VARCHAR(255) NOT NULL,
                        victim_contact_encrypted TEXT,
                        scammer_details JSONB,
                        transaction_details JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'pending',
                        priority VARCHAR(20) DEFAULT 'medium',
                        metadata JSONB,
                        INDEX idx_complaints_created_at (created_at),
                        INDEX idx_complaints_status (status),
                        INDEX idx_complaints_priority (priority)
                    )
                """))

                # Predictions table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id VARCHAR(50) PRIMARY KEY,
                        complaint_id VARCHAR(50) REFERENCES complaints(id),
                        location_name VARCHAR(255) NOT NULL,
                        location_lat DECIMAL(10,8),
                        location_lon DECIMAL(11,8),
                        confidence_score DECIMAL(5,4),
                        risk_level VARCHAR(20) NOT NULL,
                        time_window_start TIMESTAMP WITH TIME ZONE,
                        time_window_end TIMESTAMP WITH TIME ZONE,
                        prediction_models TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_predictions_created_at (created_at),
                        INDEX idx_predictions_confidence (confidence_score),
                        INDEX idx_predictions_risk (risk_level)
                    )
                """))

                # Locations table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS locations (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        address TEXT,
                        latitude DECIMAL(10,8) NOT NULL,
                        longitude DECIMAL(11,8) NOT NULL,
                        postal_code VARCHAR(20),
                        city VARCHAR(100),
                        state VARCHAR(100),
                        country VARCHAR(100) DEFAULT 'India',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_locations_coordinates (latitude, longitude),
                        INDEX idx_locations_city (city),
                        INDEX idx_locations_postal (postal_code)
                    )
                """))

                # Users table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        email VARCHAR(255) UNIQUE,
                        role VARCHAR(50) NOT NULL,
                        department VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login TIMESTAMP WITH TIME ZONE,
                        permissions JSONB,
                        INDEX idx_users_role (role),
                        INDEX idx_users_active (is_active)
                    )
                """))

                logger.info("📝 Created initial schema tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating initial schema: {str(e)}")
                raise

    async def _create_enhanced_ai_tables(self) -> None:
        """Create tables for enhanced AI models"""
        async with self.SessionLocal() as session:
            try:
                # Federated Causal Graph table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS federated_causal_graph_nodes (
                        id SERIAL PRIMARY KEY,
                        node_type VARCHAR(50) NOT NULL,
                        node_data JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_nodes_type (node_type)
                    )
                """))

                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS federated_causal_graph_edges (
                        id SERIAL PRIMARY KEY,
                        source_node_id INTEGER REFERENCES federated_causal_graph_nodes(id),
                        target_node_id INTEGER REFERENCES federated_causal_graph_nodes(id),
                        relationship_type VARCHAR(50) NOT NULL,
                        weight DECIMAL(10,4),
                        confidence DECIMAL(5,4),
                        temporal_constraint JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_edges_source (source_node_id),
                        INDEX idx_edges_target (target_node_id),
                        INDEX idx_edges_type (relationship_type)
                    )
                """))

                # Behavioral Digital Twin table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS behavioral_profiles (
                        id SERIAL PRIMARY KEY,
                        user_anon_id VARCHAR(100) NOT NULL,
                        behavior_patterns JSONB,
                        risk_score DECIMAL(5,4),
                        predicted_behaviors JSONB,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_profiles_user (user_anon_id),
                        INDEX idx_profiles_active (is_active),
                        INDEX idx_profiles_risk (risk_score)
                    )
                """))

                logger.info("📝 Created enhanced AI model tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating enhanced AI tables: {str(e)}")
                raise

    async def _create_realtime_tables(self) -> None:
        """Create tables for real-time features"""
        async with self.SessionLocal() as session:
            try:
                # Digital Cordons table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS digital_cordons (
                        cordon_id VARCHAR(50) PRIMARY KEY,
                        target_type VARCHAR(50) NOT NULL,
                        target_value VARCHAR(255) NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        priority VARCHAR(20) NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE,
                        created_by VARCHAR(100),
                        evidence JSONB,
                        npcii_reference VARCHAR(100),
                        affected_accounts TEXT[],
                        INDEX idx_cordons_status (status),
                        INDEX idx_cordons_priority (priority),
                        INDEX idx_cordons_expires (expires_at)
                    )
                """))

                # Real-time predictions table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS realtime_predictions (
                        id VARCHAR(50) PRIMARY KEY,
                        complaint_id VARCHAR(50) REFERENCES complaints(id),
                        model_version VARCHAR(20) NOT NULL,
                        predictions JSONB,
                        processing_time_ms INTEGER,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_realtime_created_at (created_at),
                        INDEX idx_realtime_model (model_version)
                    )
                """))

                # Alerts table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        alert_id VARCHAR(50) PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        channels TEXT[],
                        recipients JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'active',
                        acknowledged_at TIMESTAMP WITH TIME ZONE,
                        acknowledged_by VARCHAR(100),
                        metadata JSONB,
                        INDEX idx_alerts_severity (severity),
                        INDEX idx_alerts_status (status),
                        INDEX idx_alerts_created (created_at)
                    )
                """))

                logger.info("📝 Created real-time feature tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating real-time tables: {str(e)}")
                raise

    async def _create_learning_tables(self) -> None:
        """Create tables for continuous learning system"""
        async with self.SessionLocal() as session:
            try:
                # Learning data table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS learning_data (
                        data_id VARCHAR(50) PRIMARY KEY,
                        features JSONB NOT NULL,
                        labels JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        source VARCHAR(100) NOT NULL,
                        data_type VARCHAR(50) NOT NULL,
                        quality_score DECIMAL(5,4),
                        metadata JSONB,
                        INDEX idx_learning_timestamp (timestamp),
                        INDEX idx_learning_source (source),
                        INDEX idx_learning_type (data_type),
                        INDEX idx_learning_quality (quality_score)
                    )
                """))

                # Model deployments table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS model_deployments (
                        model_id VARCHAR(50) PRIMARY KEY,
                        model_type VARCHAR(50) NOT NULL,
                        version INTEGER NOT NULL,
                        performance_metrics JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        model_path VARCHAR(255),
                        metadata JSONB,
                        INDEX idx_deployments_type (model_type),
                        INDEX idx_deployments_version (version)
                    )
                """))

                # Learning results table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS learning_results (
                        learning_id VARCHAR(50) PRIMARY KEY,
                        model_id VARCHAR(50) REFERENCES model_deployments(model_id),
                        success BOOLEAN NOT NULL,
                        training_time_seconds DECIMAL(10,4),
                        performance_metrics JSONB,
                        validation_metrics JSONB,
                        improvement_metrics JSONB,
                        error_message TEXT,
                        warnings TEXT[],
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_results_success (success),
                        INDEX idx_results_created (created_at)
                    )
                """))

                logger.info("📝 Created continuous learning tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating learning tables: {str(e)}")
                raise

    async def _create_geospatial_tables(self) -> None:
        """Create tables for geospatial features"""
        async with self.SessionLocal() as session:
            try:
                # GIS hotspots table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS gis_hotspots (
                        id SERIAL PRIMARY KEY,
                        location_id INTEGER REFERENCES locations(id),
                        hotspot_type VARCHAR(50) NOT NULL,
                        severity_score DECIMAL(5,4),
                        confidence DECIMAL(5,4),
                        radius_meters INTEGER,
                        detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE,
                        is_active BOOLEAN DEFAULT TRUE,
                        metadata JSONB,
                        INDEX idx_hotspots_active (is_active),
                        INDEX idx_hotspots_severity (severity_score),
                        INDEX idx_hotspots_expires (expires_at)
                    )
                """))

                # Geofences table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS geofences (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        fence_type VARCHAR(50) NOT NULL, -- 'circle', 'polygon', 'rectangle'
                        coordinates JSONB NOT NULL,
                        radius_meters DECIMAL(10,2), -- for circle fences
                        created_by VARCHAR(100),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT TRUE,
                        metadata JSONB,
                        INDEX idx_geofences_active (is_active)
                    )
                """))

                # Location predictions table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS location_predictions (
                        id VARCHAR(50) PRIMARY KEY,
                        prediction_id VARCHAR(50) REFERENCES predictions(id),
                        sequence_number INTEGER NOT NULL,
                        predicted_location_id INTEGER REFERENCES locations(id),
                        cash_probability DECIMAL(5,4),
                        time_probability DECIMAL(5,4),
                        combined_score DECIMAL(5,4),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_locpred_sequence (sequence_number),
                        INDEX idx_locpred_scores (combined_score)
                    )
                """))

                logger.info("📝 Created geospatial tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating geospatial tables: {str(e)}")
                raise

    async def _create_analytics_tables(self) -> None:
        """Create tables for analytics and reporting"""
        async with self.SessionLocal() as session:
            try:
                # Analytics metrics table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15,6) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        dimensions JSONB,
                        INDEX idx_metrics_timestamp (timestamp),
                        INDEX idx_metrics_name (metric_name)
                    )
                """))

                # Performance dashboard data
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS dashboard_data (
                        id SERIAL PRIMARY KEY,
                        widget_type VARCHAR(50) NOT NULL,
                        data JSONB NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW,
                        is_current BOOLEAN DEFAULT TRUE,
                        INDEX idx_dashboard_widget (widget_type),
                        INDEX idx_dashboard_timestamp (timestamp)
                    )
                """))

                # System health monitoring
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_health (
                        id SERIAL PRIMARY KEY,
                        component_name VARCHAR(100) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        metadata JSONB,
                        INDEX idx_health_component (component_name),
                        INDEX idx_health_timestamp (timestamp),
                        INDEX idx_health_status (status)
                    )
                """))

                logger.info("📝 Created analytics tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating analytics tables: {str(e)}")
                raise

    async def _create_websocket_tables(self) -> None:
        """Create tables for WebSocket connection management"""
        async with self.SessionLocal() as session:
            try:
                # WebSocket connections table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS websocket_connections (
                        connection_id VARCHAR(100) PRIMARY KEY,
                        user_id VARCHAR(100),
                        client_role VARCHAR(50) NOT NULL,
                        connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        disconnected_at TIMESTAMP WITH TIME ZONE,
                        subscriptions TEXT[],
                        metadata JSONB,
                        INDEX idx_connections_user (user_id),
                        INDEX idx_connections_role (client_role),
                        INDEX idx_connections_active (disconnected_at IS NULL)
                    )
                """))

                # WebSocket messages log
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS websocket_messages (
                        id SERIAL PRIMARY KEY,
                        connection_id VARCHAR(100) REFERENCES websocket_connections(connection_id),
                        message_type VARCHAR(50) NOT NULL,
                        message_data JSONB,
                        direction VARCHAR(10) NOT NULL, -- 'in', 'out'
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_messages_connection (connection_id),
                        INDEX idx_messages_type (message_type),
                        INDEX idx_messages_timestamp (timestamp)
                    )
                """))

                logger.info("📝 Created WebSocket tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating WebSocket tables: {str(e)}")
                raise

    async def _create_audit_tables(self) -> None:
        """Create tables for audit logging"""
        async with self.SessionLocal() as session:
            try:
                # Audit log table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id SERIAL PRIMARY KEY,
                        action VARCHAR(100) NOT NULL,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_id VARCHAR(255),
                        user_id VARCHAR(100) NOT NULL,
                        user_role VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT,
                        status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'denied'
                        error_message TEXT,
                        metadata JSONB,
                        INDEX idx_audit_user (user_id),
                        INDEX idx_audit_action (action),
                        INDEX idx_audit_timestamp (timestamp),
                        INDEX idx_audit_status (status)
                    )
                """))

                # Data access log
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS data_access_log (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(100) NOT NULL,
                        operation VARCHAR(20) NOT NULL, -- 'read', 'write', 'delete'
                        record_id VARCHAR(255),
                        user_id VARCHAR(100) NOT NULL,
                        access_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        was_authorized BOOLEAN NOT NULL,
                        details JSONB,
                        INDEX idx_access_user (user_id),
                        INDEX idx_access_table (table_name),
                        INDEX idx_access_operation (operation)
                    )
                """))

                logger.info("📝 Created audit logging tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating audit tables: {str(e)}")
                raise

    async def _create_performance_tables(self) -> None:
        """Create tables for performance monitoring"""
        async with self.SessionLocal() as session:
            try:
                # Performance metrics table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15,6) NOT NULL,
                        unit VARCHAR(50),
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        dimensions JSONB,
                        INDEX idx_perf_name (metric_name),
                        INDEX idx_perf_timestamp (timestamp)
                    )
                """))

                # Query performance log
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS query_performance (
                        id SERIAL PRIMARY KEY,
                        query_type VARCHAR(50) NOT NULL,
                        execution_time_ms DECIMAL(10,4),
                        rows_affected INTEGER,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        user_id VARCHAR(100),
                        query_details JSONB,
                        INDEX idx_queryperf_type (query_type),
                        INDEX idx_queryperf_time (execution_time_ms),
                        INDEX idx_queryperf_timestamp (timestamp)
                    )
                """))

                # System resources monitoring
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_resources (
                        id SERIAL PRIMARY KEY,
                        cpu_usage_percent DECIMAL(5,2),
                        memory_usage_mb DECIMAL(10,2),
                        disk_usage_percent DECIMAL(5,2),
                        network_io_mb_s DECIMAL(10,2),
                        active_connections INTEGER,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_resources_timestamp (timestamp)
                    )
                """))

                logger.info("📝 Created performance monitoring tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating performance tables: {str(e)}")
                raise

    async def _create_integration_tables(self) -> None:
        """Create tables for external system integrations"""
        async with self.SessionLocal() as session:
            try:
                # External API integrations
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS api_integrations (
                        id SERIAL PRIMARY KEY,
                        service_name VARCHAR(100) UNIQUE NOT NULL,
                        api_base_url VARCHAR(500) NOT NULL,
                        api_version VARCHAR(20),
                        auth_method VARCHAR(50) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'unknown',
                        error_message TEXT,
                        configuration JSONB,
                        INDEX idx_integration_active (is_active),
                        INDEX idx_integration_status (status)
                    )
                """))

                # API call logs
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS api_call_logs (
                        id SERIAL PRIMARY KEY,
                        integration_id INTEGER REFERENCES api_integrations(id),
                        endpoint VARCHAR(255) NOT NULL,
                        method VARCHAR(10) NOT NULL,
                        request_data JSONB,
                        response_data JSONB,
                        status_code INTEGER,
                        response_time_ms INTEGER,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        error_message TEXT,
                        INDEX idx_apicall_integration (integration_id),
                        INDEX idx_apicall_status (status_code),
                        INDEX idx_apicall_time (response_time_ms)
                    )
                """))

                # Webhook deliveries
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS webhook_deliveries (
                        id SERIAL PRIMARY KEY,
                        webhook_url VARCHAR(500) NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        payload JSONB NOT NULL,
                        delivery_status VARCHAR(50) NOT NULL,
                        attempt_number INTEGER DEFAULT 1,
                        response_code INTEGER,
                        response_time_ms INTEGER,
                        scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        delivered_at TIMESTAMP WITH TIME ZONE,
                        error_message TEXT,
                        INDEX idx_webhook_status (delivery_status),
                        INDEX idx_webhook_event (event_type),
                        INDEX idx_webhook_scheduled (scheduled_at)
                    )
                """))

                logger.info("📝 Created integration tables")
                await session.commit()

            except Exception as e:
                logger.error(f"❌ Error creating integration tables: {str(e)}")
                raise

    async def initialize_default_data(self) -> None:
        """Initialize default data for the system"""
        try:
            async with self.SessionLocal() as session:
                # Create default admin user
                await session.execute(text("""
                    INSERT INTO users (user_id, name, email, role, is_active, permissions)
                    VALUES (
                        'admin@aegis.gov.in',
                        'System Administrator',
                        'admin@aegis.gov.in',
                        'administrator',
                        TRUE,
                        '{"read": true, "write": true, "delete": true, "manage_users": true}'
                    )
                    ON CONFLICT (user_id) DO NOTHING
                """))

                # Create default locations (major Indian cities)
                default_locations = [
                    ('Mumbai Central', 'Mumbai, Maharashtra', 19.0760, 72.8777, '400001'),
                    ('Delhi Nehru Place', 'New Delhi, Delhi', 28.6139, 77.2090, '110001'),
                    ('Bangalore MG Road', 'Bangalore, Karnataka', 12.9716, 77.5946, '560001'),
                    ('Chennai T Nagar', 'Chennai, Tamil Nadu', 13.0827, 80.2707, '600001'),
                    ('Kolkata Park Street', 'Kolkata, West Bengal', 22.5726, 88.3639, '700001'),
                    ('Hyderabad Charminar', 'Hyderabad, Telangana', 17.3850, 78.4867, '500001'),
                ]

                for name, address, lat, lon, postal in default_locations:
                    await session.execute(text("""
                        INSERT INTO locations (name, address, latitude, longitude, postal_code, city, state)
                        VALUES (:name, :address, :lat, :lon, :postal, :city, :state)
                        ON CONFLICT (name) DO NOTHING
                    """), {
                        "name": name,
                        "address": address,
                        "lat": lat,
                        "lon": lon,
                        "postal": postal,
                        "city": address.split(',')[0],
                        "state": address.split(',')[1]
                    })

                logger.info("📝 Initialized default data")
                await session.commit()

        except Exception as e:
            logger.error(f"❌ Error initializing default data: {str(e)}")

    async def get_schema_version(self) -> Dict[str, Any]:
        """Get current database schema version"""
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(text("""
                    SELECT migration_id, applied_at
                    FROM schema_migrations
                    WHERE status = 'completed'
                    ORDER BY applied_at DESC
                """))
                migrations = result.fetchall()

                tables_result = await session.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = tables_result.fetchall()

                return {
                    "current_migration": migrations[0][0] if migrations else "000_initial",
                    "migrations_applied": [m[0] for m in migrations],
                    "total_tables": len(tables),
                    "schema_version": "2.0.0"
                }

        except Exception as e:
            logger.error(f"❌ Error getting schema version: {str(e)}")
            return {"error": str(e)}