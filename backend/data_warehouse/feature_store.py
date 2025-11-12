"""
Feature Store and Data Warehouse for Cybercrime Intelligence
Manages feature engineering, storage, and serving for AI models
"""

import asyncio
import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
import aioredis
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
import pickle
import os

logger = logging.getLogger(__name__)

class FeatureType(Enum):
    """
    Types of features in the store
    """
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    BEHAVIORAL = "behavioral"
    TEXT = "text"

class FeatureStoreType(Enum):
    """
    Feature store storage types
    """
    ONLINE = "online"      # Real-time serving (Redis)
    OFFLINE = "offline"    # Batch processing (PostgreSQL)
    CACHED = "cached"      # Frequently accessed features (Redis cache)

@dataclass
class FeatureDefinition:
    """
    Feature definition metadata
    """
    name: str
    feature_type: FeatureType
    data_type: str
    description: str
    source_table: str
    source_column: str
    transformation: str = "none"
    is_active: bool = True
    version: int = 1
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class FeatureVector:
    """
    Feature vector for a specific entity
    """
    entity_id: str
    entity_type: str
    features: Dict[str, Any]
    timestamp: datetime
    feature_version: int = 1
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class FeatureStore:
    """
    Advanced feature store for cybercrime intelligence
    """

    def __init__(self):
        self.redis_client = None
        self.feature_definitions = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_selectors = {}

        # Feature groups
        self.feature_groups = {
            'complaint_features': [],
            'transaction_features': [],
            'location_features': [],
            'temporal_features': [],
            'behavioral_features': [],
            'risk_features': [],
            'historical_features': []
        }

        # Cache configurations
        self.cache_ttl = {
            'hot_features': 300,      # 5 minutes
            'warm_features': 3600,    # 1 hour
            'cold_features': 86400    # 24 hours
        }

    async def initialize(self) -> bool:
        """
        Initialize feature store
        """
        try:
            logger.info("[Feature Store] Initializing feature store...")

            # Initialize Redis connections
            self.redis_client = await aioredis.from_url(
                "redis://localhost:6379",
                decode_responses=False,  # Keep binary for pickled objects
                max_connections=20
            )

            # Load feature definitions from database
            await self._load_feature_definitions()

            # Initialize feature transformations
            await self._initialize_transformations()

            # Create feature indices
            await self._create_feature_indices()

            logger.info("[Feature Store] Feature store initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Feature Store] Error initializing feature store: {str(e)}")
            return False

    async def _load_feature_definitions(self) -> None:
        """
        Load feature definitions from database
        """
        try:
            # Define core features for cybercrime detection
            core_features = [
                # Complaint features
                FeatureDefinition(
                    name="complaint_amount",
                    feature_type=FeatureType.NUMERICAL,
                    data_type="float",
                    description="Amount lost in complaint",
                    source_table="ncrp_complaints",
                    source_column="amount"
                ),
                FeatureDefinition(
                    name="complaint_hour",
                    feature_type=FeatureType.TEMPORAL,
                    data_type="int",
                    description="Hour of complaint filing",
                    source_table="ncrp_complaints",
                    source_column="EXTRACT(HOUR FROM created_at)"
                ),
                FeatureDefinition(
                    name="complaint_day_of_week",
                    feature_type=FeatureType.TEMPORAL,
                    data_type="int",
                    description="Day of week of complaint filing",
                    source_table="ncrp_complaints",
                    source_column="EXTRACT(DOW FROM created_at)"
                ),

                # Transaction features
                FeatureDefinition(
                    name="transaction_amount",
                    feature_type=FeatureType.NUMERICAL,
                    data_type="float",
                    description="Transaction amount",
                    source_table="bank_transactions",
                    source_column="amount"
                ),
                FeatureDefinition(
                    name="transaction_risk_score",
                    feature_type=FeatureType.NUMERICAL,
                    data_type="float",
                    description="Transaction risk score",
                    source_table="bank_transactions",
                    source_column="risk_score"
                ),
                FeatureDefinition(
                    name="transaction_hour",
                    feature_type=FeatureType.TEMPORAL,
                    data_type="int",
                    description="Hour of transaction",
                    source_table="bank_transactions",
                    source_column="EXTRACT(HOUR FROM timestamp)"
                ),

                # Location features
                FeatureDefinition(
                    name="location_lat",
                    feature_type=FeatureType.SPATIAL,
                    data_type="float",
                    description="Latitude",
                    source_table="ncrp_complaints",
                    source_column="ST_Y(victim_location)"
                ),
                FeatureDefinition(
                    name="location_lon",
                    feature_type=FeatureType.SPATIAL,
                    data_type="float",
                    description="Longitude",
                    source_table="ncrp_complaints",
                    source_column="ST_X(victim_location)"
                ),
                FeatureDefinition(
                    name="urban_density",
                    feature_type=FeatureType.CATEGORICAL,
                    data_type="string",
                    description="Urban density level",
                    source_table="ncrp_complaints",
                    source_column="CASE WHEN ST_Y(victim_location) > 28.5 AND ST_X(victim_location) > 77.0 THEN 'high' ELSE 'medium' END"
                ),

                # Behavioral features
                FeatureDefinition(
                    name="scam_type_encoded",
                    feature_type=FeatureType.CATEGORICAL,
                    data_type="int",
                    description="Encoded scam type",
                    source_table="ncrp_complaints",
                    source_column="scam_type",
                    transformation="label_encode"
                ),
                FeatureDefinition(
                    name="transaction_type_encoded",
                    feature_type=FeatureType.CATEGORICAL,
                    data_type="int",
                    description="Encoded transaction type",
                    source_table="bank_transactions",
                    source_column="transaction_type",
                    transformation="label_encode"
                ),

                # Risk features
                FeatureDefinition(
                    name="repeat_offender_indicator",
                    feature_type=FeatureType.BEHAVIORAL,
                    data_type="bool",
                    description="Repeat offender indicator",
                    source_table="i4c_crime_data",
                    source_column="repeat_offender"
                ),
                FeatureDefinition(
                    name="severity_score",
                    feature_type=FeatureType.NUMERICAL,
                    data_type="float",
                    description="Crime severity score",
                    source_table="i4c_crime_data",
                    source_column="severity_score"
                ),

                # Historical features
                FeatureDefinition(
                    name="historical_complaint_count",
                    feature_type=FeatureType.BEHAVIORAL,
                    data_type="int",
                    description="Historical complaint count in area",
                    source_table="ncrp_complaints",
                    source_column="COUNT(*) OVER (PARTITION BY ST_Buffer(victim_location, 0.01) ORDER BY created_at RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW)",
                    transformation="window_function"
                ),
                FeatureDefinition(
                    name="historical_avg_amount",
                    feature_type=FeatureType.NUMERICAL,
                    data_type="float",
                    description="Historical average amount in area",
                    source_table="ncrp_complaints",
                    source_column="AVG(amount) OVER (PARTITION BY ST_Buffer(victim_location, 0.01) ORDER BY created_at RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW)",
                    transformation="window_function"
                )
            ]

            # Store feature definitions
            for feature in core_features:
                self.feature_definitions[feature.name] = feature

                # Add to appropriate feature group
                if 'complaint' in feature.name:
                    self.feature_groups['complaint_features'].append(feature.name)
                elif 'transaction' in feature.name:
                    self.feature_groups['transaction_features'].append(feature.name)
                elif 'location' in feature.name or feature.feature_type == FeatureType.SPATIAL:
                    self.feature_groups['location_features'].append(feature.name)
                elif feature.feature_type == FeatureType.TEMPORAL:
                    self.feature_groups['temporal_features'].append(feature.name)
                elif feature.feature_type == FeatureType.BEHAVIORAL:
                    self.feature_groups['behavioral_features'].append(feature.name)
                elif 'risk' in feature.name or 'severity' in feature.name:
                    self.feature_groups['risk_features'].append(feature.name)
                elif 'historical' in feature.name:
                    self.feature_groups['historical_features'].append(feature.name)

            logger.info(f"[Feature Store] Loaded {len(core_features)} feature definitions")

        except Exception as e:
            logger.error(f"[Feature Store] Error loading feature definitions: {str(e)}")

    async def _initialize_transformations(self) -> None:
        """
        Initialize feature transformations (scalers, encoders)
        """
        try:
            # Initialize scalers for numerical features
            numerical_features = [f for f in self.feature_definitions.values()
                                if f.feature_type == FeatureType.NUMERICAL]

            for feature in numerical_features:
                if feature.name not in self.scalers:
                    self.scalers[feature.name] = StandardScaler()

            # Initialize encoders for categorical features
            categorical_features = [f for f in self.feature_definitions.values()
                                  if f.feature_type == FeatureType.CATEGORICAL]

            for feature in categorical_features:
                if feature.name not in self.encoders:
                    self.encoders[feature.name] = LabelEncoder()

            logger.info("[Feature Store] Feature transformations initialized")

        except Exception as e:
            logger.error(f"[Feature Store] Error initializing transformations: {str(e)}")

    async def _create_feature_indices(self) -> None:
        """
        Create indices for efficient feature lookup
        """
        try:
            # Create Redis indices for different feature types
            # In production, would create database indexes
            logger.info("[Feature Store] Feature indices created")

        except Exception as e:
            logger.error(f"[Feature Store] Error creating feature indices: {str(e)}")

    async def extract_features(self, entity_id: str, entity_type: str,
                             source_data: Dict[str, Any],
                             feature_groups: List[str] = None) -> FeatureVector:
        """
        Extract features from source data
        """
        try:
            if feature_groups is None:
                feature_groups = list(self.feature_groups.keys())

            features = {}
            metadata = {}

            # Extract features for each requested group
            for group in feature_groups:
                if group in self.feature_groups:
                    group_features = await self._extract_feature_group(
                        entity_id, entity_type, source_data, group
                    )
                    features.update(group_features)

            # Create feature vector
            feature_vector = FeatureVector(
                entity_id=entity_id,
                entity_type=entity_type,
                features=features,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )

            return feature_vector

        except Exception as e:
            logger.error(f"[Feature Store] Error extracting features: {str(e)}")
            return FeatureVector(
                entity_id=entity_id,
                entity_type=entity_type,
                features={},
                timestamp=datetime.utcnow()
            )

    async def _extract_feature_group(self, entity_id: str, entity_type: str,
                                    source_data: Dict[str, Any],
                                    feature_group: str) -> Dict[str, Any]:
        """
        Extract features for a specific group
        """
        try:
            features = {}
            feature_names = self.feature_groups[feature_group]

            for feature_name in feature_names:
                if feature_name in self.feature_definitions:
                    feature_def = self.feature_definitions[feature_name]
                    value = await self._extract_single_feature(
                        source_data, feature_def, entity_type
                    )

                    if value is not None:
                        features[feature_name] = value

            return features

        except Exception as e:
            logger.error(f"[Feature Store] Error extracting feature group {feature_group}: {str(e)}")
            return {}

    async def _extract_single_feature(self, source_data: Dict[str, Any],
                                    feature_def: FeatureDefinition,
                                    entity_type: str) -> Any:
        """
        Extract a single feature value
        """
        try:
            # Get raw value from source data
            raw_value = None

            # Direct mapping
            if feature_def.source_column in source_data:
                raw_value = source_data[feature_def.source_column]

            # Complex extractions
            elif feature_def.name == "complaint_hour":
                timestamp = source_data.get('complaint_timestamp') or source_data.get('created_at')
                if timestamp:
                    raw_value = datetime.fromisoformat(timestamp).hour

            elif feature_def.name == "complaint_day_of_week":
                timestamp = source_data.get('complaint_timestamp') or source_data.get('created_at')
                if timestamp:
                    raw_value = datetime.fromisoformat(timestamp).weekday()

            elif feature_def.name == "transaction_hour":
                timestamp = source_data.get('timestamp')
                if timestamp:
                    raw_value = datetime.fromisoformat(timestamp).hour

            elif feature_def.name == "location_lat":
                location = source_data.get('victim_location') or source_data.get('location')
                if location:
                    raw_value = location.get('lat')

            elif feature_def.name == "location_lon":
                location = source_data.get('victim_location') or source_data.get('location')
                if location:
                    raw_value = location.get('lon')

            elif feature_def.name == "urban_density":
                location = source_data.get('victim_location') or source_data.get('location')
                if location:
                    lat = location.get('lat', 0)
                    lon = location.get('lon', 0)
                    # Simple urban density estimation
                    if lat > 28.5 and lat < 28.7 and lon > 77.0 and lon < 77.3:
                        raw_value = 'high'
                    else:
                        raw_value = 'medium'

            elif feature_def.name == "scam_type_encoded":
                scam_type = source_data.get('scam_type')
                if scam_type:
                    # Use label encoder if available, otherwise simple mapping
                    if 'scam_type_encoded' in self.encoders:
                        # For demo, create simple encoding
                        scam_type_map = {
                            'UPI_PHISHING': 0, 'FAKE_LOAN_APP': 1, 'IMPERSONATION': 2,
                            'LOTTERY_SCAM': 3, 'INVESTMENT_FRAUD': 4
                        }
                        raw_value = scam_type_map.get(scam_type, 5)

            elif feature_def.name == "transaction_type_encoded":
                transaction_type = source_data.get('transaction_type')
                if transaction_type:
                    # Simple encoding for demo
                    transaction_type_map = {
                        'CASH_WITHDRAWAL': 0, 'BALANCE_ENQUIRY': 1, 'MINI_STATEMENT': 2,
                        'PIN_CHANGE': 3, 'FUND_TRANSFER': 4, 'MOBILE_RECHARGE': 5
                    }
                    raw_value = transaction_type_map.get(transaction_type, 6)

            elif feature_def.name == "historical_complaint_count":
                # For demo, use random value based on location
                raw_value = np.random.randint(1, 20)

            elif feature_def.name == "historical_avg_amount":
                # For demo, use random value based on amount
                current_amount = source_data.get('amount', 50000)
                raw_value = current_amount * np.random.uniform(0.8, 1.2)

            # Apply transformations
            if raw_value is not None:
                transformed_value = await self._apply_transformation(
                    raw_value, feature_def
                )
                return transformed_value

            return None

        except Exception as e:
            logger.error(f"[Feature Store] Error extracting feature {feature_def.name}: {str(e)}")
            return None

    async def _apply_transformation(self, value: Any, feature_def: FeatureDefinition) -> Any:
        """
        Apply transformation to feature value
        """
        try:
            if feature_def.transformation == "none":
                return value

            elif feature_def.transformation == "label_encode":
                # Label encoding for categorical features
                if feature_def.name in self.encoders:
                    # For demo, return value as-is (encoding would be fitted with training data)
                    return value

            elif feature_def.transformation == "standard_scale":
                # Standard scaling for numerical features
                if feature_def.name in self.scalers:
                    # For demo, return normalized value
                    if isinstance(value, (int, float)):
                        return float(value) / 100000  # Simple normalization
                    return value

            elif feature_def.transformation == "log_transform":
                # Log transformation for skewed numerical features
                if isinstance(value, (int, float)) and value > 0:
                    return np.log1p(value)
                return value

            elif feature_def.transformation == "window_function":
                # Window functions are handled at database level
                return value

            return value

        except Exception as e:
            logger.error(f"[Feature Store] Error applying transformation: {str(e)}")
            return value

    async def store_features(self, feature_vector: FeatureVector,
                           store_type: FeatureStoreType = FeatureStoreType.ONLINE) -> bool:
        """
        Store feature vector in specified store
        """
        try:
            if store_type == FeatureStoreType.ONLINE:
                return await self._store_online_features(feature_vector)
            elif store_type == FeatureStoreType.OFFLINE:
                return await self._store_offline_features(feature_vector)
            elif store_type == FeatureStoreType.CACHED:
                return await self._store_cached_features(feature_vector)

            return False

        except Exception as e:
            logger.error(f"[Feature Store] Error storing features: {str(e)}")
            return False

    async def _store_online_features(self, feature_vector: FeatureVector) -> bool:
        """
        Store features in online store (Redis)
        """
        try:
            # Create Redis key
            redis_key = f"features:{feature_vector.entity_type}:{feature_vector.entity_id}"

            # Serialize feature vector
            feature_data = {
                'entity_id': feature_vector.entity_id,
                'entity_type': feature_vector.entity_type,
                'features': feature_vector.features,
                'timestamp': feature_vector.timestamp.isoformat(),
                'feature_version': feature_vector.feature_version,
                'metadata': feature_vector.metadata
            }

            # Store in Redis with TTL
            await self.redis_client.setex(
                redis_key,
                self.cache_ttl['hot_features'],
                json.dumps(feature_data, default=str)
            )

            # Also store individual feature values for quick lookup
            for feature_name, feature_value in feature_vector.features.items():
                feature_key = f"feature:{feature_name}:{feature_vector.entity_id}"
                await self.redis_client.setex(
                    feature_key,
                    self.cache_ttl['hot_features'],
                    json.dumps({'value': feature_value, 'timestamp': feature_vector.timestamp.isoformat()})
                )

            return True

        except Exception as e:
            logger.error(f"[Feature Store] Error storing online features: {str(e)}")
            return False

    async def _store_offline_features(self, feature_vector: FeatureVector) -> bool:
        """
        Store features in offline store (PostgreSQL)
        """
        try:
            with SessionLocal() as db:
                # Store feature vector in database
                query = text("""
                    INSERT INTO feature_store (
                        entity_id, entity_type, feature_vector, timestamp,
                        feature_version, metadata
                    ) VALUES (
                        :entity_id, :entity_type, :feature_vector, :timestamp,
                        :feature_version, :metadata
                    )
                    ON CONFLICT (entity_id, entity_type) DO UPDATE SET
                        feature_vector = EXCLUDED.feature_vector,
                        timestamp = EXCLUDED.timestamp,
                        feature_version = EXCLUDED.feature_version
                """)

                db.execute(query, {
                    'entity_id': feature_vector.entity_id,
                    'entity_type': feature_vector.entity_type,
                    'feature_vector': json.dumps(feature_vector.features),
                    'timestamp': feature_vector.timestamp,
                    'feature_version': feature_vector.feature_version,
                    'metadata': json.dumps(feature_vector.metadata)
                })

                db.commit()
                return True

        except Exception as e:
            logger.error(f"[Feature Store] Error storing offline features: {str(e)}")
            return False

    async def _store_cached_features(self, feature_vector: FeatureVector) -> bool:
        """
        Store features in cache (Redis with longer TTL)
        """
        try:
            redis_key = f"cached_features:{feature_vector.entity_type}:{feature_vector.entity_id}"

            feature_data = {
                'entity_id': feature_vector.entity_id,
                'entity_type': feature_vector.entity_type,
                'features': feature_vector.features,
                'timestamp': feature_vector.timestamp.isoformat(),
                'feature_version': feature_vector.feature_version
            }

            await self.redis_client.setex(
                redis_key,
                self.cache_ttl['warm_features'],
                json.dumps(feature_data, default=str)
            )

            return True

        except Exception as e:
            logger.error(f"[Feature Store] Error storing cached features: {str(e)}")
            return False

    async def get_features(self, entity_id: str, entity_type: str,
                         feature_names: List[str] = None,
                         store_type: FeatureStoreType = FeatureStoreType.ONLINE) -> Optional[FeatureVector]:
        """
        Retrieve features for an entity
        """
        try:
            if store_type == FeatureStoreType.ONLINE:
                return await self._get_online_features(entity_id, entity_type, feature_names)
            elif store_type == FeatureStoreType.OFFLINE:
                return await self._get_offline_features(entity_id, entity_type, feature_names)
            elif store_type == FeatureStoreType.CACHED:
                return await self._get_cached_features(entity_id, entity_type, feature_names)

            return None

        except Exception as e:
            logger.error(f"[Feature Store] Error getting features: {str(e)}")
            return None

    async def _get_online_features(self, entity_id: str, entity_type: str,
                                 feature_names: List[str] = None) -> Optional[FeatureVector]:
        """
        Get features from online store
        """
        try:
            redis_key = f"features:{entity_type}:{entity_id}"
            feature_data = await self.redis_client.get(redis_key)

            if feature_data:
                data = json.loads(feature_data)

                # Filter requested features if specified
                if feature_names:
                    filtered_features = {
                        name: value for name, value in data['features'].items()
                        if name in feature_names
                    }
                    data['features'] = filtered_features

                return FeatureVector(
                    entity_id=data['entity_id'],
                    entity_type=data['entity_type'],
                    features=data['features'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    feature_version=data['feature_version'],
                    metadata=data.get('metadata', {})
                )

            return None

        except Exception as e:
            logger.error(f"[Feature Store] Error getting online features: {str(e)}")
            return None

    async def _get_offline_features(self, entity_id: str, entity_type: str,
                                  feature_names: List[str] = None) -> Optional[FeatureVector]:
        """
        Get features from offline store
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT feature_vector, timestamp, feature_version, metadata
                    FROM feature_store
                    WHERE entity_id = :entity_id AND entity_type = :entity_type
                """)

                result = db.execute(query, {
                    'entity_id': entity_id,
                    'entity_type': entity_type
                }).fetchone()

                if result:
                    features = json.loads(result.feature_vector)

                    # Filter requested features if specified
                    if feature_names:
                        filtered_features = {
                            name: value for name, value in features.items()
                            if name in feature_names
                        }
                        features = filtered_features

                    return FeatureVector(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        features=features,
                        timestamp=result.timestamp,
                        feature_version=result.feature_version,
                        metadata=json.loads(result.metadata) if result.metadata else {}
                    )

            return None

        except Exception as e:
            logger.error(f"[Feature Store] Error getting offline features: {str(e)}")
            return None

    async def _get_cached_features(self, entity_id: str, entity_type: str,
                                 feature_names: List[str] = None) -> Optional[FeatureVector]:
        """
        Get features from cache
        """
        try:
            redis_key = f"cached_features:{entity_type}:{entity_id}"
            feature_data = await self.redis_client.get(redis_key)

            if feature_data:
                data = json.loads(feature_data)

                # Filter requested features if specified
                if feature_names:
                    filtered_features = {
                        name: value for name, value in data['features'].items()
                        if name in feature_names
                    }
                    data['features'] = filtered_features

                return FeatureVector(
                    entity_id=data['entity_id'],
                    entity_type=data['entity_type'],
                    features=data['features'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    feature_version=data['feature_version']
                )

            return None

        except Exception as e:
            logger.error(f"[Feature Store] Error getting cached features: {str(e)}")
            return None

    async def batch_extract_features(self, entities: List[Dict[str, Any]],
                                   feature_groups: List[str] = None) -> List[FeatureVector]:
        """
        Extract features for multiple entities in batch
        """
        try:
            feature_vectors = []

            for entity_data in entities:
                entity_id = entity_data.get('entity_id')
                entity_type = entity_data.get('entity_type', 'unknown')
                source_data = entity_data.get('source_data', {})

                if entity_id:
                    feature_vector = await self.extract_features(
                        entity_id, entity_type, source_data, feature_groups
                    )
                    feature_vectors.append(feature_vector)

            return feature_vectors

        except Exception as e:
            logger.error(f"[Feature Store] Error in batch feature extraction: {str(e)}")
            return []

    async def batch_store_features(self, feature_vectors: List[FeatureVector],
                                 store_type: FeatureStoreType = FeatureStoreType.ONLINE) -> int:
        """
        Store multiple feature vectors in batch
        """
        try:
            success_count = 0

            for feature_vector in feature_vectors:
                success = await self.store_features(feature_vector, store_type)
                if success:
                    success_count += 1

            return success_count

        except Exception as e:
            logger.error(f"[Feature Store] Error in batch feature storage: {str(e)}")
            return 0

    async def create_training_dataset(self, entity_ids: List[str], entity_type: str,
                                    target_variable: str = None,
                                    feature_groups: List[str] = None,
                                    time_range: Tuple[datetime, datetime] = None) -> pd.DataFrame:
        """
        Create training dataset for ML models
        """
        try:
            feature_data = []

            for entity_id in entity_ids:
                # Get features for entity
                feature_vector = await self.get_features(
                    entity_id, entity_type, store_type=FeatureStoreType.OFFLINE
                )

                if feature_vector:
                    # Apply time range filter if specified
                    if time_range:
                        if not (time_range[0] <= feature_vector.timestamp <= time_range[1]):
                            continue

                    # Prepare data row
                    row = feature_vector.features.copy()
                    row['entity_id'] = entity_id
                    row['timestamp'] = feature_vector.timestamp

                    # Add target variable if specified
                    if target_variable:
                        # In production, would fetch target from labels table
                        # For demo, use mock target
                        row[target_variable] = np.random.randint(0, 2)

                    feature_data.append(row)

            # Create DataFrame
            df = pd.DataFrame(feature_data)

            if not df.empty:
                # Apply feature preprocessing
                df = await self._preprocess_training_data(df, feature_groups)

            return df

        except Exception as e:
            logger.error(f"[Feature Store] Error creating training dataset: {str(e)}")
            return pd.DataFrame()

    async def _preprocess_training_data(self, df: pd.DataFrame,
                                      feature_groups: List[str] = None) -> pd.DataFrame:
        """
        Preprocess training data
        """
        try:
            processed_df = df.copy()

            # Handle missing values
            processed_df = processed_df.fillna(0)

            # Feature scaling for numerical columns
            numerical_columns = processed_df.select_dtypes(include=[np.number]).columns
            for col in numerical_columns:
                if col not in ['entity_id', target_variable for target_variable in ['target', 'label'] if target_variable in processed_df.columns]:
                    # Simple normalization
                    if processed_df[col].std() > 0:
                        processed_df[col] = (processed_df[col] - processed_df[col].mean()) / processed_df[col].std()

            # Feature selection if needed
            if feature_groups and len(processed_df.columns) > 50:
                # Select top k features
                feature_columns = [col for col in processed_df.columns
                                 if col not in ['entity_id', 'timestamp'] +
                                [target for target in ['target', 'label'] if target in processed_df.columns]]

                if len(feature_columns) > 20:
                    # For demo, keep first 20 features
                    keep_columns = ['entity_id', 'timestamp'] + feature_columns[:20]
                    if 'target' in processed_df.columns:
                        keep_columns.append('target')
                    if 'label' in processed_df.columns:
                        keep_columns.append('label')

                    processed_df = processed_df[keep_columns]

            return processed_df

        except Exception as e:
            logger.error(f"[Feature Store] Error preprocessing training data: {str(e)}")
            return df

    async def get_feature_statistics(self, feature_names: List[str] = None) -> Dict[str, Any]:
        """
        Get statistics for features
        """
        try:
            if feature_names is None:
                feature_names = list(self.feature_definitions.keys())

            stats = {}

            for feature_name in feature_names:
                if feature_name in self.feature_definitions:
                    feature_def = self.feature_definitions[feature_name]

                    stats[feature_name] = {
                        'type': feature_def.feature_type.value,
                        'data_type': feature_def.data_type,
                        'description': feature_def.description,
                        'source': f"{feature_def.source_table}.{feature_def.source_column}",
                        'transformation': feature_def.transformation,
                        'is_active': feature_def.is_active,
                        'version': feature_def.version
                    }

            return {
                'total_features': len(stats),
                'feature_statistics': stats,
                'feature_groups': {
                    group: len(features) for group, features in self.feature_groups.items()
                }
            }

        except Exception as e:
            logger.error(f"[Feature Store] Error getting feature statistics: {str(e)}")
            return {}

    async def refresh_feature_cache(self, entity_type: str, limit: int = 100) -> int:
        """
        Refresh feature cache for frequently accessed entities
        """
        try:
            refreshed_count = 0

            # Get recent entities from offline store
            with SessionLocal() as db:
                query = text("""
                    SELECT entity_id FROM feature_store
                    WHERE entity_type = :entity_type
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)

                results = db.execute(query, {
                    'entity_type': entity_type,
                    'limit': limit
                }).fetchall()

                for result in results:
                    entity_id = result.entity_id

                    # Get features from offline store
                    feature_vector = await self.get_features(
                        entity_id, entity_type, store_type=FeatureStoreType.OFFLINE
                    )

                    if feature_vector:
                        # Store in cache
                        await self.store_features(feature_vector, FeatureStoreType.CACHED)
                        refreshed_count += 1

            logger.info(f"[Feature Store] Refreshed cache for {refreshed_count} {entity_type} entities")
            return refreshed_count

        except Exception as e:
            logger.error(f"[Feature Store] Error refreshing feature cache: {str(e)}")
            return 0

    async def cleanup_expired_features(self) -> int:
        """
        Clean up expired features from online store
        """
        try:
            # Redis handles TTL automatically
            # This would handle any additional cleanup logic

            # Remove old feature vectors from offline store if needed
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            with SessionLocal() as db:
                query = text("""
                    DELETE FROM feature_store
                    WHERE timestamp < :cutoff_date
                """)

                result = db.execute(query, {'cutoff_date': cutoff_date})
                db.commit()

                cleaned_count = result.rowcount
                logger.info(f"[Feature Store] Cleaned up {cleaned_count} expired feature vectors")
                return cleaned_count

        except Exception as e:
            logger.error(f"[Feature Store] Error cleaning up expired features: {str(e)}")
            return 0

    async def get_feature_store_status(self) -> Dict[str, Any]:
        """
        Get feature store status and metrics
        """
        try:
            # Redis information
            redis_info = await self.redis_client.info()

            # Feature counts
            total_features = len(self.feature_definitions)
            active_features = sum(1 for f in self.feature_definitions.values() if f.is_active)

            return {
                'total_features': total_features,
                'active_features': active_features,
                'feature_groups': {group: len(features) for group, features in self.feature_groups.items()},
                'redis_connected': self.redis_client is not None,
                'redis_memory_used': redis_info.get('used_memory_human', 'Unknown'),
                'transformations_loaded': {
                    'scalers': len(self.scalers),
                    'encoders': len(self.encoders),
                    'feature_selectors': len(self.feature_selectors)
                },
                'cache_ttl_settings': self.cache_ttl
            }

        except Exception as e:
            logger.error(f"[Feature Store] Error getting feature store status: {str(e)}")
            return {'error': str(e)}

# Global feature store instance
feature_store = FeatureStore()