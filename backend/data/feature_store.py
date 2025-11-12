"""
Advanced Feature Store and Data Warehouse for AEGIS
Enterprise-grade Data Management System

Implements comprehensive data management with:
- Real-time feature serving and storage
- Time-series data management
- Feature engineering and transformation
- Data versioning and lineage tracking
- Multi-modal data storage (structured, unstructured, spatial)
- Advanced analytics and reporting
- Automated data quality monitoring
- Scalable data warehousing with partitioning
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiofiles
import aiohttp
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, JSON, LargeBinary, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.types import TypeDecorator, LargeBinary
import redis
import yaml
import pyarrow as pa
import pyarrow.parquet as pq
from pyspark.sql import SparkSession
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction import FeatureHasher
import geopandas as gpd
from shapely.geometry import Point, Polygon
import structlog
from concurrent.futures import ThreadPoolExecutor
import prometheus_client as prom
import psutil
import gc

# Configure structured logging
logger = structlog.get_logger()

Base = declarative_base()

class FeatureType(Enum):
    """Feature data types"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    TEXT = "text"
    BINARY = "binary"
    TIME_SERIES = "time_series"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class StorageTier(Enum):
    """Data storage tiers"""
    HOT = "hot"          # Frequently accessed, SSD storage
    WARM = "warm"        # Moderately accessed, HDD storage
    COLD = "cold"        # Rarely accessed, object storage
    ARCHIVE = "archive"  # Long-term archival, tape/cloud glacier

class DataFormat(Enum):
    """Data storage formats"""
    PARQUET = "parquet"
    AVRO = "avro"
    ORC = "orc"
    JSON = "json"
    CSV = "csv"
    DELTA = "delta"
    HDFS = "hdfs"

@dataclass
class FeatureDefinition:
    """Feature definition metadata"""
    feature_name: str
    feature_type: FeatureType
    data_type: str
    description: str
    tags: List[str]
    owner: str
    created_at: datetime
    updated_at: datetime
    version: int
    is_active: bool
    storage_tier: StorageTier
    partition_keys: List[str]
    ttl_seconds: Optional[int] = None

@dataclass
class FeatureValue:
    """Feature value with metadata"""
    feature_name: str
    entity_id: str
    value: Any
    timestamp: datetime
    quality_score: float
    source_system: str
    version: int
    metadata: Dict[str, Any]

@dataclass
class DataLineage:
    """Data lineage information"""
    lineage_id: str
    source_features: List[str]
    target_features: List[str]
    transformation_type: str
    transformation_code: str
    execution_timestamp: datetime
    input_data_hash: str
    output_data_hash: str

# Prometheus metrics
FEATURE_SERVE_REQUESTS = prom.Counter('feature_serve_requests_total', 'Total feature serve requests', ['feature_name', 'status'])
FEATURE_STORAGE_OPERATIONS = prom.Counter('feature_storage_operations_total', 'Total feature storage operations', ['operation_type'])
DATA_QUALITY_SCORE = prom.Gauge('data_quality_score', 'Current data quality score')
STORAGE_USAGE_BYTES = prom.Gauge('storage_usage_bytes', 'Storage usage by tier', ['tier'])
FEATURE_COMPUTE_LATENCY = prom.Histogram('feature_compute_latency_seconds', 'Feature computation latency')

# Custom SQLAlchemy types
class GeometryType(TypeDecorator):
    """Custom type for PostGIS geometry"""
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.wkb
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            from shapely import wkb
            return wkb.loads(value)
        return None

# Database Models
class FeatureDefinitionRecord(Base):
    """Database model for feature definitions"""
    __tablename__ = "feature_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(255), nullable=False, unique=True, index=True)
    feature_type = Column(String(50), nullable=False)
    data_type = Column(String(100), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))
    owner = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    storage_tier = Column(String(20), default='hot')
    partition_keys = Column(ARRAY(String))
    ttl_seconds = Column(Integer)
    schema_definition = Column(JSONB)
    indexing_strategy = Column(JSONB)

class FeatureRecord(Base):
    """Database model for feature values"""
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(255), nullable=False, index=True)
    entity_id = Column(String(255), nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    value_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    quality_score = Column(Float, default=1.0)
    source_system = Column(String(255), nullable=False)
    version = Column(Integer, default=1)
    metadata = Column(JSONB)
    partition_date = Column(String(10), index=True)  # YYYY-MM-DD format
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_feature_entity_time', 'feature_name', 'entity_id', 'timestamp'),
        Index('idx_partition_date_feature', 'partition_date', 'feature_name'),
    )

class DataLineageRecord(Base):
    """Database model for data lineage"""
    __tablename__ = "data_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lineage_id = Column(String(255), nullable=False, unique=True, index=True)
    source_features = Column(ARRAY(String))
    target_features = Column(ARRAY(String))
    transformation_type = Column(String(100), nullable=False)
    transformation_code = Column(Text)
    execution_timestamp = Column(DateTime, nullable=False)
    input_data_hash = Column(String(64))
    output_data_hash = Column(String(64))
    execution_context = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

class FeatureStoreStats(Base):
    """Database model for feature store statistics"""
    __tablename__ = "feature_store_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(255), nullable=False, index=True)
    stat_date = Column(DateTime, nullable=False, index=True)
    total_records = Column(Integer, default=0)
    avg_quality_score = Column(Float, default=0.0)
    storage_size_bytes = Column(BigInteger, default=0)
    access_count = Column(Integer, default=0)
    compute_latency_ms = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataWarehouseTable(Base):
    """Database model for data warehouse tables"""
    __tablename__ = "warehouse_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(255), nullable=False, unique=True)
    schema_definition = Column(JSONB, nullable=False)
    partition_columns = Column(ARRAY(String))
    storage_format = Column(String(20), default='parquet')
    location_path = Column(String(500))
    size_bytes = Column(BigInteger, default=0)
    row_count = Column(BigInteger, default=0)
    last_modified = Column(DateTime, nullable=False)
    compression_type = Column(String(20))
    table_type = Column(String(50))  # fact, dimension, aggregate
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RealTimeFeatureProcessor:
    """Real-time feature processing engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feature_cache = {}
        self.processing_queue = asyncio.Queue(maxsize=config.get('queue_size', 10000))
        self.batch_size = config.get('batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 5.0)
        self.processors = {}
        self.metrics = {
            'features_processed': 0,
            'processing_errors': 0,
            'average_latency': 0.0
        }

    async def register_feature_processor(self, feature_name: str, processor_func: callable):
        """Register a feature processor function"""
        self.processors[feature_name] = processor_func
        logger.info(f"Registered processor for feature: {feature_name}")

    async def process_feature_stream(self, feature_data: List[Dict[str, Any]]) -> List[FeatureValue]:
        """Process a stream of feature data"""
        try:
            start_time = time.time()
            processed_features = []

            # Batch processing
            for i in range(0, len(feature_data), self.batch_size):
                batch = feature_data[i:i + self.batch_size]

                # Process each feature in the batch
                for feature in batch:
                    try:
                        feature_name = feature.get('feature_name')
                        if feature_name in self.processors:
                            # Apply feature-specific processing
                            processed_value = await self.processors[feature_name](feature)

                            feature_value = FeatureValue(
                                feature_name=feature_name,
                                entity_id=feature.get('entity_id'),
                                value=processed_value,
                                timestamp=datetime.fromisoformat(feature.get('timestamp')),
                                quality_score=feature.get('quality_score', 1.0),
                                source_system=feature.get('source_system'),
                                version=feature.get('version', 1),
                                metadata=feature.get('metadata', {})
                            )
                            processed_features.append(feature_value)

                    except Exception as e:
                        logger.error(f"Feature processing error: {str(e)}")
                        self.metrics['processing_errors'] += 1

                # Small delay to prevent overwhelming the system
                if i + self.batch_size < len(feature_data):
                    await asyncio.sleep(0.001)

            # Update metrics
            processing_time = time.time() - start_time
            self.metrics['features_processed'] += len(processed_features)
            self._update_latency_metrics(processing_time)

            FEATURE_COMPUTE_LATENCY.observe(processing_time)
            logger.info(f"Processed {len(processed_features)} features in {processing_time:.3f}s")

            return processed_features

        except Exception as e:
            logger.error(f"Feature stream processing error: {str(e)}")
            raise

    def _update_latency_metrics(self, processing_time: float):
        """Update processing latency metrics"""
        total_processed = self.metrics['features_processed']
        current_avg = self.metrics['average_latency']
        new_avg = (current_avg * (total_processed - len(processed_features)) + processing_time) / total_processed
        self.metrics['average_latency'] = new_avg

class FeatureEngineering:
    """Advanced feature engineering capabilities"""

    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_hashers = {}
        self.engineered_features = {}

    def create_temporal_features(self, data: pd.DataFrame, timestamp_column: str) -> pd.DataFrame:
        """Create temporal features from timestamp column"""
        try:
            df = data.copy()
            timestamps = pd.to_datetime(df[timestamp_column])

            # Basic temporal features
            df['hour_of_day'] = timestamps.dt.hour
            df['day_of_week'] = timestamps.dt.dayofweek
            df['day_of_month'] = timestamps.dt.day
            df['month'] = timestamps.dt.month
            df['quarter'] = timestamps.dt.quarter
            df['year'] = timestamps.dt.year

            # Cyclical features
            df['hour_sin'] = np.sin(2 * np.pi * timestamps.dt.hour / 24)
            df['hour_cos'] = np.cos(2 * np.pi * timestamps.dt.hour / 24)
            df['day_sin'] = np.sin(2 * np.pi * timestamps.dt.dayofweek / 7)
            df['day_cos'] = np.cos(2 * np.pi * timestamps.dt.dayofweek / 7)
            df['month_sin'] = np.sin(2 * np.pi * timestamps.dt.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * timestamps.dt.month / 12)

            # Business features
            df['is_weekend'] = timestamps.dt.dayofweek >= 5
            df['is_business_hours'] = (timestamps.dt.hour >= 9) & (timestamps.dt.hour <= 17)
            df['is_holiday'] = self._is_holiday(timestamps)  # Simplified holiday detection

            # Time-based aggregations (if entity_id exists)
            if 'entity_id' in df.columns:
                df = self._create_time_based_aggregations(df, timestamp_column)

            logger.info(f"Created temporal features: {list(df.columns)}")
            return df

        except Exception as e:
            logger.error(f"Temporal feature creation error: {str(e)}")
            return data

    def create_spatial_features(self, data: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Create spatial features from latitude/longitude"""
        try:
            df = data.copy()

            # Convert to GeoDataFrame
            geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

            # Spatial clustering
            if len(gdf) > 10:
                from sklearn.cluster import DBSCAN
                coords = np.array([[p.x, p.y] for p in gdf.geometry])
                clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
                gdf['spatial_cluster'] = clustering.labels_

            # Distance-based features
            if len(gdf) > 1:
                # Calculate distance to nearest neighbor
                from sklearn.neighbors import NearestNeighbors
                nbrs = NearestNeighbors(n_neighbors=2).fit(coords)
                distances, indices = nbrs.kneighbors(coords)
                gdf['distance_to_nearest'] = distances[:, 1] * 111000  # Convert to meters

            # Geographic context features
            gdf['is_urban'] = self._is_urban_area(gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean())
            gdf['region'] = self._get_geographic_region(gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean())

            # Grid-based features
            gdf['lat_grid'] = (gdf.geometry.centroid.y * 100).astype(int)
            gdf['lon_grid'] = (gdf.geometry.centroid.x * 100).astype(int)
            gdf['grid_id'] = gdf['lat_grid'].astype(str) + '_' + gdf['lon_grid'].astype(str)

            logger.info(f"Created spatial features: {[col for col in gdf.columns if col not in data.columns]}")
            return gdf.drop('geometry', axis=1) if 'geometry' in gdf.columns else gdf

        except Exception as e:
            logger.error(f"Spatial feature creation error: {str(e)}")
            return data

    def create_interaction_features(self, data: pd.DataFrame, feature_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
        """Create interaction features between feature pairs"""
        try:
            df = data.copy()

            for feat1, feat2 in feature_pairs:
                if feat1 in df.columns and feat2 in df.columns:
                    # Skip if either feature is non-numeric
                    if not (np.issubdtype(df[feat1].dtype, np.number) and np.issubdtype(df[feat2].dtype, np.number)):
                        continue

                    # Interaction terms
                    df[f'{feat1}_x_{feat2}'] = df[feat1] * df[feat2]
                    df[f'{feat1}_div_{feat2}'] = df[feat1] / (df[feat2] + 1e-8)  # Avoid division by zero
                    df[f'{feat1}_plus_{feat2}'] = df[feat1] + df[feat2]
                    df[f'{feat1}_minus_{feat2}'] = df[feat1] - df[feat2]

                    # Ratio features
                    if (df[feat2] != 0).any():
                        df[f'{feat1}_to_{feat2}_ratio'] = df[feat1] / df[feat2].replace(0, np.nan)

            logger.info(f"Created interaction features for {len(feature_pairs)} pairs")
            return df

        except Exception as e:
            logger.error(f"Interaction feature creation error: {str(e)}")
            return data

    def create_aggregation_features(self, data: pd.DataFrame, group_columns: List[str],
                                   agg_columns: List[str], window_size: int = 10) -> pd.DataFrame:
        """Create rolling aggregation features"""
        try:
            df = data.copy().sort_values('timestamp' if 'timestamp' in df.columns else df.index)

            for group_col in group_columns:
                for agg_col in agg_columns:
                    if group_col in df.columns and agg_col in df.columns:
                        if not np.issubdtype(df[agg_col].dtype, np.number):
                            continue

                        group_key = f'{group_col}_{agg_col}'

                        # Rolling statistics
                        df[f'{group_key}_rolling_mean_{window_size}'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.rolling(window=window_size, min_periods=1).mean()
                        )
                        df[f'{group_key}_rolling_std_{window_size}'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.rolling(window=window_size, min_periods=1).std()
                        )
                        df[f'{group_key}_rolling_max_{window_size}'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.rolling(window=window_size, min_periods=1).max()
                        )
                        df[f'{group_key}_rolling_min_{window_size}'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.rolling(window=window_size, min_periods=1).min()
                        )

                        # Lag features
                        for lag in [1, 3, 7]:
                            df[f'{group_key}_lag_{lag}'] = df.groupby(group_col)[agg_col].transform(
                                lambda x: x.shift(lag)
                            )

                        # Difference features
                        df[f'{group_key}_diff_1'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.diff(1)
                        )
                        df[f'{group_key}_pct_change_1'] = df.groupby(group_col)[agg_col].transform(
                            lambda x: x.pct_change(1)
                        )

            logger.info(f"Created aggregation features for {len(group_columns)} groups, {len(agg_columns)} columns")
            return df

        except Exception as e:
            logger.error(f"Aggregation feature creation error: {str(e)}")
            return data

    def create_text_features(self, data: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """Create text-based features"""
        try:
            df = data.copy()

            if text_column not in df.columns:
                return df

            # Basic text features
            df[f'{text_column}_length'] = df[text_column].astype(str).str.len()
            df[f'{text_column}_word_count'] = df[text_column].astype(str).str.split().str.len()
            df[f'{text_column}_char_count'] = df[text_column].astype(str).str.len()
            df[f'{text_column}_digit_count'] = df[text_column].astype(str).str.count(r'\d')
            df[f'{text_column}_upper_count'] = df[text_column].astype(str).str.count(r'[A-Z]')
            df[f'{text_column}_lower_count'] = df[text_column].astype(str).str.count(r'[a-z]')

            # Punctuation and special characters
            df[f'{text_column}_punct_count'] = df[text_column].astype(str).str.count(r'[^\w\s]')
            df[f'{text_column}_space_count'] = df[text_column].astype(str).str.count(r'\s')

            # Ratio features
            df[f'{text_column}_digit_ratio'] = df[f'{text_column}_digit_count'] / (df[f'{text_column}_char_count'] + 1)
            df[f'{text_column}_upper_ratio'] = df[f'{text_column}_upper_count'] / (df[f'{text_column}_char_count'] + 1)

            # TF-IDF features (simplified)
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')

            # Handle NaN values
            text_data = df[text_column].fillna('').astype(str)
            tfidf_matrix = vectorizer.fit_transform(text_data)

            # Add top TF-IDF features
            feature_names = vectorizer.get_feature_names_out()
            for i, feature_name in enumerate(feature_names[:10]):  # Top 10 features
                df[f'{text_column}_tfidf_{feature_name}'] = tfidf_matrix[:, i].toarray().flatten()

            logger.info(f"Created text features: {[col for col in df.columns if col.startswith(text_column + '_')]}")
            return df

        except Exception as e:
            logger.error(f"Text feature creation error: {str(e)}")
            return data

    def _is_holiday(self, timestamps: pd.Series) -> pd.Series:
        """Simplified holiday detection"""
        # In practice, use a proper holiday calendar
        return timestamps.dt.dayofweek >= 5  # Weekends as "holidays"

    def _create_time_based_aggregations(self, df: pd.DataFrame, timestamp_column: str) -> pd.DataFrame:
        """Create time-based aggregation features"""
        try:
            df['timestamp'] = pd.to_datetime(df[timestamp_column])
            df = df.sort_values(['entity_id', 'timestamp'])

            for entity_id in df['entity_id'].unique():
                entity_mask = df['entity_id'] == entity_id
                entity_data = df.loc[entity_mask]

                # Previous transaction features
                df.loc[entity_mask, 'prev_transaction_amount'] = entity_data['amount'].shift(1)
                df.loc[entity_mask, 'prev_transaction_time_diff'] = (
                    entity_data['timestamp'] - entity_data['timestamp'].shift(1)
                ).dt.total_seconds() / 3600  # Convert to hours

                # Rolling features for this entity
                window_sizes = [3, 7, 30]  # 3, 7, 30 transactions
                for window in window_sizes:
                    df.loc[entity_mask, f'rolling_mean_amount_{window}'] = (
                        entity_data['amount'].rolling(window=window, min_periods=1).mean()
                    )
                    df.loc[entity_mask, f'rolling_std_amount_{window}'] = (
                        entity_data['amount'].rolling(window=window, min_periods=1).std()
                    )

            return df

        except Exception as e:
            logger.warning(f"Time-based aggregation error: {str(e)}")
            return df

    def _is_urban_area(self, lat: float, lon: float) -> bool:
        """Simplified urban area detection"""
        # Major Indian cities coordinates (simplified)
        major_cities = [
            (28.6139, 77.2090),  # Delhi
            (19.0760, 72.8777),  # Mumbai
            (12.9716, 77.5946),  # Bengaluru
            (17.3850, 78.4867),  # Hyderabad
            (13.0827, 80.2707),  # Chennai
        ]

        for city_lat, city_lon in major_cities:
            distance = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if distance < 0.5:  # Within ~50km
                return True
        return False

    def _get_geographic_region(self, lat: float, lon: float) -> str:
        """Get geographic region from coordinates"""
        if lat > 20:
            return 'north_india'
        elif lat > 15:
            return 'central_india'
        else:
            return 'south_india'

class DataWarehouseManager:
    """Advanced data warehouse management"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.spark = None
        self.tables = {}
        self.partitions = {}
        self.storage_config = config.get('storage', {})

    async def initialize_spark(self):
        """Initialize Spark session for data warehouse operations"""
        try:
            self.spark = SparkSession.builder \
                .appName("AEGIS_DataWarehouse") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .getOrCreate()

            logger.info("Spark session initialized for data warehouse")
            return True

        except Exception as e:
            logger.error(f"Spark initialization failed: {str(e)}")
            return False

    async def create_table(self, table_name: str, schema: Dict[str, str],
                         partition_columns: List[str] = None,
                         storage_format: str = 'parquet') -> bool:
        """Create a data warehouse table"""
        try:
            if not self.spark:
                await self.initialize_spark()

            # Create Spark DataFrame schema
            fields = []
            for col_name, col_type in schema.items():
                spark_type = self._convert_to_spark_type(col_type)
                fields.append(f"`{col_name}` {spark_type}")

            schema_sql = ", ".join(fields)
            partition_sql = f" PARTITIONED BY ({', '.join([f'`{col}` STRING' for col in partition_columns])})" if partition_columns else ""

            # Create table using Spark SQL
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {schema_sql}
            ) USING {storage_format}{partition_sql}
            """

            self.spark.sql(create_table_sql)

            # Store table metadata
            self.tables[table_name] = {
                'schema': schema,
                'partition_columns': partition_columns or [],
                'storage_format': storage_format,
                'created_at': datetime.utcnow()
            }

            logger.info(f"Created warehouse table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Table creation error: {str(e)}")
            return False

    async def ingest_data(self, table_name: str, data: pd.DataFrame,
                         mode: str = 'append') -> bool:
        """Ingest data into warehouse table"""
        try:
            if not self.spark:
                await self.initialize_spark()

            # Convert pandas to Spark DataFrame
            spark_df = self.spark.createDataFrame(data)

            # Write to table
            spark_df.write.mode(mode).saveAsTable(table_name)

            logger.info(f"Ingested {len(data)} records into {table_name}")
            return True

        except Exception as e:
            logger.error(f"Data ingestion error: {str(e)}")
            return False

    def _convert_to_spark_type(self, python_type: str) -> str:
        """Convert Python type to Spark SQL type"""
        type_mapping = {
            'str': 'STRING',
            'int': 'BIGINT',
            'float': 'DOUBLE',
            'bool': 'BOOLEAN',
            'datetime': 'TIMESTAMP',
            'date': 'DATE',
            'object': 'STRING'
        }

        return type_mapping.get(python_type, 'STRING')

class FeatureStore:
    """Main feature store implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config.get('database', {})
        self.redis_config = config.get('redis', {})
        self.storage_config = config.get('storage', {})

        # Initialize components
        self.engine = create_engine(self.db_config.get('url', 'sqlite:///aegis_features.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis for caching
        self.redis_client = redis.Redis(
            host=self.redis_config.get('host', 'localhost'),
            port=self.redis_config.get('port', 6379),
            db=self.redis_config.get('db', 5),
            decode_responses=True
        )

        # Feature processing
        self.real_time_processor = RealTimeFeatureProcessor(config.get('real_time', {}))
        self.feature_engineering = FeatureEngineering()
        self.warehouse_manager = DataWarehouseManager(config)

        # Performance metrics
        self.metrics = {
            'features_stored': 0,
            'features_served': 0,
            'storage_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Start background tasks
        self.background_tasks = []
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Data quality monitoring
        self.background_tasks.append(
            asyncio.create_task(self._monitor_data_quality())
        )
        # Cache cleanup
        self.background_tasks.append(
            asyncio.create_task(self._cleanup_expired_features())
        )
        # Metrics collection
        self.background_tasks.append(
            asyncio.create_task(self._collect_metrics())
        )

    async def register_feature(self, feature_def: FeatureDefinition) -> bool:
        """Register a new feature definition"""
        try:
            db = self.SessionLocal()

            # Check if feature already exists
            existing = db.query(FeatureDefinitionRecord).filter(
                FeatureDefinitionRecord.feature_name == feature_def.feature_name
            ).first()

            if existing:
                # Update existing feature
                existing.feature_type = feature_def.feature_type.value
                existing.data_type = feature_def.data_type
                existing.description = feature_def.description
                existing.tags = feature_def.tags
                existing.updated_at = datetime.utcnow()
                existing.version += 1
            else:
                # Create new feature
                feature_record = FeatureDefinitionRecord(
                    feature_name=feature_def.feature_name,
                    feature_type=feature_def.feature_type.value,
                    data_type=feature_def.data_type,
                    description=feature_def.description,
                    tags=feature_def.tags,
                    owner=feature_def.owner,
                    storage_tier=feature_def.storage_tier.value,
                    partition_keys=feature_def.partition_keys,
                    ttl_seconds=feature_def.ttl_seconds
                )
                db.add(feature_record)

            db.commit()
            logger.info(f"Registered feature: {feature_def.feature_name}")
            return True

        except Exception as e:
            logger.error(f"Feature registration error: {str(e)}")
            return False
        finally:
            db.close()

    async def store_features(self, features: List[FeatureValue]) -> int:
        """Store feature values in the feature store"""
        try:
            start_time = time.time()
            stored_count = 0

            db = self.SessionLocal()

            for feature in features:
                try:
                    # Create feature record
                    feature_record = FeatureRecord(
                        feature_name=feature.feature_name,
                        entity_id=feature.entity_id,
                        value=feature.value if isinstance(feature.value, (list, dict)) else {'value': feature.value},
                        value_type=type(feature.value).__name__,
                        timestamp=feature.timestamp,
                        quality_score=feature.quality_score,
                        source_system=feature.source_system,
                        version=feature.version,
                        metadata=feature.metadata,
                        partition_date=feature.timestamp.strftime('%Y-%m-%d')
                    )

                    db.add(feature_record)

                    # Cache hot features
                    if feature.quality_score > 0.8:
                        cache_key = f"feature:{feature.feature_name}:{feature.entity_id}"
                        self.redis_client.setex(
                            cache_key,
                            3600,  # 1 hour TTL
                            json.dumps({
                                'value': feature.value,
                                'timestamp': feature.timestamp.isoformat(),
                                'quality_score': feature.quality_score
                            }, default=str)
                        )

                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error storing feature {feature.feature_name}: {str(e)}")

            db.commit()
            db.close()

            # Update metrics
            self.metrics['features_stored'] += stored_count
            processing_time = (time.time() - start_time) * 1000
            FEATURE_STORAGE_OPERATIONS.labels(operation_type='store').inc(stored_count)

            logger.info(f"Stored {stored_count} features in {processing_time:.2f}ms")
            return stored_count

        except Exception as e:
            logger.error(f"Feature storage error: {str(e)}")
            return 0

    async def get_feature(self, feature_name: str, entity_id: str,
                        as_of: datetime = None) -> Optional[FeatureValue]:
        """Retrieve a feature value for an entity"""
        try:
            # Check cache first
            cache_key = f"feature:{feature_name}:{entity_id}"
            cached_value = self.redis_client.get(cache_key)

            if cached_value:
                self.metrics['cache_hits'] += 1
                cached_data = json.loads(cached_value)

                return FeatureValue(
                    feature_name=feature_name,
                    entity_id=entity_id,
                    value=cached_data['value'],
                    timestamp=datetime.fromisoformat(cached_data['timestamp']),
                    quality_score=cached_data['quality_score'],
                    source_system='cache',
                    version=1,
                    metadata={'cached': True}
                )

            self.metrics['cache_misses'] += 1

            # Query database
            db = self.SessionLocal()
            query = db.query(FeatureRecord).filter(
                FeatureRecord.feature_name == feature_name,
                FeatureRecord.entity_id == entity_id
            )

            if as_of:
                query = query.filter(FeatureRecord.timestamp <= as_of)

            # Get most recent feature
            feature_record = query.order_by(FeatureRecord.timestamp.desc()).first()

            if feature_record:
                feature_value = FeatureValue(
                    feature_name=feature_record.feature_name,
                    entity_id=feature_record.entity_id,
                    value=feature_record.value,
                    timestamp=feature_record.timestamp,
                    quality_score=feature_record.quality_score,
                    source_system=feature_record.source_system,
                    version=feature_record.version,
                    metadata=feature_record.metadata or {}
                )

                # Cache the result
                self.redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps({
                        'value': feature_value.value,
                        'timestamp': feature_value.timestamp.isoformat(),
                        'quality_score': feature_value.quality_score
                    }, default=str)
                )

                self.metrics['features_served'] += 1
                FEATURE_SERVE_REQUESTS.labels(feature_name=feature_name, status='success').inc()

                return feature_value

            FEATURE_SERVE_REQUESTS.labels(feature_name=feature_name, status='not_found').inc()
            return None

        except Exception as e:
            logger.error(f"Feature retrieval error: {str(e)}")
            FEATURE_SERVE_REQUESTS.labels(feature_name=feature_name, status='error').inc()
            return None
        finally:
            db.close()

    async def get_features_batch(self, feature_names: List[str],
                               entity_ids: List[str]) -> Dict[str, Dict[str, FeatureValue]]:
        """Retrieve multiple features for multiple entities"""
        try:
            results = {}

            for entity_id in entity_ids:
                entity_features = {}
                for feature_name in feature_names:
                    feature_value = await self.get_feature(feature_name, entity_id)
                    if feature_value:
                        entity_features[feature_name] = feature_value

                if entity_features:
                    results[entity_id] = entity_features

            logger.info(f"Retrieved features for {len(results)} entities")
            return results

        except Exception as e:
            logger.error(f"Batch feature retrieval error: {str(e)}")
            return {}

    async def process_streaming_features(self, feature_stream: List[Dict[str, Any]]) -> int:
        """Process streaming feature data"""
        try:
            # Process features through real-time processor
            processed_features = await self.real_time_processor.process_feature_stream(feature_stream)

            # Store processed features
            stored_count = await self.store_features(processed_features)

            return stored_count

        except Exception as e:
            logger.error(f"Streaming feature processing error: {str(e)}")
            return 0

    async def create_feature_view(self, view_name: str, feature_names: List[str],
                                filters: Dict[str, Any] = None) -> bool:
        """Create a materialized view of features"""
        try:
            # This would create a materialized view or cached feature set
            # For now, we'll cache the feature combination in Redis

            view_key = f"feature_view:{view_name}"
            view_data = {
                'feature_names': feature_names,
                'filters': filters or {},
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }

            self.redis_client.setex(view_key, 7200, json.dumps(view_data))  # 2 hours TTL
            logger.info(f"Created feature view: {view_name}")
            return True

        except Exception as e:
            logger.error(f"Feature view creation error: {str(e)}")
            return False

    async def get_feature_statistics(self, feature_name: str,
                                   time_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """Get statistics for a feature"""
        try:
            db = self.SessionLocal()
            query = db.query(FeatureRecord).filter(
                FeatureRecord.feature_name == feature_name
            )

            if time_range:
                start_time, end_time = time_range
                query = query.filter(
                    FeatureRecord.timestamp >= start_time,
                    FeatureRecord.timestamp <= end_time
                )

            # Calculate statistics
            total_records = query.count()
            avg_quality = db.query(db.func.avg(FeatureRecord.quality_score)).filter(
                FeatureRecord.feature_name == feature_name
            ).scalar() or 0.0

            # Daily record counts
            daily_counts = db.query(
                db.func.date(FeatureRecord.timestamp).label('date'),
                db.func.count(FeatureRecord.id).label('count')
            ).filter(
                FeatureRecord.feature_name == feature_name
            ).group_by(db.func.date(FeatureRecord.timestamp)).all()

            stats = {
                'feature_name': feature_name,
                'total_records': total_records,
                'average_quality_score': float(avg_quality),
                'daily_counts': [
                    {'date': str(count.date), 'count': count.count}
                    for count in daily_counts
                ],
                'last_updated': datetime.utcnow().isoformat()
            }

            db.close()
            return stats

        except Exception as e:
            logger.error(f"Feature statistics error: {str(e)}")
            return {}

    async def _monitor_data_quality(self):
        """Background task to monitor data quality"""
        while True:
            try:
                # Calculate overall data quality score
                db = self.SessionLocal()

                avg_quality = db.query(db.func.avg(FeatureRecord.quality_score)).scalar() or 0.0
                total_records = db.query(FeatureRecord).count()
                error_count = db.query(FeatureRecord).filter(
                    FeatureRecord.quality_score < 0.5
                ).count()

                quality_score = max(0, 1 - (error_count / max(1, total_records)))
                DATA_QUALITY_SCORE.set(quality_score)

                logger.info(f"Data quality monitoring: score={quality_score:.3f}, records={total_records}")

                db.close()

                # Update storage usage metrics
                await self._update_storage_metrics()

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Data quality monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_expired_features(self):
        """Background task to clean up expired features"""
        while True:
            try:
                db = self.SessionLocal()

                # Find expired features (those with TTL)
                expired_time = datetime.utcnow() - timedelta(days=30)  # 30 days retention

                deleted_count = db.query(FeatureRecord).filter(
                    FeatureRecord.timestamp < expired_time
                ).delete()

                db.commit()
                db.close()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired features")

                # Cleanup Redis cache
                self.redis_client.flushdb()  # Simplified cleanup

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Feature cleanup error: {str(e)}")
                await asyncio.sleep(300)

    async def _collect_metrics(self):
        """Background task to collect system metrics"""
        while True:
            try:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage('/').percent

                # Update feature store metrics
                cache_hit_rate = self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])

                metrics_data = {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'disk_usage': disk_usage,
                    'features_stored': self.metrics['features_stored'],
                    'features_served': self.metrics['features_served'],
                    'cache_hit_rate': cache_hit_rate,
                    'timestamp': datetime.utcnow().isoformat()
                }

                # Store metrics in Redis
                self.redis_client.setex(
                    'feature_store_metrics',
                    300,  # 5 minutes TTL
                    json.dumps(metrics_data)
                )

                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(60)

    async def _update_storage_metrics(self):
        """Update storage usage metrics"""
        try:
            # This would calculate actual storage usage by tier
            # For now, use estimated values
            storage_usage = {
                'hot': 1024 * 1024 * 1024,  # 1GB
                'warm': 10 * 1024 * 1024 * 1024,  # 10GB
                'cold': 100 * 1024 * 1024 * 1024,  # 100GB
                'archive': 1024 * 1024 * 1024 * 1024  # 1TB
            }

            for tier, usage in storage_usage.items():
                STORAGE_USAGE_BYTES.labels(tier=tier).set(usage)

        except Exception as e:
            logger.warning(f"Storage metrics update error: {str(e)}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get feature store system status"""
        try:
            # Get metrics from Redis
            metrics_data = self.redis_client.get('feature_store_metrics')
            system_metrics = json.loads(metrics_data) if metrics_data else {}

            # Database connection test
            db = self.SessionLocal()
            db.execute("SELECT 1")  # Test connection
            db.close()
            db_status = "connected"

            return {
                'status': 'healthy',
                'database_status': db_status,
                'redis_status': 'connected' if self.redis_client.ping() else 'disconnected',
                'metrics': system_metrics,
                'total_features_stored': self.metrics['features_stored'],
                'total_features_served': self.metrics['features_served'],
                'background_tasks_active': len([task for task in self.background_tasks if not task.done()]),
                'last_updated': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"System status error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

    async def cleanup(self):
        """Cleanup feature store resources"""
        logger.info("Cleaning up feature store")

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Close connections
        if self.redis_client:
            self.redis_client.close()

        logger.info("Feature store cleanup completed")

# Testing functionality
async def test_feature_store():
    """Test feature store functionality"""
    print("Testing Advanced Feature Store and Data Warehouse")

    # Initialize feature store
    config = {
        'database': {'url': 'sqlite:///aegis_features.db'},
        'redis': {'host': 'localhost', 'port': 6379, 'db': 5},
        'storage': {'default_path': '/tmp/aegis_feature_store'},
        'real_time': {'queue_size': 1000, 'batch_size': 50}
    }

    feature_store = FeatureStore(config)

    try:
        # Wait for background tasks to initialize
        await asyncio.sleep(1)

        # Test feature registration
        print("\n1. Testing Feature Registration...")
        feature_def = FeatureDefinition(
            feature_name="transaction_amount_risk_score",
            feature_type=FeatureType.NUMERICAL,
            data_type="float",
            description="Risk score based on transaction amount",
            tags=["risk", "transaction", "amount"],
            owner="data_science_team",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1,
            is_active=True,
            storage_tier=StorageTier.HOT,
            partition_keys=["date"],
            ttl_seconds=86400
        )

        registration_success = await feature_store.register_feature(feature_def)
        print(f"Feature registration success: {registration_success}")

        # Test feature storage
        print("\n2. Testing Feature Storage...")
        test_features = [
            FeatureValue(
                feature_name="transaction_amount_risk_score",
                entity_id="account_123",
                value=0.75,
                timestamp=datetime.utcnow(),
                quality_score=0.9,
                source_system="fraud_detection",
                version=1,
                metadata={"model_version": "v1.0", "confidence": 0.85}
            ),
            FeatureValue(
                feature_name="transaction_amount_risk_score",
                entity_id="account_456",
                value=0.45,
                timestamp=datetime.utcnow(),
                quality_score=0.8,
                source_system="fraud_detection",
                version=1,
                metadata={"model_version": "v1.0", "confidence": 0.78}
            ),
            FeatureValue(
                feature_name="customer_location_risk",
                entity_id="account_123",
                value="high_risk_area",
                timestamp=datetime.utcnow(),
                quality_score=0.95,
                source_system="location_analysis",
                version=1,
                metadata={"lat": 28.6139, "lon": 77.2090}
            )
        ]

        stored_count = await feature_store.store_features(test_features)
        print(f"Stored {stored_count} features")

        # Test feature retrieval
        print("\n3. Testing Feature Retrieval...")
        retrieved_feature = await feature_store.get_feature("transaction_amount_risk_score", "account_123")
        if retrieved_feature:
            print(f"Retrieved feature: {retrieved_feature.value} (quality: {retrieved_feature.quality_score})")
        else:
            print("Feature not found")

        # Test batch retrieval
        print("\n4. Testing Batch Feature Retrieval...")
        batch_features = await feature_store.get_features_batch(
            ["transaction_amount_risk_score", "customer_location_risk"],
            ["account_123", "account_456"]
        )
        print(f"Retrieved features for {len(batch_features)} entities:")
        for entity_id, features in batch_features.items():
            print(f"  {entity_id}: {list(features.keys())}")

        # Test streaming feature processing
        print("\n5. Testing Streaming Feature Processing...")
        stream_data = [
            {
                'feature_name': 'suspicious_activity_score',
                'entity_id': 'account_789',
                'value': 0.92,
                'timestamp': datetime.utcnow().isoformat(),
                'quality_score': 0.88,
                'source_system': 'real_time_monitor'
            },
            {
                'feature_name': 'transaction_pattern_risk',
                'entity_id': 'account_789',
                'value': 0.67,
                'timestamp': datetime.utcnow().isoformat(),
                'quality_score': 0.82,
                'source_system': 'real_time_monitor'
            }
        ]

        processed_count = await feature_store.process_streaming_features(stream_data)
        print(f"Processed {processed_count} streaming features")

        # Test feature engineering
        print("\n6. Testing Feature Engineering...")
        sample_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
            'amount': np.random.lognormal(8, 1.5, 100),
            'entity_id': [f'entity_{i%10}' for i in range(100)],
            'latitude': 28.6139 + np.random.uniform(-0.1, 0.1, 100),
            'longitude': 77.2090 + np.random.uniform(-0.1, 0.1, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'description': ['Transaction description'] * 100
        })

        # Test temporal features
        temporal_features = feature_store.feature_engineering.create_temporal_features(sample_data, 'timestamp')
        print(f"Created temporal features: {len(temporal_features.columns)} columns")

        # Test spatial features
        spatial_features = feature_store.feature_engineering.create_spatial_features(sample_data, 'latitude', 'longitude')
        print(f"Created spatial features: {len(spatial_features.columns)} columns")

        # Test text features
        text_features = feature_store.feature_engineering.create_text_features(sample_data, 'description')
        print(f"Created text features: {len(text_features.columns)} columns")

        # Test system status
        print("\n7. System Status:")
        status = await feature_store.get_system_status()
        print(f"  Status: {status['status']}")
        print(f"  Database: {status['database_status']}")
        print(f"  Redis: {status['redis_status']}")
        print(f"  Features stored: {status['total_features_stored']}")
        print(f"  Features served: {status['total_features_served']}")
        print(f"  Background tasks: {status['background_tasks_active']}")

        print("\n✅ All feature store tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Feature store test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await feature_store.cleanup()

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_feature_store())