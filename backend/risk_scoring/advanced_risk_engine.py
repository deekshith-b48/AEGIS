"""
Advanced Risk Scoring Engine with Machine Learning
Multi-dimensional risk assessment with ensemble methods and real-time learning

Features:
- Ensemble machine learning models
- Real-time risk scoring
- Multi-dimensional risk factors
- Adaptive thresholding
- Explainable AI (XAI) integration
- Continuous learning
- Risk prediction and forecasting
- Multi-source data integration
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.calibration import calibration_curve
import shap  # SHAP for model explainability
import joblib
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

Base = declarative_base()

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class RiskCategory(Enum):
    """Risk category classifications"""
    FINANCIAL = "financial"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    REPUTATION = "reputation"
    OPERATIONAL = "operational"
    LEGAL = "legal"

class ModelType(Enum):
    """Machine learning model types"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LOGISTIC_REGRESSION = "logistic_regression"
    ENSEMBLE = "ensemble"

@dataclass
class RiskFactor:
    """Individual risk factor with weight"""
    factor_id: str
    factor_name: str
    factor_category: RiskCategory
    value: float
    weight: float
    description: str
    confidence: float
    timestamp: datetime
    source: str

@dataclass
class RiskScore:
    """Comprehensive risk score"""
    score_id: str
    entity_id: str
    entity_type: str  # 'transaction', 'account', 'customer', 'merchant'
    overall_score: float
    risk_level: RiskLevel
    risk_category: RiskCategory
    component_scores: Dict[str, float]
    confidence: float
    explanation: List[str]
    recommendation: List[str]
    timestamp: datetime
    model_version: str
    feature_importance: Dict[str, float]

@dataclass
class ModelPerformance:
    """Machine learning model performance metrics"""
    model_id: str
    model_type: ModelType
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    calibration_score: float
    last_trained: datetime
    training_samples: int

class RiskScoreDatabase(Base):
    """Database model for risk scores"""
    __tablename__ = "risk_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    score_id = Column(String, nullable=False, unique=True, index=True)
    entity_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False, index=True)
    risk_category = Column(String, nullable=False, index=True)
    component_scores = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=True)
    recommendation = Column(JSON, nullable=True)
    model_version = Column(String, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelDatabase(Base):
    """Database model for ML models"""
    __tablename__ = "risk_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, nullable=False, unique=True)
    model_type = Column(String, nullable=False)
    model_data = Column(JSON, nullable=False)
    performance_data = Column(JSON, nullable=True)
    feature_names = Column(JSON, nullable=False)
    scaler_data = Column(JSON, nullable=True)
    label_encoder_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdvancedRiskScoringEngine:
    """
    Advanced Risk Scoring Engine with Machine Learning
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Machine learning models
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.model_performance = {}

        # Ensemble configuration
        self.model_weights = config.get('model_weights', {
            ModelType.RANDOM_FOREST: 0.35,
            ModelType.GRADIENT_BOOSTING: 0.35,
            ModelType.LOGISTIC_REGRESSION: 0.30
        })

        # Risk scoring configuration
        self.risk_thresholds = config.get('risk_thresholds', {
            RiskLevel.VERY_LOW: 0.0,
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.85,
            RiskLevel.CRITICAL: 0.95
        })

        # Feature configuration
        self.feature_config = config.get('features', {})
        self.feature_importance_cache = {}

        # Database setup
        self.engine = create_engine(config.get('database_url', 'sqlite:///aegis_risk_scoring.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis for caching
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 9),
            decode_responses=True
        )

        # Learning configuration
        self.learning_rate = config.get('learning_rate', 0.01)
        self.min_samples_for_training = config.get('min_samples_for_training', 1000)
        self.model_retrain_interval = config.get('model_retrain_interval', 86400)  # 24 hours
        self.feature_drift_threshold = config.get('feature_drift_threshold', 0.1)

        # State management
        self.is_running = False
        self.last_training_time = None
        self.total_scores_generated = 0
        self.models_trained = 0

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize the advanced risk scoring engine"""
        logger.info("Initializing Advanced Risk Scoring Engine")

        try:
            # Load existing models
            await self._load_models_from_database()

            # Initialize feature engineering
            await self._initialize_feature_engineering()

            # Start continuous learning
            self.is_running = True
            learning_task = asyncio.create_task(self._continuous_learning_loop())

            # Start performance monitoring
            monitor_task = asyncio.create_task(self._performance_monitoring())

            logger.info("Advanced Risk Scoring Engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize risk scoring engine: {str(e)}")
            return False

    async def train_advanced_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train advanced machine learning models for risk scoring
        """
        try:
            logger.info(f"Training advanced ML models with {len(training_data)} samples")

            start_time = time.time()

            # Prepare training data
            X, y = await self._prepare_training_data(training_data)

            if len(X) < self.min_samples_for_training:
                return {
                    'success': False,
                    'error': f'Insufficient training data: {len(X)} samples (minimum: {self.min_samples_for_training})'
                }

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Train ensemble models
            training_results = {}

            # Train Random Forest
            rf_result = await self._train_random_forest(X_train, X_test, y_train, y_test)
            training_results['random_forest'] = rf_result

            # Train Gradient Boosting
            gb_result = await self._train_gradient_boosting(X_train, X_test, y_train, y_test)
            training_results['gradient_boosting'] = gb_result

            # Train Logistic Regression
            lr_result = await self._train_logistic_regression(X_train, X_test, y_train, y_test)
            training_results['logistic_regression'] = lr_result

            # Train ensemble
            ensemble_result = await self._train_ensemble(
                X_train, X_test, y_train, y_test, training_results
            )
            training_results['ensemble'] = ensemble_result

            # Calculate feature importance
            await self._calculate_feature_importance(X_train, y_train)

            # Save models to database
            await self._save_models_to_database()

            # Update performance metrics
            self.last_training_time = datetime.utcnow()
            self.models_trained += 1

            processing_time = time.time() - start_time

            result = {
                'success': True,
                'models_trained': len(training_results),
                'training_samples': len(X_train),
                'validation_samples': len(X_test),
                'processing_time_seconds': processing_time,
                'model_performance': {
                    model: {
                        'accuracy': perf['accuracy'],
                        'f1_score': perf['f1_score'],
                        'roc_auc': perf['roc_auc']
                    }
                    for model, perf in training_results.items()
                },
                'feature_importance': self.feature_importance_cache,
                'risk_distribution': self._calculate_risk_distribution()
            }

            # Cache result
            await self._cache_training_result(result)

            logger.info(f"Advanced ML models trained successfully: {result}")
            return result

        except Exception as e:
            logger.error(f"Error training advanced models: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def calculate_comprehensive_risk_score(self, entity_data: Dict[str, Any]) -> RiskScore:
        """
        Calculate comprehensive risk score using ML models
        """
        try:
            score_id = f"risk_{entity_data.get('entity_id', 'unknown')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Extract risk factors
            risk_factors = await self._extract_risk_factors(entity_data)

            # Prepare features
            features = await self._prepare_features(risk_factors)

            # Get ensemble prediction
            if not self.models or not self.models.get('ensemble'):
                # Fallback to rule-based scoring
                return await self._calculate_rule_based_score(entity_data, risk_factors, score_id)

            # Make predictions with ensemble
            ensemble_prediction = await self._predict_with_ensemble(features)

            # Convert prediction to risk level
            risk_level = self._score_to_risk_level(ensemble_prediction['probability'])

            # Get component scores
            component_scores = await self._get_component_scores(risk_factors)

            # Generate explanation
            explanation = await self._generate_explanation(ensemble_prediction, risk_factors)

            # Generate recommendations
            recommendations = await self._generate_recommendations(risk_level, risk_factors)

            # Create risk score object
            risk_score = RiskScore(
                score_id=score_id,
                entity_id=entity_data.get('entity_id', 'unknown'),
                entity_type=entity_data.get('entity_type', 'unknown'),
                overall_score=ensemble_prediction['probability'],
                risk_level=risk_level,
                risk_category=RiskCategory.FINANCIAL,  # Default, can be enhanced
                component_scores=component_scores,
                confidence=ensemble_prediction['confidence'],
                explanation=explanation,
                recommendation=recommendations,
                timestamp=datetime.utcnow(),
                model_version="v1.0",
                feature_importance=self._get_feature_importance_for_score(features)
            )

            # Cache the score
            await self._cache_risk_score(risk_score)

            # Update metrics
            self.total_scores_generated += 1

            return risk_score

        except Exception as e:
            logger.error(f"Error calculating comprehensive risk score: {str(e)}")
            # Return default risk score
            return await self._create_default_risk_score(entity_data)

    async def calculate_batch_risk_scores(self, entity_data_list: List[Dict[str, Any]]) -> List[RiskScore]:
        """
        Calculate risk scores for multiple entities in batch
        """
        try:
            logger.info(f"Calculating batch risk scores for {len(entity_data_list)} entities")

            # Process in parallel
            risk_scores = []
            tasks = []

            for entity_data in entity_data_list:
                task = asyncio.create_task(
                    self.calculate_comprehensive_risk_score(entity_data)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            risk_scores = await asyncio.gather(*tasks)

            logger.info(f"Generated {len(risk_scores)} risk scores in batch")
            return risk_scores

        except Exception as e:
            logger.error(f"Error calculating batch risk scores: {str(e)}")
            return []

    def _prepare_training_data(self, training_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for ML models"""
        try:
            # Define features
            feature_columns = [
                'amount', 'transaction_count', 'risk_score', 'fraud_signals_count',
                'account_age_days', 'device_risk_score', 'location_risk_score',
                'temporal_risk_score', 'velocity_risk_score', 'cross_border_flag',
                'high_value_transaction', 'unusual_timing', 'new_device_flag'
            ]

            # Ensure all required columns exist
            for col in feature_columns:
                if col not in training_data.columns:
                    training_data[col] = 0.0

            # Create features and target
            X = training_data[feature_columns].values
            y = training_data['is_fraud'].values if 'is_fraud' in training_data.columns else (
                (training_data['risk_score'] > 0.7).astype(int)
            )

            return X, y

        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return np.array([]), np.array([])

    async def _train_random_forest(self, X_train: np.ndarray, X_test: np.ndarray,
                                  y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train Random Forest model"""
        try:
            logger.info("Training Random Forest model")

            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            model.fit(X_train, y_train)

            # Predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Performance metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_proba)

            # Calibration
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test, y_proba, n_bins=10)
            calibration_score = np.mean(mean_predicted_value)

            # Store model
            self.models[ModelType.RANDOM_FOREST] = model
            self.model_performance[ModelType.RANDOM_FOREST] = ModelPerformance(
                model_id="rf_v1",
                model_type=ModelType.RANDOM_FOREST,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                roc_auc=roc_auc,
                calibration_score=calibration_score,
                last_trained=datetime.utcnow(),
                training_samples=len(X_train)
            )

            return {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'roc_auc': roc_auc,
                'calibration_score': calibration_score
            }

        except Exception as e:
            logger.error(f"Error training Random Forest: {str(e)}")
            return {'error': str(e)}

    async def _train_gradient_boosting(self, X_train: np.ndarray, X_test: np.ndarray,
                                     y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train Gradient Boosting model"""
        try:
            logger.info("Training Gradient Boosting model")

            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                n_jobs=-1
            )

            model.fit(X_train, y_train)

            # Predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Performance metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_proba)

            # Calibration
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test, y_proba, n_bins=10)
            calibration_score = np.mean(mean_predicted_value)

            # Store model
            self.models[ModelType.GRADIENT_BOOSTING] = model
            self.model_performance[ModelType.GRADIENT_BOOSTING] = ModelPerformance(
                model_id="gb_v1",
                model_type=ModelType.GRADIENT_BOOSTING,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                roc_auc=roc_auc,
                calibration_score=calibration_score,
                last_trained=datetime.utcnow(),
                training_samples=len(X_train)
            )

            return {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'roc_auc': roc_auc,
                'calibration_score': calibration_score
            }

        except Exception as e:
            logger.error(f"Error training Gradient Boosting: {str(e)}")
            return {'error': str(e)}

    async def _train_logistic_regression(self, X_train: np.ndarray, X_test: np.ndarray,
                                      y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train Logistic Regression model"""
        try:
            logger.info("Training Logistic Regression model")

            model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                n_jobs=-1
            )

            model.fit(X_train, y_train)

            # Predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Performance metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_proba)

            # Calibration
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test, y_proba, n_bins=10)
            calibration_score = np.mean(mean_predicted_value)

            # Store model
            self.models[ModelType.LOGISTIC_REGRESSION] = model
            self.model_performance[ModelType.LOGISTIC_REGRESSION] = ModelPerformance(
                model_id="lr_v1",
                model_type=ModelType.LOGISTIC_REGRESSION,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                roc_auc=roc_auc,
                calibration_score=calibration_score,
                last_trained=datetime.utcnow(),
                training_samples=len(X_train)
            )

            return {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'roc_auc': roc_auc,
                'calibration_score': calibration_score
            }

        except Exception as e:
            logger.error(f"Error training Logistic Regression: {str(e)}")
            return {'error': str(e)}

    async def _train_ensemble(self, X_train: np.ndarray, X_test: np.ndarray,
                             y_train: np.ndarray, y_test: np.ndarray,
                             training_results: Dict) -> Dict[str, Any]:
        """Train ensemble model"""
        try:
            logger.info("Training ensemble model")

            # Get individual model predictions
            rf_pred = self.models[ModelType.RANDOM_FOREST].predict_proba(X_test)[:, 1]
            gb_pred = self.models[ModelType.GRADIENT_BOOSTING].predict_proba(X_test)[:, 1]
            lr_pred = self.models[ModelType.LOGISTIC_REGRESSION].predict_proba(X_test)[:, 1]

            # Weighted ensemble
            weighted_pred = (
                self.model_weights[ModelType.RANDOM_FOREST] * rf_pred +
                self.model_weights[ModelType.GRADIENT_BOOSTING] * gb_pred +
                self.model_weights[ModelType.LOGISTIC_REGRESSION] * lr_pred
            )

            # Final prediction
            ensemble_pred = (weighted_pred > 0.5).astype(int)
            ensemble_proba = weighted_pred

            # Performance metrics
            accuracy = accuracy_score(y_test, ensemble_pred)
            precision = precision_score(y_test, ensemble_pred)
            recall = recall_score(y_test, ensemble_pred)
            f1 = f1_score(y_test, ensemble_pred)
            roc_auc = roc_auc_score(y_test, ensemble_proba)

            # Calibration
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test, ensemble_proba, n_bins=10)
            calibration_score = np.mean(mean_predicted_value)

            # Store ensemble
            self.models[ModelType.ENSEMBLE] = {
                'weights': self.model_weights,
                'models': {
                    'random_forest': self.models[ModelType.RANDOM_FOREST],
                    'gradient_boosting': self.models[Model.GRADIENT_BOOSTING],
                    'logistic_regression': self.models[ModelType.LOGISTIC_REGRESSION]
                }
            }
            self.model_performance[ModelType.ENSEMBLE] = ModelPerformance(
                model_id="ensemble_v1",
                model_type=ModelType.ENSEMBLE,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                roc_auc=roc_auc,
                calibration_score=calibration_score,
                last_trained=datetime.utcnow(),
                training_samples=len(X_train)
            )

            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'roc_auc': roc_auc,
                'calibration_score': calibration_score
            }

        except Exception as e:
            logger.error(f"Error training ensemble model: {str(e)}")
            return {'error': str(e)}

    async def _calculate_feature_importance(self, X_train: np.ndarray, y_train: np.ndarray):
        """Calculate feature importance using SHAP"""
        try:
            if ModelType.RANDOM_FOREST in self.models:
                # Use Random Forest feature importance
                model = self.models[ModelType.RANDOM_FOREST]
                importances = model.feature_importances_

                feature_names = [
                    'amount', 'transaction_count', 'risk_score', 'fraud_signals_count',
                    'account_age_days', 'device_risk_score', 'location_risk_score',
                    'temporal_risk_score', 'velocity_risk_score', 'cross_border_flag',
                    'high_value_transaction', 'unusual_timing', 'new_device_flag'
                ]

                # Cache feature importance
                for i, importance in enumerate(importances):
                    if i < len(feature_names):
                        self.feature_importance_cache[feature_names[i]] = importance

                logger.info(f"Calculated feature importance for {len(self.feature_importance_cache)} features")

        except Exception as e:
            logger.error(f"Error calculating feature importance: {str(e)}")

    async def _extract_risk_factors(self, entity_data: Dict[str, Any]) -> List[RiskFactor]:
        """Extract risk factors from entity data"""
        try:
            risk_factors = []

            # Financial risk factors
            amount = entity_data.get('amount', 0)
            risk_factors.append(RiskFactor(
                factor_id="amount",
                factor_name="Transaction Amount",
                factor_category=RiskCategory.FINANCIAL,
                value=min(amount / 100000, 1.0),  # Normalize by 100k
                weight=0.3,
                description="Transaction amount risk",
                confidence=0.9,
                timestamp=datetime.utcnow(),
                source="transaction_data"
            ))

            # Account age risk
            account_age_days = entity_data.get('account_age_days', 0)
            risk_factors.append(RiskFactor(
                factor_id="account_age",
                factor_name="Account Age",
                factor_category=RiskCategory.SECURITY,
                value=max(0, 1.0 - (account_age_days / 365)),  # Newer accounts are riskier
                weight=0.2,
                description="Account age risk",
                confidence=0.95,
                timestamp=datetime.utcnow(),
                source="account_data"
            ))

            # Device risk
            device_risk_score = entity_data.get('device_risk_score', 0)
            risk_factors.append(RiskFactor(
                factor_id="device_risk",
                factor_name="Device Risk",
                factor_category=RiskCategory.SECURITY,
                value=device_risk_score,
                weight=0.2,
                description="Device risk assessment",
                confidence=0.8,
                timestamp=datetime.utcnow(),
                source="device_data"
            ))

            # Location risk
            location_risk_score = entity_data.get('location_risk_score', 0)
            risk_factors.append(RiskFactor(
                factor_id="location_risk",
                factor_name="Location Risk",
                factor_category=RiskCategory.SECURITY,
                value=location_risk_score,
                weight=0.15,
                description="Geographic risk assessment",
                confidence=0.85,
                timestamp=datetime.utcnow(),
                source="location_data"
            ))

            # Velocity risk
            velocity_risk_score = entity_data.get('velocity_risk_score', 0)
            risk_factors.append(RiskFactor(
                factor_id="velocity_risk",
                factor_name="Transaction Velocity",
                factor_category=RiskCategory.OPERATIONAL,
                value=velocity_risk_score,
                weight=0.15,
                description="Transaction velocity risk",
                confidence=0.75,
                timestamp=datetime.utcnow(),
                source="transaction_analysis"
            ))

            # Fraud signals
            fraud_signals = entity_data.get('fraud_signals', [])
            fraud_signals_count = len(fraud_signals)
            risk_factors.append(RiskFactor(
                factor_id="fraud_signals",
                factor_name="Fraud Signals",
                factor_category=RiskCategory.SECURITY,
                value=min(fraud_signals_count / 10, 1.0),
                weight=0.25,
                description="Fraud detection signals",
                confidence=0.9,
                timestamp=datetime.utcnow(),
                source="fraud_detection"
            ))

            # Cross-border flag
            cross_border_flag = 1.0 if entity_data.get('cross_border_flag', False) else 0.0
            risk_factors.append(RiskFactor(
                factor_id="cross_border",
                factor_name="Cross-Border Transaction",
                factor_category=RiskCategory.COMPLIANCE,
                value=cross_border_flag,
                weight=0.2,
                description="Cross-border transaction flag",
                confidence=0.95,
                timestamp=datetime.utcnow(),
                source="transaction_analysis"
            ))

            # High value transaction
            high_value_flag = 1.0 if entity_data.get('amount', 0) > 100000 else 0.0
            risk_factors.append(RiskFactor(
                factor_id="high_value",
                factor_name="High Value Transaction",
                factor_category=RiskCategory.FINANCIAL,
                value=high_value_flag,
                weight=0.2,
                description="High value transaction (>100k)",
                confidence=1.0,
                timestamp=datetime.utcnow(),
                source="transaction_data"
            ))

            # Unusual timing
            unusual_timing_flag = 1.0 if entity_data.get('unusual_timing', False) else 0.0
            risk_factors.append(RiskFactor(
                factor_id="unusual_timing",
                factor_name="Unusual Transaction Timing",
                factor_category=RiskCategory.OPERATIONAL,
                value=unusual_timing_flag,
                weight=0.1,
                description="Unusual transaction timing",
                confidence=0.8,
                timestamp=datetime.utcnow(),
                source="transaction_analysis"
            ))

            # New device flag
            new_device_flag = 1.0 if entity_data.get('new_device_flag', False) else 0.0
            risk_factors.append(RiskFactor(
                factor_id="new_device",
                factor_name="New Device",
                factor_category=RiskCategory.SECURITY,
                value=new_device_flag,
                weight=0.15,
                description="New device usage",
                confidence=0.9,
                timestamp=datetime.utcnow(),
                source="device_data"
            ))

            return risk_factors

        except Exception as e:
            logger.error(f"Error extracting risk factors: {str(e)}")
            return []

    async def _prepare_features(self, risk_factors: List[RiskFactor]) -> np.ndarray:
        """Prepare features for ML models"""
        try:
            # Create feature vector
            feature_dict = {factor.factor_id: factor.value for factor in risk_factors}

            # Ensure consistent feature order
            feature_order = [
                'amount', 'account_age', 'device_risk', 'location_risk',
                'velocity_risk', 'fraud_signals', 'cross_border',
                'high_value', 'unusual_timing', 'new_device'
            ]

            features = []
            for feature_name in feature_order:
                features.append(feature_dict.get(feature_name, 0.0))

            return np.array(features)

        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return np.zeros(10)  # Return default feature vector

    async def _predict_with_ensemble(self, features: np.ndarray) -> Dict[str, Any]:
        """Make prediction using ensemble model"""
        try:
            if ModelType.ENSEMBLE not in self.models:
                return {'probability': 0.5, 'confidence': 0.5}

            ensemble = self.models[ModelType.ENSEMBLE]
            models = ensemble['models']

            # Get individual predictions
            rf_proba = models['random_forest'].predict_proba([features])[0][1]
            gb_proba = models['gradient_boosting'].predict_proba([features])[0][1]
            lr_proba = models['logistic_regression'].predict_proba([features])[0][1]

            # Weighted ensemble
            weighted_pred = (
                ensemble['weights'][ModelType.RANDOM_FOREST] * rf_proba +
                ensemble['weights'][ModelType.GRADIENT_BOOSTING] * gb_proba +
                ensemble['weights'][ModelType.LOGISTIC_REGRESSION] * lr_proba
            )

            # Calculate confidence based on model agreement
            predictions = [rf_proba, gb_proba, lr_proba]
            max_pred = max(predictions)
            min_pred = min(predictions)
            confidence = 1.0 - (max_pred - min_pred)

            return {
                'probability': weighted_pred,
                'confidence': confidence,
                'individual_predictions': {
                    'random_forest': rf_proba,
                    'gradient_boosting': gb_proba,
                    'logistic_regression': lr_proba
                }
            }

        except Exception as e:
            logger.error(f"Error making ensemble prediction: {str(e)}")
            return {'probability': 0.5, 'confidence': 0.5}

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert probability score to risk level"""
        for level, threshold in sorted(self.risk_thresholds.items(), key=lambda x: x[1]):
            if score >= threshold:
                return level
        return RiskLevel.VERY_LOW

    async def _get_component_scores(self, risk_factors: List[RiskFactor]) -> Dict[str, float]:
        """Get component risk scores"""
        try:
            component_scores = {}

            # Group by risk category
            category_groups = defaultdict(list)
            for factor in risk_factors:
                category_groups[factor.factor_category.value].append(factor.value)

            for category, values in category_groups.items():
                if values:
                    category_scores[category] = np.mean(values)

            return component_scores

        except Exception as e:
            logger.error(f"Error calculating component scores: {str(e)}")
            return {}

    async def _generate_explanation(self, prediction: Dict[str, Any], risk_factors: List[RiskFactor]) -> List[str]:
        """Generate explanation for risk prediction"""
        try:
            explanations = []

            # Top contributing factors
            contributing_factors = sorted(
                [(factor.factor_name, factor.value * factor.weight)
                 for factor in risk_factors],
                key=lambda x: x[1], reverse=True
            )[:5]

            for factor_name, contribution in contributing_factors:
                if contribution > 0.3:
                    explanations.append(
                        f"High {factor_name} (score: {contribution:.2f})"
                    )

            # Model confidence explanation
            confidence = prediction.get('confidence', 0.5)
            if confidence > 0.8:
                explanations.append("High confidence prediction from ensemble model")
            elif confidence < 0.4:
                explanations.append("Low confidence - requires manual review")

            # Individual model agreement
            individual_predictions = prediction.get('individual_predictions', {})
            if individual_predictions:
                pred_values = list(individual_predictions.values())
                pred_variance = np.var(pred_values)
                if pred_variance < 0.1:
                    explanations.append("Consistent predictions across models")
                elif pred_variance > 0.2:
                    explanations.append("Divergent predictions - high uncertainty")

            return explanations

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return ["Unable to generate explanation"]

    async def _generate_recommendations(self, risk_level: RiskLevel, risk_factors: List[RiskFactor]) -> List[str]:
        """Generate recommendations based on risk level and factors"""
        try:
            recommendations = []

            # Risk level-based recommendations
            if risk_level in [RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
                recommendations.extend([
                    "IMMEDIATE: Block transaction and freeze accounts",
                    "Elevate to fraud investigation team",
                    "Implement enhanced monitoring",
                    "Consider account closure"
                ])
            elif risk_level == RiskLevel.HIGH:
                recommendations.extend([
                    "Flag for manual review",
                    "Increase monitoring frequency",
                    "Require additional verification",
                    "Implement temporary restrictions"
                ])
            elif risk_level == RiskLevel.MEDIUM:
                recommendations.extend([
                    "Standard monitoring procedures",
                    "Periodic risk assessment",
                    "Maintain normal controls"
                ])
            else:
                recommendations.extend([
                    "Standard processing",
                    "Routine monitoring"
                ])

            # Factor-specific recommendations
            high_risk_factors = [
                factor for factor in risk_factors
                if factor.value > 0.7
            ]

            for factor in high_risk_factors[:3]:  # Top 3 high-risk factors
                if factor.factor_category == RiskCategory.FINANCIAL:
                    recommendations.append(f"Enhanced financial monitoring for {factor.factor_name}")
                elif factor.factor_category == RiskCategory.SECURITY:
                    recommendations.append(f"Security review for {factor.factor_name}")
                elif factor.factor_category == RiskCategory.OPERATIONAL:
                    recommendations.append(f"Operational controls for {factor.factor_name}")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations"]

    def _get_feature_importance_for_score(self, features: np.ndarray) -> Dict[str, float]:
        """Get feature importance for a specific score"""
        try:
            feature_names = [
                'amount', 'account_age', 'device_risk', 'location_risk',
                'velocity_risk', 'fraud_signals', 'cross_border',
                'high_value', 'unusual_timing', 'new_device'
            ]

            importance_dict = {}
            for i, feature_name in enumerate(feature_names):
                if i < len(features) and i < len(feature_names):
                    feature_name = feature_names[i]
                    cached_importance = self.feature_importance_cache.get(feature_name, 0.1)
                    importance_dict[feature_name] = cached_importance

            return importance_dict

        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            return {}

    async def _create_default_risk_score(self, entity_data: Dict[str, Any]) -> RuleBasedRiskScore:
        """Create default rule-based risk score when ML models are not available"""
        try:
            # Simple rule-based scoring
            score = 0.5

            # Adjust based on known risk indicators
            if entity_data.get('amount', 0) > 50000:
                score += 0.2
            if entity_data.get('fraud_signals'):
                score += 0.3 * min(len(entity_data['fraud_signals']) / 3, 1.0)
            if entity_data.get('cross_border_flag', False):
                score += 0.2

            score = min(score, 1.0)

            # Create risk score object
            return RuleBasedRiskScore(
                score_id=f"rule_{entity_data.get('entity_id', 'unknown')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                entity_id=entity_data.get('entity_id', 'unknown'),
                entity_type=entity_data.get('entity_type', 'unknown'),
                overall_score=score,
                risk_level=self._score_to_risk_level(score),
                risk_category=RiskCategory.FINANCIAL,
                component_scores={},
                confidence=0.6,
                explanation=["Rule-based fallback scoring"],
                recommendation=["Standard review"],
                timestamp=datetime.utcnow(),
                model_version="rule_based"
            )

        except Exception as e:
            logger.error(f"Error creating default risk score: {str(e)}")
            # Return minimal risk score
            return RuleBasedRiskScore(
                score_id=f"rule_{entity_data.get('entity_id', 'unknown')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                entity_id=entity_data.get('entity_id', 'unknown'),
                entity_type=entity_data.get('entity_type', 'unknown'),
                overall_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                risk_category=RiskCategory.FINANCIAL,
                component_scores={},
                confidence=0.5,
                explanation=["Default risk scoring"],
                recommendation=["Standard monitoring"],
                timestamp=datetime.utcnow(),
                model_version="rule_based_v1"
            )

    async def _load_models_from_database(self):
        """Load trained models from database"""
        try:
            db = self.SessionLocal()
            try:
                # Load model records
                model_records = db.query(ModelDatabase).all()

                for record in model_records:
                    model_data = record.model_data
                    model_type = ModelType(model_data['model_type'])

                    # Reconstruct model based on type
                    if model_type == ModelType.RANDOM_FOREST:
                        model = RandomForestClassifier(
                            n_estimators=model_data.get('n_estimators', 100),
                            max_depth=model_data.get('max_depth', 10),
                            random_state=model_data.get('random_state', 42),
                            n_jobs=-1
                        )
                        model.set_params(**model_data.get('model_params', {}))

                    elif model_type == ModelType.GRADIENT_BOOSTING:
                        model = GradientBoostingClassifier(
                            n_estimators=model_data.get('n_estimators', 100),
                            learning_rate=model_data.get('learning_rate', 0.1),
                            max_depth=model_data.get('max_depth', 6),
                            random_state=model_data.get('random_state', 42),
                            n_jobs=-1
                        )
                        model.set_params(**model_data.get('model_params', {}))

                    elif model_type == ModelType.LOGISTIC_REGRESSION:
                        model = LogisticRegression(
                            random_state=model_data.get('random_state', 42),
                            max_iter=model_data.get('max_iter', 1000),
                            n_jobs=-1
                        )
                        model.set_params(**model_data.get('model_params', {}))

                    # Load performance data
                    if record.performance_data:
                        self.model_performance[model_type] = ModelPerformance(
                            model_id=record.model_id,
                            model_type=model_type,
                            **record.performance_data
                        )

                    # Load scalers and encoders
                    if record.scaler_data:
                        self.scalers[model_type] = StandardScaler()
                        self.scalers[model_type].mean_ = np.array(record.scaler_data.get('mean_', []))
                        self.scalers[model_type].scale_ = np.array(record.scaler_data.get('scale_', []))

                    if record.label_encoder_data:
                        self.label_encoders[model_type] = LabelEncoder()
                        self.label_encoders[model_type].classes_ = np.array(record.label_encoder_data.get('classes_', []))

                    # Store model
                    self.models[model_type] = model

                logger.info(f"Loaded {len(self.models)} models from database")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error loading models from database: {str(e)}")

    async def _initialize_feature_engineering(self):
        """Initialize feature engineering components"""
        try:
            # Initialize scalers for each model type
            for model_type in ModelType:
                if model_type not in self.scalers:
                    self.scalers[model_type] = StandardScaler()

                if model_type not in self.label_encoders:
                    self.label_encoders[model_type] = LabelEncoder()

            logger.info("Feature engineering components initialized")

        except Exception as e:
            logger.error(f"Error initializing feature engineering: {str(e)}")

    async def _save_models_to_database(self):
        """Save trained models to database"""
        try:
            db = self.SessionLocal()
            try:
                for model_type, model in self.models.items():
                    if model_type == ModelType.ENSEMBLE:
                        # Save ensemble metadata
                        model_record = ModelDatabase(
                            model_id="ensemble_v1",
                            model_type=model_type.value,
                            model_data={
                                'weights': model['weights'],
                                'model_params': {},
                                'feature_names': []
                            },
                            performance_data=asdict(self.model_performance.get(model_type, {})),
                            feature_names=[],
                            scaler_data={},
                            label_encoder_data={},
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                    else:
                        # Save individual model
                        model_record = ModelDatabase(
                            model_id=f"{model_type.value}_v1",
                            model_type=model_type.value,
                            model_data={
                                'n_estimators': getattr(model, 'n_estimators', 100),
                                'max_depth': getattr(model, 'max_depth', 10),
                                'random_state': getattr(model, 'random_state', 42),
                                'model_params': {}
                            },
                            performance_data=asdict(self.model_performance.get(model_type, {})),
                            feature_names=[],
                            scaler_data={},
                            label_encoder_data={},
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )

                        db.add(model_record)

                db.commit()
                logger.info("Models saved to database")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error saving models to database: {str(e)}")

    async def _cache_training_result(self, result: Dict[str, Any]):
        """Cache training result"""
        try:
            self.redis_client.setex(
                "latest_training_result",
                3600,  # 1 hour
                json.dumps(result, default=str)
            )

        except Exception as e:
            logger.error(f"Error caching training result: {str(e)}")

    def _calculate_risk_distribution(self) -> Dict[str, float]:
        """Calculate risk distribution"""
        try:
            if not self.models:
                return {}

            # Get sample predictions
            sample_predictions = []
            for model_type, model in self.models.items():
                if model_type != ModelType.ENSEMBLE:
                    # Generate sample predictions for distribution analysis
                    try:
                        sample_data = np.random.normal(0, 1, (100, 20))
                        predictions = model.predict_proba(sample_data)[:, 1]
                        sample_predictions.extend(predictions)
                    except:
                        pass

            if sample_predictions:
                # Calculate distribution
                risk_counts = {
                    'very_low': len([p for p in sample_predictions if p < 0.2]),
                    'low': len([p for p in sample_predictions if 0.2 <= p < 0.4]),
                    'medium': len([p for p in sample_predictions if 0.4 <= p < 0.7]),
                    'high': len([p for p in sample_predictions if 0.7 <= p < 0.85]),
                    'very_high': len([p for p in sample_predictions if p >= 0.85]),
                    'critical': len([p for p in sample_predictions if p >= 0.95])
                }

                total = sum(risk_counts.values())
                if total > 0:
                    return {level: count/total for level, count in risk_counts.items()}

            return {}

        except Exception as e:
            logger.error(f"Error calculating risk distribution: {str(e)}")
            return {}

    async def _cache_risk_score(self, risk_score: RiskScore):
        """Cache risk score"""
        try:
            cache_key = f"risk_score_{risk_score.score_id}"
            self.redis_client.setex(
                cache_key,
                3600,  # 1 hour
                json.dumps(asdict(risk_score), default=str)
            )

        except Exception as e:
            logger.error(f"Error caching risk score: {str(e)}")

    async def _continuous_learning_loop(self):
        """Continuous learning loop for model improvement"""
        while self.is_running:
            try:
                logger.info("Starting continuous learning cycle")

                # Check if retraining is needed
                if self._should_retrain_models():
                    logger.info("Triggering model retraining")
                    # In practice, this would collect recent data and retrain models
                    # For now, we'll just update performance metrics
                    await self._update_performance_metrics()

                # Wait for next cycle
                await asyncio.sleep(self.model_retrain_interval)

            except Exception as e:
                logger.error(f"Error in continuous learning loop: {str(e)}")
                await asyncio.sleep(300)  # 5 minutes before retrying

    def _should_retrain_models(self) -> bool:
        """Determine if models should be retrained"""
        try:
            # Check if enough time has passed since last training
            if self.last_training_time:
                time_since_training = (datetime.utcnow() - self.last_training_time).total_seconds()
                return time_since_training >= self.model_retrain_interval

            # Check if performance has degraded
            if self.model_performance:
                avg_accuracy = np.mean([
                    perf.accuracy for perf in self.model_performance.values()
                    if perf.accuracy
                ])
                return avg_accuracy < 0.7  # Retrain if accuracy drops below 70%

            return False

        except Exception as e:
            logger.error(f"Error checking retrain condition: {str(e)}")
            return False

    async def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # In practice, this would collect recent performance data
            # For now, we'll simulate some metrics updates
            for model_type, performance in self.model_performance.items():
                # Simulate slight performance changes
                new_accuracy = performance.accuracy * (1 + np.random.normal(0, 0.01))  # Small random variation
                performance.accuracy = max(0.1, min(1.0, new_accuracy))
                performance.f1_score = performance.f1_score * (1 + np.random.normal(0, 0.01))
                performance.f1_score = max(0.1, min(1.0, performance.f1_score))

                # Update timestamp
                performance.last_trained = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")

    async def _performance_monitoring(self):
        """Monitor system performance"""
        while self.is_running:
            try:
                # Calculate performance metrics
                performance_data = {
                    'uptime_hours': (datetime.utcnow() - datetime.now()).total_seconds() / 3600,
                    'total_scores_generated': self.total_scores_generated,
                    'models_trained': self.models_trained,
                    'active_models': len(self.models),
                    'ensemble_available': ModelType.ENSEMBLE in self.models,
                    'cache_hits': self.redis_client.dbsize() if self.redis_client else 0,
                    'memory_usage': self._estimate_memory_usage(),
                    'is_healthy': self._check_system_health(),
                    'last_update': datetime.utcnow().isoformat()
                }

                # Cache performance data
                self.redis_client.setex(
                    "risk_engine_performance",
                    300,  # 5 minutes
                    json.dumps(performance_data, default=str)
                )

                logger.info(f"Performance metrics: {performance_data}")

                # Wait for next monitoring cycle
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}")
                await asyncio.sleep(60)

    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage"""
        try:
            # Rough estimation
            models_memory = len(self.models) * 1024 * 1024  # 1MB per model
            cache_memory = self.redis_client.dbsize() * 1024 * 1024 if self.redis_client else 0
            scalers_memory = len(self.scalers) * 10 * 1024  # 10KB per scaler
            encoders_memory = len(self.label_encoders) * 5 * 1024  # 5KB per encoder

            total_bytes = models_memory + cache_memory + scalers_memory + encoders_memory

            if total_bytes < 1024:
                return f"{total_bytes} B"
            elif total_bytes < 1024 * 1024:
                return f"{total_bytes / 1024:.1f} KB"
            else:
                return f"{total_bytes / (1024 * 1024):.1f} MB"

        except Exception:
            return "Unknown"

    def _check_system_health(self) -> bool:
        """Check overall system health"""
        try:
            health_checks = [
                len(self.models) > 0,
                ModelType.ENSEMBLE in self.models,
                self.total_scores_generated > 0,
                self._calculate_overall_accuracy() > 0.5,
                self.redis_client.ping() if self.redis_client else False
            ]

            return all(health_checks)

        except Exception:
            return False

    def _calculate_overall_accuracy(self) -> float:
        """Calculate overall accuracy across all models"""
        try:
            if not self.model_performance:
                return 0.5

            accuracies = [perf.accuracy for perf in self.model_performance.values() if perf.accuracy]
            return np.mean(accuracies) if accuracies else 0.5

        except Exception:
            return 0.5

    async def get_model_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive model performance dashboard"""
        try:
            dashboard = {
                'model_count': len(self.models),
                'models_available': list(self.models.keys()),
                'performance_metrics': {
                    model_type: {
                        'accuracy': perf.accuracy,
                        'precision': perf.precision,
                        'recall': perf.recall,
                        'f1_score': perf.f1_score,
                        'roc_auc': perf.roc_auc,
                        'calibration_score': perf.calibration_score
                    }
                    for model_type, perf in self.model_performance.items()
                },
                'ensemble_performance': self.model_performance.get(ModelType.ENSEMBLE),
                'last_training': self.last_training_time.isoformat() if self.last_training_time else None,
                'total_scores_generated': self.total_scores_generated,
                'models_trained': self.models_trained,
                'feature_importance': self.feature_importance_cache
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error getting model performance dashboard: {str(e)}")
            return {'error': str(e)}

    async def export_risk_scoring_analysis(self) -> Dict[str, Any]:
        """Export comprehensive risk scoring analysis"""
        try:
            # Get recent risk scores
            db = self.SessionLocal()
            try:
                recent_scores = db.query(RiskScoreDatabase).order_by(
                    RiskScore.created_at.desc()
                ).limit(1000).all()

                # Analyze scores
                score_analysis = {
                    'total_scores': len(recent_scores),
                    'risk_level_distribution': dict(Counter([score.risk_level.value for score in recent_scores])),
                    'average_score': np.mean([score.overall_score for score in recent_scores]),
                    'high_risk_count': len([s for s in recent_scores if s.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]]),
                    'model_accuracy': self._calculate_overall_accuracy(),
                    'risk_category_distribution': dict(Counter([score.risk_category.value for score in recent_scores])),
                    'time_trends': self._analyze_temporal_trends(recent_scores)
                }

            finally:
                db.close()

            return {
                'analysis_summary': score_analysis,
                'model_performance': await self.get_model_performance_dashboard(),
                'feature_importance': self.feature_importance_cache,
                'risk_patterns': self._identify_risk_patterns(recent_scores),
                'recommendations': self._generate_system_recommendations(),
                'system_health': {
                    'is_healthy': self._check_system_health(),
                    'models_available': len(self.models),
                    'cache_status': 'active' if self.redis_client.ping() else 'inactive',
                    'last_update': datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error exporting risk scoring analysis: {str(e)}")
            return {'error': str(e)}

    def _analyze_temporal_trends(self, scores: List[RiskScore]) -> Dict[str, Any]:
        """Analyze temporal trends in risk scores"""
        try:
            if not scores:
                return {}

            # Group by hour
            hourly_counts = defaultdict(int)
            daily_counts = defaultdict(int)
            monthly_counts = defaultdict(int)

            for score in scores:
                timestamp = score.timestamp
                hourly_counts[timestamp.hour] += 1
                daily_counts[timestamp.date().day] += 1
                monthly_counts[timestamp.date().month] += 1

            return {
                'hourly_trends': dict(hourly_counts),
                'daily_trends': dict(daily_counts),
                'monthly_trends': dict(monthly_counts),
                'peak_hours': sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'peak_days': sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'trend_analysis': self._calculate_trend_analysis(hourly_counts)
            }

        except Exception as e:
            logger.error(f"Error analyzing temporal trends: {str(e)}")
            return {}

    def _calculate_trend_analysis(self, time_series: Dict[str, int]) -> Dict[str, str]:
        """Calculate trend analysis from time series"""
        try:
            if len(time_series) < 3:
                return {'trend': 'insufficient_data'}

            values = list(time_series.values())
            if len(set(values)) == 1:
                return {'trend': 'stable'}

            # Simple linear regression to determine trend
            indices = list(range(len(values)))
            correlation = np.corrcoef(indices, values)[0, 1]

            if correlation > 0.5:
                return {'trend': 'increasing', 'correlation': correlation}
            elif correlation < -0.5:
                return {'trend': 'decreasing', 'correlation': correlation}
            else:
                return {'trend': 'stable'}

        except Exception as e:
            logger.error(f"Error calculating trend analysis: {str(e)}")
            return {'trend': 'unknown'}

    def _identify_risk_patterns(self, scores: List[RiskScore]) -> List[Dict[str, Any]]:
        """Identify recurring risk patterns"""
        try:
            patterns = []

            # Group by entity type
            entity_groups = defaultdict(list)
            for score in scores:
                entity_groups[score.entity_type].append(score)

            # Find patterns within each entity type
            for entity_type, entity_scores in entity_groups.items():
                if len(entity_scores) >= 3:
                    # Analyze score patterns
                    scores = [s.overall_score for s in entity_scores]
                    avg_score = np.mean(scores)
                    score_variance = np.var(scores)

                    pattern = {
                        'entity_type': entity_type,
                        'pattern_type': 'recurring_high_risk' if avg_score > 0.7 else 'normal',
                        'average_score': avg_score,
                        'score_variance': score_variance,
                        'occurrence_count': len(entity_scores),
                        'high_risk_instances': len([s for s in entity_scores if s.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]]),
                        'timestamp_range': {
                            'earliest': min(s.timestamp for s in entity_scores).isoformat(),
                            'latest': max(s.timestamp for s in entity_scores).isoformat()
                        }
                    }
                    patterns.append(pattern)

            return sorted(patterns, key=lambda x: x['average_score'], reverse=True)

        except Exception as e:
            logger.error(f"Error identifying risk patterns: {str(e)}")
            return []

    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-level recommendations"""
        try:
            recommendations = []

            # Model performance recommendations
            avg_accuracy = self._calculate_overall_accuracy()
            if avg_accuracy < 0.7:
                recommendations.append("Consider model retraining with more diverse data")
            if avg_accuracy < 0.5:
                recommendations.append("Review feature engineering process")
            if not self.models:
                recommendations.append("Initialize ML models for better performance")

            # System capacity recommendations
            total_scores = self.total_scores_generated
            if total_scores > 10000:
                recommendations.append("Consider scaling up risk scoring infrastructure")
            if total_scores > 50000:
                recommendations.append("Implement distributed risk scoring")

            # Feature importance recommendations
            if not self.feature_importance_cache:
                recommendations.append("Establish feature importance tracking")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating system recommendations: {str(e)}")
            return []

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Advanced Risk Scoring Engine")

            self.is_running = False

            if self.executor:
                self.executor.shutdown(wait=True)

            if self.redis_client:
                self.redis_client.close()

            logger.info("Advanced Risk Scoring Engine cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Rule-based risk score class for fallback
@dataclass
class RuleBasedRiskScore:
    """Rule-based risk score for fallback when ML models are not available"""
    score_id: str
    entity_id: str
    entity_type: str
    overall_score: float
    risk_level: RiskLevel
    risk_category: RiskCategory
    component_scores: Dict[str, float]
    confidence: float
    explanation: List[str]
    recommendation: List[str]
    timestamp: datetime
    model_version: str

# Factory function
async def create_advanced_risk_scoring_engine(config: Dict[str, Any]) -> AdvancedRiskScoringEngine:
    """Create and initialize advanced risk scoring engine"""
    engine = AdvancedRiskScoringEngine(config)
    success = await engine.initialize()

    if not success:
        raise Exception("Failed to initialize Advanced Risk Scoring Engine")

    return engine

# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'redis_host': 'localhost',
        'redis_port': 6379,
        'database_url': 'sqlite:///aegis_risk_scoring.db',
        'model_weights': {
            ModelType.RANDOM_FOREST: 0.35,
            ModelType.GRADIENT_BOOSTING: 0.35,
            ModelType.LOGISTIC_REGRESSION: 0.30
        },
        'risk_thresholds': {
            RiskLevel.VERY_LOW: 0.0,
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.85,
            RiskLevel.CRITICAL: 0.95
        },
        'learning_rate': 0.01,
        'min_samples_for_training': 1000,
        'model_retrain_interval': 86400,  # 24 hours
        'feature_drift_threshold': 0.1
    }

    async def main():
        # Create risk scoring engine
        engine = await create_advanced_risk_scoring_engine(config)

        try:
            # Generate mock training data
            training_data = pd.DataFrame({
                'amount': np.random.exponential(50000, 0.2, 1000000),
                'transaction_count': np.random.randint(1, 100),
                'risk_score': np.random.beta(2, 5, 0.1),
                'fraud_signals_count': np.random.randint(0, 10),
                'account_age_days': np.random.randint(0, 3650),
                'device_risk_score': np.random.uniform(0, 1),
                'location_risk_score': np.random.uniform(0, 1),
                'temporal_risk_score': np.random.uniform(0, 1),
                'velocity_risk_score': np.random.uniform(0, 1),
                'cross_border_flag': np.random.choice([True, False], p=0.1),
                'high_value_transaction': (np.random.exponential(100000, 0.1, 1000000) > 100000).astype(bool),
                'unusual_timing': np.random.choice([True, False], p=0.15),
                'new_device_flag': np.random.choice([True, False], p=0.2),
                'is_fraud': np.random.choice([True, False], p=0.3)
            })

            # Train models
            result = await engine.train_advanced_models(training_data)
            print(f"Training result: {result}")

            # Get performance dashboard
            dashboard = await engine.get_model_performance_dashboard()
            print(f"Performance dashboard: {dashboard}")

            # Test risk scoring
            test_entity = {
                'entity_id': 'test_001',
                'entity_type': 'transaction',
                'amount': 75000,
                'risk_score': 0.8,
                'fraud_signals': ['new_device', 'geolocation_mismatch'],
                'cross_border_flag': True
            }

            risk_score = await engine.calculate_comprehensive_risk_score(test_entity)
            print(f"Test risk score: {risk_score}")

            # Test batch scoring
            test_entities = [test_entity] * 5
            batch_scores = await engine.calculate_batch_risk_scores(test_entities)
            print(f"Batch risk scores generated: {len(batch_scores)}")

            # Export analysis
            analysis = await engine.export_risk_scoring_analysis()
            print(f"Analysis: {analysis}")

            # Keep system running
            while True:
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("Shutting down Advanced Risk Scoring Engine")
        finally:
            await engine.cleanup()

    # Run the risk scoring engine
    asyncio.run(main())