"""
Continuous Learning Loop
Real-time model improvement and adaptation system
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import os
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """
    Types of learning approaches
    """
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    ONLINE = "online"
    BATCH = "batch"
    FEDERATED = "federated"

class ModelType(Enum):
    """
    Types of models that can be learned
    """
    RISK_SCORING = "risk_scoring"
    ANOMALY_DETECTION = "anomaly_detection"
    PATTERN_RECOGNITION = "pattern_recognition"
    BEHAVIORAL_PREDICTION = "behavioral_prediction"
    TEMPORAL_FORECASTING = "temporal_forecasting"
    CAUSAL_INFERENCE = "causal_inference"

class LearningStatus(Enum):
    """
    Learning process status
    """
    IDLE = "idle"
    COLLECTING = "collecting"
    TRAINING = "training"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    ERROR = "error"

@dataclass
class LearningData:
    """
    Learning data structure
    """
    data_id: str
    features: Dict[str, Any]
    labels: Any
    timestamp: datetime
    source: str
    data_type: ModelType
    quality_score: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LearningModel:
    """
    Learning model structure
    """
    model_id: str
    model_type: ModelType
    learning_type: LearningType
    algorithm: str
    version: int
    performance_metrics: Dict[str, float]
    training_data_count: int
    created_at: datetime
    last_updated: datetime
    is_active: bool
    model_path: str
    hyperparameters: Dict[str, Any]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LearningConfig:
    """
    Learning configuration
    """
    learning_type: LearningType
    model_type: ModelType
    training_frequency: str  # 'hourly', 'daily', 'weekly'
    min_training_samples: int
    validation_split: float
    performance_threshold: float
    retrain_trigger_metrics: List[str]
    hyperparameter_tuning: bool
    feature_selection: bool
    ensemble_methods: bool
    max_training_time_minutes: int

@dataclass
class LearningResult:
    """
    Learning process result
    """
    learning_id: str
    model_id: str
    success: bool
    training_time_seconds: float
    performance_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    improvement_metrics: Dict[str, float]
    error_message: str = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class ContinuousLearningLoop:
    """
    Continuous learning loop for real-time model improvement
    """

    def __init__(self):
        # Learning storage
        self.active_models = {}
        self.learning_history = []
        self.data_buffers = defaultdict(lambda: deque(maxlen=10000))

        # Learning configurations
        self.learning_configs = {}
        self.learning_schedules = {}

        # Performance tracking
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))
        self.model_performance = {}

        # Learning state
        self.learning_status = LearningStatus.IDLE
        self.current_learning_task = None

        # Feature processing
        self.feature_processors = {}
        self.feature_importance = {}

        # Model registry
        self.model_registry = {}
        self.model_versions = defaultdict(int)

        # Learning statistics
        self.learning_stats = {
            'total_learning_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'total_training_time': 0,
            'average_improvement': 0,
            'models_deployed': 0,
            'data_points_processed': 0
        }

        # Data quality thresholds
        self.quality_thresholds = {
            'completeness': 0.8,
            'accuracy': 0.7,
            'consistency': 0.8,
            'timeliness': 0.9
        }

    async def initialize(self) -> bool:
        """
        Initialize continuous learning system
        """
        try:
            logger.info("[Continuous Learning] Initializing continuous learning loop...")

            # Load learning configurations
            await self._load_learning_configurations()

            # Load existing models
            await self._load_existing_models()

            # Initialize feature processors
            await self._initialize_feature_processors()

            # Start learning schedulers
            await self._start_learning_schedulers()

            # Start model monitoring
            asyncio.create_task(self._monitor_model_performance())

            # Start data quality monitoring
            asyncio.create_task(self._monitor_data_quality())

            logger.info("[Continuous Learning] Continuous learning loop initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Continuous Learning] Error initializing learning loop: {str(e)}")
            return False

    async def _load_learning_configurations(self) -> None:
        """
        Load learning configurations for different model types
        """
        try:
            # Risk scoring model configuration
            self.learning_configs[ModelType.RISK_SCORING] = LearningConfig(
                learning_type=LearningType.SUPERVISED,
                model_type=ModelType.RISK_SCORING,
                training_frequency='daily',
                min_training_samples=1000,
                validation_split=0.2,
                performance_threshold=0.8,
                retrain_trigger_metrics=['accuracy', 'f1_score', 'auc_roc'],
                hyperparameter_tuning=True,
                feature_selection=True,
                ensemble_methods=True,
                max_training_time_minutes=60
            )

            # Anomaly detection configuration
            self.learning_configs[ModelType.ANOMALY_DETECTION] = LearningConfig(
                learning_type=LearningType.UNSUPERVISED,
                model_type=ModelType.ANOMALY_DETECTION,
                training_frequency='weekly',
                min_training_samples=5000,
                validation_split=0.15,
                performance_threshold=0.75,
                retrain_trigger_metrics=['precision', 'recall', 'f1_score'],
                hyperparameter_tuning=False,
                feature_selection=True,
                ensemble_methods=False,
                max_training_time_minutes=120
            )

            # Behavioral prediction configuration
            self.learning_configs[ModelType.BEHAVIORAL_PREDICTION] = LearningConfig(
                learning_type=LearningType.REINFORCEMENT,
                model_type=ModelType.BEHAVIORAL_PREDICTION,
                training_frequency='daily',
                min_training_samples=2000,
                validation_split=0.25,
                performance_threshold=0.7,
                retrain_trigger_metrics=['accuracy', 'precision', 'recall'],
                hyperparameter_tuning=True,
                feature_selection=True,
                ensemble_methods=True,
                max_training_time_minutes=90
            )

            # Temporal forecasting configuration
            self.learning_configs[ModelType.TEMPORAL_FORECASTING] = LearningConfig(
                learning_type=LearningType.ONLINE,
                model_type=ModelType.TEMPORAL_FORECASTING,
                training_frequency='hourly',
                min_training_samples=500,
                validation_split=0.2,
                performance_threshold=0.8,
                retrain_trigger_metrics=['mse', 'mae', 'r2_score'],
                hyperparameter_tuning=False,
                feature_selection=True,
                ensemble_methods=True,
                max_training_time_minutes=30
            )

            logger.info("[Continuous Learning] Learning configurations loaded")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error loading learning configurations: {str(e)}")

    async def _load_existing_models(self) -> None:
        """
        Load existing trained models
        """
        try:
            models_dir = Path("models/continuous_learning")
            models_dir.mkdir(parents=True, exist_ok=True)

            for model_file in models_dir.glob("*.pkl"):
                try:
                    model_data = joblib.load(model_file)
                    model_id = model_file.stem

                    self.active_models[model_id] = model_data
                    self.model_performance[model_id] = model_data.get('performance', {})

                    logger.info(f"[Continuous Learning] Loaded model: {model_id}")

                except Exception as e:
                    logger.error(f"[Continuous Learning] Error loading model {model_file}: {str(e)}")

            logger.info(f"[Continuous Learning] Loaded {len(self.active_models)} existing models")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error loading existing models: {str(e)}")

    async def _initialize_feature_processors(self) -> None:
        """
        Initialize feature processors for different data types
        """
        try:
            # Initialize scaler for numerical features
            self.feature_processors['numerical'] = StandardScaler()

            # Initialize encoders for categorical features (would use proper encoders in production)
            self.feature_processors['categorical'] = {}

            logger.info("[Continuous Learning] Feature processors initialized")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error initializing feature processors: {str(e)}")

    async def _start_learning_schedulers(self) -> None:
        """
        Start scheduled learning tasks
        """
        try:
            for model_type, config in self.learning_configs.items():
                if config.training_frequency == 'hourly':
                    asyncio.create_task(self._hourly_learning_scheduler(model_type))
                elif config.training_frequency == 'daily':
                    asyncio.create_task(self._daily_learning_scheduler(model_type))
                elif config.training_frequency == 'weekly':
                    asyncio.create_task(self._weekly_learning_scheduler(model_type))

            logger.info("[Continuous Learning] Learning schedulers started")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error starting learning schedulers: {str(e)}")

    async def _hourly_learning_scheduler(self, model_type: ModelType) -> None:
        """
        Hourly learning scheduler
        """
        try:
            while True:
                await asyncio.sleep(3600)  # 1 hour
                await self._trigger_learning_cycle(model_type, "scheduled_hourly")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in hourly scheduler for {model_type.value}: {str(e)}")

    async def _daily_learning_scheduler(self, model_type: ModelType) -> None:
        """
        Daily learning scheduler
        """
        try:
            while True:
                # Wait until 2 AM daily
                now = datetime.now()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)

                sleep_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(sleep_seconds)

                await self._trigger_learning_cycle(model_type, "scheduled_daily")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in daily scheduler for {model_type.value}: {str(e)}")

    async def _weekly_learning_scheduler(self, model_type: ModelType) -> None:
        """
        Weekly learning scheduler
        """
        try:
            while True:
                # Wait until Sunday 3 AM weekly
                now = datetime.now()
                days_ahead = 6 - now.weekday()
                if days_ahead <= 0 or (days_ahead == 0 and now.hour >= 3):
                    days_ahead += 7

                next_run = now + timedelta(days=days_ahead)
                next_run = next_run.replace(hour=3, minute=0, second=0, microsecond=0)

                sleep_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(sleep_seconds)

                await self._trigger_learning_cycle(model_type, "scheduled_weekly")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in weekly scheduler for {model_type.value}: {str(e)}")

    async def add_learning_data(self, features: Dict[str, Any], labels: Any,
                              source: str, data_type: ModelType,
                              quality_score: float = None,
                              metadata: Dict[str, Any] = None) -> str:
        """
        Add new data for learning
        """
        try:
            data_id = f"data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(features)) % 10000:04d}"

            # Calculate quality score if not provided
            if quality_score is None:
                quality_score = await self._calculate_data_quality(features, labels)

            learning_data = LearningData(
                data_id=data_id,
                features=features,
                labels=labels,
                timestamp=datetime.utcnow(),
                source=source,
                data_type=data_type,
                quality_score=quality_score,
                metadata=metadata or {}
            )

            # Add to appropriate data buffer
            self.data_buffers[data_type].append(learning_data)

            # Store in database
            await self._store_learning_data(learning_data)

            # Update statistics
            self.learning_stats['data_points_processed'] += 1

            # Check if we should trigger learning
            config = self.learning_configs.get(data_type)
            if config and len(self.data_buffers[data_type]) >= config.min_training_samples:
                await self._trigger_learning_cycle(data_type, "data_threshold")

            logger.debug(f"[Continuous Learning] Added learning data {data_id} for {data_type.value}")
            return data_id

        except Exception as e:
            logger.error(f"[Continuous Learning] Error adding learning data: {str(e)}")
            raise

    async def _calculate_data_quality(self, features: Dict[str, Any], labels: Any) -> float:
        """
        Calculate data quality score
        """
        try:
            quality_scores = []

            # Completeness check
            if isinstance(features, dict):
                non_null_features = sum(1 for v in features.values() if v is not None)
                completeness = non_null_features / len(features) if features else 0
                quality_scores.append(completeness)

            # Consistency check (basic)
            if isinstance(features, dict):
                numeric_features = [v for v in features.values() if isinstance(v, (int, float))]
                if numeric_features:
                    # Check for reasonable ranges (would be more sophisticated in production)
                    consistency_score = 1.0
                    for value in numeric_features:
                        if abs(value) > 1e10:  # Unreasonably large values
                            consistency_score *= 0.8
                    quality_scores.append(consistency_score)

            # Timeliness check
            timeliness = 1.0  # Would check data age in production
            quality_scores.append(timeliness)

            return np.mean(quality_scores) if quality_scores else 0.5

        except Exception as e:
            logger.error(f"[Continuous Learning] Error calculating data quality: {str(e)}")
            return 0.5

    async def _store_learning_data(self, learning_data: LearningData) -> None:
        """
        Store learning data in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO learning_data (
                        data_id, features, labels, timestamp, source, data_type,
                        quality_score, metadata
                    ) VALUES (
                        :data_id, :features, :labels, :timestamp, :source, :data_type,
                        :quality_score, :metadata
                    )
                """)

                db.execute(query, {
                    'data_id': learning_data.data_id,
                    'features': json.dumps(learning_data.features),
                    'labels': json.dumps(learning_data.labels) if learning_data.labels is not None else None,
                    'timestamp': learning_data.timestamp,
                    'source': learning_data.source,
                    'data_type': learning_data.data_type.value,
                    'quality_score': learning_data.quality_score,
                    'metadata': json.dumps(learning_data.metadata)
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Continuous Learning] Error storing learning data: {str(e)}")

    async def _trigger_learning_cycle(self, model_type: ModelType, trigger_reason: str) -> None:
        """
        Trigger a learning cycle for a model type
        """
        try:
            if self.learning_status == LearningStatus.TRAINING:
                logger.info(f"[Continuous Learning] Learning already in progress, skipping {model_type.value}")
                return

            config = self.learning_configs.get(model_type)
            if not config:
                logger.warning(f"[Continuous Learning] No configuration found for {model_type.value}")
                return

            # Check if we have enough data
            if len(self.data_buffers[model_type]) < config.min_training_samples:
                logger.info(f"[Continuous Learning] Insufficient data for {model_type.value}: {len(self.data_buffers[model_type])}/{config.min_training_samples}")
                return

            logger.info(f"[Continuous Learning] Triggering learning cycle for {model_type.value} due to {trigger_reason}")

            # Start learning in background
            asyncio.create_task(self._execute_learning_cycle(model_type, trigger_reason))

        except Exception as e:
            logger.error(f"[Continuous Learning] Error triggering learning cycle: {str(e)}")

    async def _execute_learning_cycle(self, model_type: ModelType, trigger_reason: str) -> None:
        """
        Execute a complete learning cycle
        """
        learning_id = f"learning_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{model_type.value}"
        start_time = datetime.utcnow()

        try:
            self.learning_status = LearningStatus.TRAINING
            self.current_learning_task = learning_id

            logger.info(f"[Continuous Learning] Starting learning cycle {learning_id} for {model_type.value}")

            # Step 1: Data collection and preparation
            self.learning_status = LearningStatus.COLLECTING
            training_data = await self._prepare_training_data(model_type)

            if len(training_data) < self.learning_configs[model_type].min_training_samples:
                logger.warning(f"[Continuous Learning] Insufficient training data: {len(training_data)}")
                return

            # Step 2: Feature engineering and selection
            X, y = await self._engineer_features(training_data, model_type)

            # Step 3: Model training
            self.learning_status = LearningStatus.TRAINING
            model, training_metrics = await self._train_model(X, y, model_type)

            # Step 4: Model validation
            self.learning_status = LearningStatus.VALIDATING
            validation_metrics = await self._validate_model(model, X, y, model_type)

            # Step 5: Model deployment (if performance is acceptable)
            should_deploy = await self._should_deploy_model(
                model_type, training_metrics, validation_metrics
            )

            if should_deploy:
                self.learning_status = LearningStatus.DEPLOYING
                await self._deploy_model(model, model_type, training_metrics, validation_metrics)

            # Step 6: Create learning result
            learning_time = (datetime.utcnow() - start_time).total_seconds()
            improvement_metrics = await self._calculate_improvement_metrics(
                model_type, training_metrics, validation_metrics
            )

            learning_result = LearningResult(
                learning_id=learning_id,
                model_id=f"{model_type.value}_v{self.model_versions[model_type]}",
                success=should_deploy,
                training_time_seconds=learning_time,
                performance_metrics=training_metrics,
                validation_metrics=validation_metrics,
                improvement_metrics=improvement_metrics
            )

            # Store learning result
            await self._store_learning_result(learning_result)

            # Update statistics
            self.learning_stats['total_learning_cycles'] += 1
            self.learning_stats['successful_cycles'] += 1 if should_deploy else 0
            self.learning_stats['failed_cycles'] += 1 if not should_deploy else 0
            self.learning_stats['total_training_time'] += learning_time

            # Store in history
            self.learning_history.append(learning_result)

            logger.info(f"[Continuous Learning] Learning cycle {learning_id} completed: {'DEPLOYED' if should_deploy else 'REJECTED'}")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in learning cycle {learning_id}: {str(e)}")

            # Store failed result
            failed_result = LearningResult(
                learning_id=learning_id,
                model_id="",
                success=False,
                training_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
                performance_metrics={},
                validation_metrics={},
                improvement_metrics={},
                error_message=str(e)
            )
            await self._store_learning_result(failed_result)

            self.learning_stats['failed_cycles'] += 1

        finally:
            self.learning_status = LearningStatus.IDLE
            self.current_learning_task = None

    async def _prepare_training_data(self, model_type: ModelType) -> List[LearningData]:
        """
        Prepare training data for learning
        """
        try:
            data_buffer = self.data_buffers[model_type]
            config = self.learning_configs[model_type]

            # Filter data by quality threshold
            quality_threshold = self.quality_thresholds.get('completeness', 0.8)
            filtered_data = [
                data for data in data_buffer
                if data.quality_score >= quality_threshold
            ]

            # Additional data filtering based on recency
            cutoff_time = datetime.utcnow() - timedelta(days=30)  # Use last 30 days
            recent_data = [
                data for data in filtered_data
                if data.timestamp >= cutoff_time
            ]

            # Balance data if needed (for supervised learning)
            if config.learning_type == LearningType.SUPERVISED:
                recent_data = await self._balance_training_data(recent_data, model_type)

            logger.info(f"[Continuous Learning] Prepared {len(recent_data)} training samples for {model_type.value}")
            return recent_data

        except Exception as e:
            logger.error(f"[Continuous Learning] Error preparing training data: {str(e)}")
            return []

    async def _balance_training_data(self, data: List[LearningData], model_type: ModelType) -> List[LearningData]:
        """
        Balance training data for supervised learning
        """
        try:
            # Group by label
            label_groups = defaultdict(list)
            for item in data:
                label_key = str(item.labels) if item.labels is not None else 'unknown'
                label_groups[label_key].append(item)

            # Find the size of the smallest group
            min_group_size = min(len(group) for group in label_groups.values())

            # Sample each group to the size of the smallest group
            balanced_data = []
            for group in label_groups.values():
                if len(group) > min_group_size:
                    sampled_group = np.random.choice(group, min_group_size, replace=False).tolist()
                else:
                    sampled_group = group
                balanced_data.extend(sampled_group)

            np.random.shuffle(balanced_data)
            return balanced_data

        except Exception as e:
            logger.error(f"[Continuous Learning] Error balancing training data: {str(e)}")
            return data

    async def _engineer_features(self, data: List[LearningData], model_type: ModelType) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform feature engineering
        """
        try:
            if not data:
                return np.array([]), np.array([])

            # Extract features and labels
            features_list = []
            labels_list = []

            for item in data:
                # Convert features to numerical format
                numerical_features = []
                feature_names = set()

                # Get all feature names from all data points
                for d in data:
                    feature_names.update(d.features.keys())

                feature_names = sorted(list(feature_names))

                for feature_name in feature_names:
                    value = item.features.get(feature_name, 0)
                    if isinstance(value, str):
                        # Simple categorical encoding (would use proper encoding in production)
                        value = hash(value) % 1000
                    elif not isinstance(value, (int, float)):
                        value = 0
                    numerical_features.append(float(value))

                features_list.append(numerical_features)
                labels_list.append(item.labels)

            X = np.array(features_list)
            y = np.array(labels_list)

            # Handle missing values
            X = np.nan_to_num(X, nan=0.0)

            # Feature scaling for numerical features
            if model_type in [ModelType.RISK_SCORING, ModelType.BEHAVIORAL_PREDICTION]:
                if model_type not in self.feature_processors:
                    self.feature_processors[model_type] = StandardScaler()

                # Fit scaler if not already fitted
                if not hasattr(self.feature_processors[model_type], 'scale_'):
                    self.feature_processors[model_type].fit(X)

                X = self.feature_processors[model_type].transform(X)

            # Feature selection if enabled
            config = self.learning_configs.get(model_type)
            if config and config.feature_selection and len(features_list) > 0:
                X = await self._select_features(X, y, model_type)

            logger.debug(f"[Continuous Learning] Engineered features: X.shape={X.shape}, y.shape={y.shape}")
            return X, y

        except Exception as e:
            logger.error(f"[Continuous Learning] Error engineering features: {str(e)}")
            return np.array([]), np.array([])

    async def _select_features(self, X: np.ndarray, y: np.ndarray, model_type: ModelType) -> np.ndarray:
        """
        Perform feature selection
        """
        try:
            from sklearn.feature_selection import SelectKBest, f_classif

            # Select top k features
            k = min(50, X.shape[1])  # Select top 50 features or all if less
            selector = SelectKBest(score_func=f_classif, k=k)
            X_selected = selector.fit_transform(X, y)

            # Store feature importance
            feature_scores = selector.scores_
            self.feature_importance[model_type] = {
                'scores': feature_scores.tolist(),
                'selected_indices': selector.get_support(indices=True).tolist()
            }

            logger.info(f"[Continuous Learning] Selected {X_selected.shape[1]} features for {model_type.value}")
            return X_selected

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in feature selection: {str(e)}")
            return X

    async def _train_model(self, X: np.ndarray, y: np.ndarray, model_type: ModelType) -> Tuple[Any, Dict[str, float]]:
        """
        Train a model based on the configuration
        """
        try:
            config = self.learning_configs[model_type]

            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=config.validation_split, random_state=42
            )

            # Choose algorithm based on model type and configuration
            if model_type == ModelType.RISK_SCORING:
                if config.ensemble_methods:
                    model = GradientBoostingClassifier(
                        n_estimators=100,
                        learning_rate=0.1,
                        max_depth=3,
                        random_state=42
                    )
                else:
                    model = RandomForestClassifier(
                        n_estimators=100,
                        max_depth=10,
                        random_state=42
                    )

            elif model_type == ModelType.ANOMALY_DETECTION:
                # Use isolation forest for anomaly detection
                from sklearn.ensemble import IsolationForest
                model = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )

            elif model_type == ModelType.BEHAVIORAL_PREDICTION:
                model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    random_state=42
                )

            else:
                # Default to logistic regression
                model = LogisticRegression(random_state=42, max_iter=1000)

            # Train model
            if model_type == ModelType.ANOMALY_DETECTION:
                model.fit(X_train)
                # For anomaly detection, create labels for validation
                y_pred = model.predict(X_val)
                y_pred = (y_pred == -1).astype(int)  # Convert -1 (anomaly) to 1
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)

            # Calculate training metrics
            training_metrics = await self._calculate_metrics(
                y_val, y_pred, model_type, X_val, model
            )

            logger.info(f"[Continuous Learning] Trained {model_type.value} model with metrics: {training_metrics}")
            return model, training_metrics

        except Exception as e:
            logger.error(f"[Continuous Learning] Error training model: {str(e)}")
            raise

    async def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                               model_type: ModelType, X_val: np.ndarray = None,
                               model: Any = None) -> Dict[str, float]:
        """
        Calculate performance metrics
        """
        try:
            metrics = {}

            if model_type != ModelType.ANOMALY_DETECTION:
                # Classification metrics
                metrics['accuracy'] = accuracy_score(y_true, y_pred)
                metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)

                try:
                    if len(np.unique(y_true)) == 2:
                        metrics['auc_roc'] = roc_auc_score(y_true, y_pred)
                    else:
                        # For multi-class, calculate one-vs-rest AUC
                        from sklearn.preprocessing import label_binarize
                        y_true_bin = label_binarize(y_true, classes=np.unique(y_true))
                        if y_true_bin.shape[1] == 1:
                            y_true_bin = np.hstack([1 - y_true_bin, y_true_bin])
                        metrics['auc_roc'] = roc_auc_score(y_true_bin, y_pred, multi_class='ovr', average='weighted')
                except Exception as e:
                    logger.warning(f"[Continuous Learning] Could not calculate AUC: {str(e)}")
                    metrics['auc_roc'] = 0.0

            else:
                # Anomaly detection metrics
                metrics['anomaly_rate'] = np.mean(y_pred == 1)
                metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
                metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)

            # Cross-validation score
            try:
                if model_type != ModelType.ANOMALY_DETECTION and X_val is not None and model is not None:
                    cv_scores = cross_val_score(model, X_val, y_true, cv=3, scoring='accuracy')
                    metrics['cv_accuracy'] = np.mean(cv_scores)
                    metrics['cv_std'] = np.std(cv_scores)
            except Exception as e:
                logger.warning(f"[Continuous Learning] Cross-validation failed: {str(e)}")

            return metrics

        except Exception as e:
            logger.error(f"[Continuous Learning] Error calculating metrics: {str(e)}")
            return {}

    async def _validate_model(self, model: Any, X: np.ndarray, y: np.ndarray,
                            model_type: ModelType) -> Dict[str, float]:
        """
        Validate model on holdout data
        """
        try:
            # Split data for final validation
            _, X_test, _, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Make predictions
            if model_type == ModelType.ANOMALY_DETECTION:
                y_pred = model.predict(X_test)
                y_pred = (y_pred == -1).astype(int)
            else:
                y_pred = model.predict(X_test)

            # Calculate validation metrics
            validation_metrics = await self._calculate_metrics(
                y_test, y_pred, model_type, X_test, model
            )

            return validation_metrics

        except Exception as e:
            logger.error(f"[Continuous Learning] Error validating model: {str(e)}")
            return {}

    async def _should_deploy_model(self, model_type: ModelType,
                                 training_metrics: Dict[str, float],
                                 validation_metrics: Dict[str, float]) -> bool:
        """
        Determine if model should be deployed
        """
        try:
            config = self.learning_configs[model_type]
            threshold = config.performance_threshold

            # Check primary metrics
            primary_metrics = config.retrain_trigger_metrics

            for metric in primary_metrics:
                if metric in validation_metrics:
                    if validation_metrics[metric] < threshold:
                        logger.info(f"[Continuous Learning] Model rejected: {metric}={validation_metrics[metric]:.3f} < {threshold}")
                        return False

            # Compare with existing model performance
            current_model_id = f"{model_type.value}_v{self.model_versions[model_type]}"
            if current_model_id in self.model_performance:
                current_performance = self.model_performance[current_model_id]

                # Require improvement in at least one metric
                improvement = False
                for metric in primary_metrics:
                    if metric in validation_metrics and metric in current_performance:
                        if validation_metrics[metric] > current_performance[metric] * 1.05:  # 5% improvement
                            improvement = True
                            break

                if not improvement:
                    logger.info(f"[Continuous Learning] Model rejected: no significant improvement over current model")
                    return False

            logger.info(f"[Continuous Learning] Model approved for deployment")
            return True

        except Exception as e:
            logger.error(f"[Continuous Learning] Error evaluating model deployment: {str(e)}")
            return False

    async def _deploy_model(self, model: Any, model_type: ModelType,
                          training_metrics: Dict[str, float],
                          validation_metrics: Dict[str, float]) -> None:
        """
        Deploy the trained model
        """
        try:
            # Increment model version
            self.model_versions[model_type] += 1
            model_id = f"{model_type.value}_v{self.model_versions[model_type]}"

            # Prepare model data for storage
            model_data = {
                'model': model,
                'model_type': model_type.value,
                'version': self.model_versions[model_type],
                'performance': {**training_metrics, **validation_metrics},
                'created_at': datetime.utcnow().isoformat(),
                'feature_processor': self.feature_processors.get(model_type),
                'feature_importance': self.feature_importance.get(model_type, {})
            }

            # Save model to disk
            models_dir = Path("models/continuous_learning")
            models_dir.mkdir(parents=True, exist_ok=True)

            model_path = models_dir / f"{model_id}.pkl"
            joblib.dump(model_data, model_path)

            # Update active models
            self.active_models[model_id] = model_data
            self.model_performance[model_id] = model_data['performance']

            # Update model registry
            self.model_registry[model_type.value] = {
                'active_model_id': model_id,
                'deployed_at': datetime.utcnow().isoformat(),
                'performance': model_data['performance']
            }

            # Store in database
            await self._store_model_deployment(model_id, model_type, model_data)

            self.learning_stats['models_deployed'] += 1

            logger.info(f"[Continuous Learning] Deployed model {model_id} with performance: {validation_metrics}")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error deploying model: {str(e)}")
            raise

    async def _store_model_deployment(self, model_id: str, model_type: ModelType,
                                    model_data: Dict[str, Any]) -> None:
        """
        Store model deployment information in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO model_deployments (
                        model_id, model_type, version, performance_metrics,
                        created_at, model_path, metadata
                    ) VALUES (
                        :model_id, :model_type, :version, :performance_metrics,
                        :created_at, :model_path, :metadata
                    )
                    ON CONFLICT (model_id) DO UPDATE SET
                        performance_metrics = EXCLUDED.performance_metrics,
                        created_at = EXCLUDED.created_at
                """)

                db.execute(query, {
                    'model_id': model_id,
                    'model_type': model_type.value,
                    'version': self.model_versions[model_type],
                    'performance_metrics': json.dumps(model_data['performance']),
                    'created_at': datetime.utcnow(),
                    'model_path': f"models/continuous_learning/{model_id}.pkl",
                    'metadata': json.dumps({
                        'feature_importance': model_data.get('feature_importance', {}),
                        'deployment_source': 'continuous_learning'
                    })
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Continuous Learning] Error storing model deployment: {str(e)}")

    async def _calculate_improvement_metrics(self, model_type: ModelType,
                                           training_metrics: Dict[str, float],
                                           validation_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate improvement metrics compared to previous model
        """
        try:
            improvement = {}

            current_model_id = f"{model_type.value}_v{self.model_versions[model_type]}"
            if current_model_id in self.model_performance:
                current_performance = self.model_performance[current_model_id]

                for metric, value in validation_metrics.items():
                    if metric in current_performance:
                        old_value = current_performance[metric]
                        improvement[metric] = ((value - old_value) / old_value * 100) if old_value != 0 else 0

            return improvement

        except Exception as e:
            logger.error(f"[Continuous Learning] Error calculating improvement metrics: {str(e)}")
            return {}

    async def _store_learning_result(self, result: LearningResult) -> None:
        """
        Store learning result in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO learning_results (
                        learning_id, model_id, success, training_time_seconds,
                        performance_metrics, validation_metrics, improvement_metrics,
                        error_message, warnings, created_at
                    ) VALUES (
                        :learning_id, :model_id, :success, :training_time_seconds,
                        :performance_metrics, :validation_metrics, :improvement_metrics,
                        :error_message, :warnings, :created_at
                    )
                """)

                db.execute(query, {
                    'learning_id': result.learning_id,
                    'model_id': result.model_id,
                    'success': result.success,
                    'training_time_seconds': result.training_time_seconds,
                    'performance_metrics': json.dumps(result.performance_metrics),
                    'validation_metrics': json.dumps(result.validation_metrics),
                    'improvement_metrics': json.dumps(result.improvement_metrics),
                    'error_message': result.error_message,
                    'warnings': json.dumps(result.warnings),
                    'created_at': datetime.utcnow()
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Continuous Learning] Error storing learning result: {str(e)}")

    async def _monitor_model_performance(self) -> None:
        """
        Monitor model performance and trigger retraining if needed
        """
        try:
            while True:
                await asyncio.sleep(300)  # Check every 5 minutes

                for model_type in ModelType:
                    if model_type in self.model_registry:
                        await self._check_model_performance(model_type)

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in performance monitoring: {str(e)}")

    async def _check_model_performance(self, model_type: ModelType) -> None:
        """
        Check if model performance has degraded
        """
        try:
            registry_info = self.model_registry.get(model_type.value)
            if not registry_info:
                return

            active_model_id = registry_info['active_model_id']
            performance_history = self.performance_history[model_type]

            # Check if we have enough recent performance data
            if len(performance_history) < 10:
                return

            # Calculate recent performance trend
            recent_performance = list(performance_history)[-10:]
            avg_recent_performance = np.mean([p.get('accuracy', 0) for p in recent_performance])

            # Compare with deployed model performance
            deployed_performance = registry_info['performance'].get('accuracy', 0)

            # If recent performance is significantly worse, trigger retraining
            if avg_recent_performance < deployed_performance * 0.9:  # 10% degradation
                logger.warning(f"[Continuous Learning] Performance degradation detected for {model_type.value}")
                await self._trigger_learning_cycle(model_type, "performance_degradation")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error checking model performance: {str(e)}")

    async def _monitor_data_quality(self) -> None:
        """
        Monitor data quality and trigger alerts if needed
        """
        try:
            while True:
                await asyncio.sleep(600)  # Check every 10 minutes

                for model_type, data_buffer in self.data_buffers.items():
                    if len(data_buffer) > 100:  # Only check if we have sufficient data
                        await self._assess_data_quality(model_type, data_buffer)

        except Exception as e:
            logger.error(f"[Continuous Learning] Error in data quality monitoring: {str(e)}")

    async def _assess_data_quality(self, model_type: ModelType, data_buffer: deque) -> None:
        """
        Assess data quality for a model type
        """
        try:
            recent_data = list(data_buffer)[-100:]  # Check last 100 data points

            # Calculate quality metrics
            quality_scores = [data.quality_score for data in recent_data]
            avg_quality = np.mean(quality_scores)

            # Check if quality has dropped
            if avg_quality < self.quality_thresholds['completeness']:
                logger.warning(f"[Continuous Learning] Low data quality for {model_type.value}: {avg_quality:.3f}")

            # Check for data drift (simplified)
            timestamps = [data.timestamp for data in recent_data]
            time_span = (max(timestamps) - min(timestamps)).total_seconds()

            if time_span > 86400 * 7:  # Data is older than 7 days
                logger.warning(f"[Continuous Learning] Data staleness detected for {model_type.value}")

        except Exception as e:
            logger.error(f"[Continuous Learning] Error assessing data quality: {str(e)}")

    async def get_model_prediction(self, model_type: ModelType, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get prediction from the active model
        """
        try:
            registry_info = self.model_registry.get(model_type.value)
            if not registry_info:
                return {'error': f'No active model found for {model_type.value}'}

            active_model_id = registry_info['active_model_id']
            model_data = self.active_models.get(active_model_id)

            if not model_data:
                return {'error': f'Model {active_model_id} not found in memory'}

            model = model_data['model']

            # Prepare features
            numerical_features = []
            feature_names = set()

            # Use the same feature engineering as during training
            for data in self.data_buffers[model_type]:
                feature_names.update(data.features.keys())

            feature_names = sorted(list(feature_names))

            for feature_name in feature_names:
                value = features.get(feature_name, 0)
                if isinstance(value, str):
                    value = hash(value) % 1000
                elif not isinstance(value, (int, float)):
                    value = 0
                numerical_features.append(float(value))

            X = np.array([numerical_features])
            X = np.nan_to_num(X, nan=0.0)

            # Apply feature scaling if available
            feature_processor = model_data.get('feature_processor')
            if feature_processor and hasattr(feature_processor, 'scale_'):
                X = feature_processor.transform(X)

            # Make prediction
            if model_type == ModelType.ANOMALY_DETECTION:
                prediction = model.predict(X)[0]
                is_anomaly = prediction == -1
                anomaly_score = model.decision_function(X)[0] if hasattr(model, 'decision_function') else 0

                return {
                    'prediction': 'anomaly' if is_anomaly else 'normal',
                    'is_anomaly': is_anomaly,
                    'anomaly_score': float(anomaly_score),
                    'confidence': abs(float(anomaly_score))
                }
            else:
                prediction = model.predict(X)[0]
                probabilities = None

                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(X)[0]
                    confidence = float(np.max(probabilities))
                else:
                    confidence = 1.0

                return {
                    'prediction': int(prediction),
                    'probabilities': probabilities.tolist() if probabilities is not None else None,
                    'confidence': confidence,
                    'model_id': active_model_id,
                    'model_version': self.model_versions[model_type]
                }

        except Exception as e:
            logger.error(f"[Continuous Learning] Error getting prediction: {str(e)}")
            return {'error': str(e)}

    async def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive learning statistics
        """
        try:
            return {
                'learning_statistics': self.learning_stats,
                'active_models': {
                    model_type.value: registry_info
                    for model_type, registry_info in self.model_registry.items()
                },
                'current_learning_status': {
                    'status': self.learning_status.value,
                    'current_task': self.current_learning_task
                },
                'data_buffer_sizes': {
                    model_type.value: len(buffer)
                    for model_type, buffer in self.data_buffers.items()
                },
                'model_performance': self.model_performance,
                'feature_importance': {
                    model_type.value: importance
                    for model_type, importance in self.feature_importance.items()
                },
                'learning_configurations': {
                    model_type.value: asdict(config)
                    for model_type, config in self.learning_configs.items()
                }
            }

        except Exception as e:
            logger.error(f"[Continuous Learning] Error getting learning statistics: {str(e)}")
            return {'error': str(e)}

    async def force_learning_cycle(self, model_type: ModelType) -> Dict[str, Any]:
        """
        Force a learning cycle for a specific model type
        """
        try:
            if self.learning_status == LearningStatus.TRAINING:
                return {'error': 'Learning already in progress'}

            if len(self.data_buffers[model_type]) < self.learning_configs[model_type].min_training_samples:
                return {'error': f'Insufficient data: {len(self.data_buffers[model_type])} < {self.learning_configs[model_type].min_training_samples}'}

            # Trigger learning cycle
            await self._trigger_learning_cycle(model_type, "manual_trigger")

            return {'message': f'Learning cycle triggered for {model_type.value}'}

        except Exception as e:
            logger.error(f"[Continuous Learning] Error forcing learning cycle: {str(e)}")
            return {'error': str(e)}

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get continuous learning system status
        """
        try:
            return {
                'system_status': 'operational',
                'learning_status': self.learning_status.value,
                'current_task': self.current_learning_task,
                'active_models_count': len(self.active_models),
                'data_points_processed': self.learning_stats['data_points_processed'],
                'total_learning_cycles': self.learning_stats['total_learning_cycles'],
                'success_rate': (
                    self.learning_stats['successful_cycles'] / max(1, self.learning_stats['total_learning_cycles']) * 100
                ),
                'last_activity': datetime.utcnow().isoformat(),
                'data_quality_metrics': {
                    'completeness_threshold': self.quality_thresholds['completeness'],
                    'accuracy_threshold': self.quality_thresholds['accuracy'],
                    'consistency_threshold': self.quality_thresholds['consistency'],
                    'timeliness_threshold': self.quality_thresholds['timeliness']
                }
            }

        except Exception as e:
            logger.error(f"[Continuous Learning] Error getting system status: {str(e)}")
            return {'error': str(e)}

# Global continuous learning instance
continuous_learning = ContinuousLearningLoop()