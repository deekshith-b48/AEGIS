"""
Database Configuration and Connection Management for Project AEGIS
PostgreSQL with PostGIS for geospatial capabilities
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "aegis_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "sslmode": os.getenv("DB_SSL_MODE", "prefer"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    "echo": os.getenv("DB_ECHO", "false").lower() == "true"
}

# Construct database URL
DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?sslmode={DATABASE_CONFIG['sslmode']}"

# Base model for declarative models
Base = declarative_base()

# Create engine with optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_CONFIG["pool_size"],
    max_overflow=DATABASE_CONFIG["max_overflow"],
    pool_timeout=DATABASE_CONFIG["pool_timeout"],
    pool_recycle=DATABASE_CONFIG["pool_recycle"],
    echo=DATABASE_CONFIG["echo"],
    # Additional optimizations
    pool_pre_ping=True,
    pool_use_lifo=True,
    connect_args={
        "command_timeout": 60,
        "application_name": "Project AEGIS",
        "connect_timeout": 30,
    }
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

class DatabaseManager:
    """
    Advanced database connection manager for Project AEGIS
    Handles connections, transactions, and performance monitoring
    """

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.connection_stats = {
            "total_queries": 0,
            "failed_queries": 0,
            "average_query_time": 0.0,
            "active_connections": 0,
            "pooled_connections": 0
        }

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @asynccontextmanager
    async def get_async_session(self):
        """Async context manager for database sessions"""
        session = self.get_session()
        try:
            yield session
            await self._update_connection_stats(True)
        except Exception as e:
            await session.rollback()
            await self._update_connection_stats(False)
            raise
        finally:
            session.close()

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """Execute a raw SQL query and return results"""
        try:
            with self.get_session() as session:
                start_time = datetime.now()
                result = session.execute(text(query), params or {})
                execution_time = (datetime.now() - start_time).total_seconds() * 1000

                # Update statistics
                self.connection_stats["total_queries"] += 1
                self._update_query_time(execution_time)

                return result.fetchall()
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"Database query failed: {str(e)}")
            raise

    async def execute_transaction(self, queries: list) -> bool:
        """Execute multiple queries in a single transaction"""
        try:
            with self.get_session() as session:
                session.begin()
                try:
                    for query_info in queries:
                        if isinstance(query_info, dict):
                            session.execute(text(query_info["query"]), query_info.get("params", {}))
                        else:
                            session.execute(text(query_info))

                    session.commit()
                    return True
                except Exception as e:
                    session.rollback()
                    raise
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            return False

    async def check_connection(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1 as health_check"))
                health_check = result.fetchone()

                # Get database stats
                stats_result = session.execute(text("""
                    SELECT
                        datname as database_name,
                        numbackends as connections,
                        xact_commit as transactions_committed,
                        xact_rollback as transactions_rolled_back,
                        blks_read as blocks_read,
                        blks_hit as blocks_hit
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """))
                db_stats = stats_result.fetchone()

                # Get table sizes
                table_stats_result = session.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """))
                table_stats = table_stats_result.fetchall()

                return {
                    "status": "healthy",
                    "database_url": f"{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}",
                    "connection_pool": {
                        "size": self.engine.pool.size(),
                        "checked_in": self.engine.pool.checkedin(),
                        "checked_out": self.engine.pool.checkedout(),
                        "overflow": self.engine.pool.overflow()
                    },
                    "database_stats": {
                        "database_name": db_stats.database_name if db_stats else None,
                        "active_connections": db_stats.connections if db_stats else 0,
                        "transactions_committed": db_stats.transactions_committed if db_stats else 0,
                        "transactions_rolled_back": db_stats.transactions_rolled_back if db_stats else 0,
                        "cache_hit_ratio": (
                            db_stats.blocks_hit / (db_stats.blocks_read + db_stats.blocks_hit) * 100
                            if db_stats and db_stats.blocks_read > 0 else 0
                        )
                    },
                    "largest_tables": [
                        {
                            "schema": row.schemaname,
                            "table": row.tablename,
                            "size": row.size
                        } for row in table_stats
                    ],
                    "query_stats": self.connection_stats
                }

        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_url": f"{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            }

    async def initialize_postgis(self) -> bool:
        """Initialize PostGIS extensions for geospatial features"""
        try:
            with self.get_session() as session:
                # Enable PostGIS extension
                session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
                session.execute(text("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch"))
                session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

                # Create spatial index on locations table if it exists
                try:
                    session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_locations_geometry
                        ON locations
                        USING GIST (ST_Point(longitude, latitude))
                    """))
                except Exception:
                    # Locations table might not exist yet
                    pass

                session.commit()
                logger.info("✅ PostGIS extensions initialized successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize PostGIS: {str(e)}")
            return False

    async def create_indexes(self) -> bool:
        """Create optimized indexes for better performance"""
        try:
            indexes = [
                # Complaints table indexes
                "CREATE INDEX IF NOT EXISTS idx_complaints_gin_features ON complaints USING GIN (features)",
                "CREATE INDEX IF NOT EXISTS idx_complaints_gin_metadata ON complaints USING GIN (metadata)",
                "CREATE INDEX IF NOT EXISTS idx_complaints_gin_scammer_details ON complaints USING GIN (scammermer_details)",

                # Predictions table indexes
                "CREATE INDEX IF NOT EXISTS idx_predictions_gin_data ON predictions USING GIN (data)",

                # Learning data indexes
                "CREATE INDEX IF NOT EXISTS idx_learning_data_gin_features ON learning_data USING GIN (features)",
                "CREATE INDEX IF NOT EXISTS idx_learning_data_gin_labels ON learning_data USING GIN (labels)",

                # Analytics indexes
                "CREATE INDEX IF NOT EXISTS idx_analytics_gin_dimensions ON analytics_metrics USING GIN (dimensions)",
                "CREATE INDEX IF NOT EXISTS idx_dashboard_gin_data ON dashboard_data USING GIN (data)",

                # System health indexes
                "CREATE INDEX IF NOT EXISTS idx_health_gin_metadata ON system_health USING GIN (metadata)",

                # Full-text search indexes
                "CREATE INDEX IF NOT EXISTS idx_complaints_fulltext ON complaints USING GIN (to_tsvector('english', complaint_type || ' ' || COALESCE(victim_location, '')))",
                "CREATE INDEX IF NOT EXISTS idx_locations_fulltext ON locations USING GIN (to_tsvector('english', name || ' ' || COALESCE(address, '') || ' ' || COALESCE(city, '') || ' ' || COALESCE(state, '')))",
            ]

            with self.get_session() as session:
                for index_query in indexes:
                    try:
                        session.execute(text(index_query))
                        logger.debug(f"✅ Created index: {index_query[:50]}...")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create index: {str(e)}")

                session.commit()
                logger.info("✅ Database indexes created successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {str(e)}")
            return False

    async def vacuum_analyze(self) -> bool:
        """Run VACUUM ANALYZE for database maintenance"""
        try:
            with self.get_session() as session:
                # Run ANALYZE first (less blocking)
                session.execute(text("ANALYZE"))
                session.commit()

                # Run VACUUM on specific tables if needed (in production, use proper scheduling)
                tables_to_vacuum = [
                    "complaints",
                    "predictions",
                    "learning_data",
                    "analytics_metrics"
                ]

                for table in tables_to_vacuum:
                    try:
                        session.execute(text(f"VACUUM ANALYZE {table}"))
                        logger.info(f"✅ VACUUM ANALYZE completed for {table}")
                    except Exception as e:
                        logger.warning(f"⚠️ VACUUM failed for {table}: {str(e)}")

                logger.info("✅ Database maintenance completed")
                return True

        except Exception as e:
            logger.error(f"❌ Database maintenance failed: {str(e)}")
            return False

    async def backup_schema(self) -> Dict[str, Any]:
        """Generate schema backup information"""
        try:
            with self.get_session() as session:
                # Get table schemas
                tables_result = session.execute(text("""
                    SELECT table_name, column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """))
                schema_info = tables_result.fetchall()

                # Get constraints
                constraints_result = session.execute(text("""
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                    ORDER BY tc.table_name, tc.constraint_name
                """))
                constraints_info = constraints_result.fetchall()

                # Get indexes
                indexes_result = session.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """))
                indexes_info = indexes_result.fetchall()

                return {
                    "tables": [
                        {
                            "table": row.table_name,
                            "column": row.column_name,
                            "type": row.data_type,
                            "nullable": row.is_nullable,
                            "default": row.column_default
                        } for row in schema_info
                    ],
                    "constraints": [
                        {
                            "table": row.table_name,
                            "name": row.constraint_name,
                            "type": row.constraint_type,
                            "column": row.column_name
                        } for row in constraints_info
                    ],
                    "indexes": [
                        {
                            "schema": row.schemaname,
                            "table": row.tablename,
                            "name": row.indexname,
                            "definition": row.indexdef
                        } for row in indexes_info
                    ],
                    "generated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ Schema backup failed: {str(e)}")
            return {"error": str(e)}

    def _update_connection_stats(self, success: bool) -> None:
        """Update connection statistics"""
        if not success:
            self.connection_stats["failed_queries"] += 1

    def _update_query_time(self, execution_time_ms: float) -> None:
        """Update average query time"""
        total = self.connection_stats["total_queries"]
        current_avg = self.connection_stats["average_query_time"]
        self.connection_stats["average_query_time"] = ((current_avg * (total - 1)) + execution_time_ms) / total

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        pool = self.engine.pool
        return {
            **self.connection_stats,
            "pool_status": {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            },
            "engine_url": str(self.engine.url).replace(self.engine.url.password or "", "***")
        }

# Global database manager instance
database_manager = DatabaseManager()

# Dependency for FastAPI routes
def get_db():
    """FastAPI dependency for database session"""
    db = database_manager.get_session()
    try:
        yield db
    finally:
        db.close()

# Event listeners for connection lifecycle
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure connection settings"""
    if "postgresql" in str(dbapi_connection):
        # PostgreSQL-specific settings
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET SESSION TIME ZONE 'UTC'")
            cursor.execute("SET statement_timeout = '300s'")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout"""
    connection_record.info["checked_out"] = datetime.utcnow()

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin"""
    connection_record.info["checked_in"] = datetime.utcnow()

async def initialize_database() -> bool:
    """Initialize database with all required features"""
    try:
        logger.info("🔄 Initializing Project AEGIS database...")

        # Check connection
        health = await database_manager.check_connection()
        if health["status"] != "healthy":
            logger.error(f"❌ Database connection failed: {health.get('error')}")
            return False

        # Initialize PostGIS
        if not await database_manager.initialize_postgis():
            logger.error("❌ PostGIS initialization failed")
            return False

        # Create indexes
        if not await database_manager.create_indexes():
            logger.error("❌ Index creation failed")
            return False

        logger.info("✅ Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        return False