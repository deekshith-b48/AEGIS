"""
Advanced Risk Scoring Engine
Multi-factor risk assessment with machine learning and real-time adaptation
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
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """
    Risk level classifications
    """
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class RiskFactorCategory(Enum):
    """
    Categories of risk factors
    """
    BEHAVIORAL = "behavioral"
    FINANCIAL = "financial"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"
    NETWORK = "network"
    HISTORICAL = "historical"
    CONTEXTUAL = "contextual"

@dataclass
class RiskFactor:
    """
    Individual risk factor
    """
    name: str
    category: RiskFactorCategory
    weight: float
    value: float
    description: str
    is_active: bool = True

@dataclass
class RiskAssessment:
    """
    Complete risk assessment result
    """
    entity_id: str
    entity_type: str
    overall_score: float
    risk_level: RiskLevel
    confidence: float
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    timestamp: datetime
    assessment_version: str = "2.0"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RiskThresholds:
    """
    Risk scoring thresholds
    """
    very_low: float = 0.1
    low: float = 0.3
    medium: float = 0.5
    high: float = 0.7
    very_high: float = 0.85
    critical: float = 0.95

class AdvancedRiskScoringEngine:
    """
    Advanced risk scoring engine with ML capabilities
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.risk_thresholds = RiskThresholds()
        self.risk_factors_config = {}
        self.learning_rate = 0.01
        self.model_version = "2.0"

        # Risk factor weights by category
        self.category_weights = {
            RiskFactorCategory.BEHAVIORAL: 0.25,
            RiskFactorCategory.FINANCIAL: 0.20,
            RiskFactorCategory.TEMPORAL: 0.15,
            RiskFactorCategory.GEOGRAPHIC: 0.15,
            RiskFactorCategory.NETWORK: 0.10,
            RiskFactorCategory.HISTORICAL: 0.10,
            RiskFactorCategory.CONTEXTUAL: 0.05
        }

    async def initialize(self) -> bool:
        """
        Initialize risk scoring engine
        """
        try:
            logger.info("[Risk Engine] Initializing advanced risk scoring engine...")

            # Load risk factor configurations
            await self._load_risk_factor_configurations()

            # Initialize ML models
            await self._initialize_ml_models()

            # Load trained models if available
            await self._load_trained_models()

            # Initialize feature importance tracking
            await self._initialize_feature_importance()

            logger.info("[Risk Engine] Risk scoring engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Risk Engine] Error initializing risk engine: {str(e)}")
            return False

    async def _load_risk_factor_configurations(self) -> None:
        """
        Load risk factor configurations
        """
        try:
            # Behavioral risk factors
            self.risk_factors_config['behavioral'] = [
                {
                    'name': 'unusual_transaction_pattern',
                    'weight': 0.8,
                    'description': 'Deviates from normal transaction patterns'
                },
                {
                    'name': 'multiple_failed_attempts',
                    'weight': 0.7,
                    'description': 'Multiple failed transaction attempts'
                },
                {
                    'name': 'rapid_succession_transactions',
                    'weight': 0.6,
                    'description': 'Multiple transactions in short time period'
                },
                {
                    'name': 'off_hours_activity',
                    'weight': 0.5,
                    'description': 'Activity during unusual hours'
                },
                {
                    'name': 'new_account_behavior',
                    'weight': 0.7,
                    'description': 'Suspicious behavior from new accounts'
                }
            ]

            # Financial risk factors
            self.risk_factors_config['financial'] = [
                {
                    'name': 'high_transaction_amount',
                    'weight': 0.6,
                    'description': 'Unusually high transaction amounts'
                },
                {
                    'name': 'round_amount_preference',
                    'weight': 0.4,
                    'description': 'Preference for round number amounts'
                },
                {
                    'name': 'amount_velocity',
                    'weight': 0.7,
                    'description': 'High velocity of money movement'
                },
                {
                    'name': 'unusual_payment_method',
                    'weight': 0.5,
                    'description': 'Use of unusual payment methods'
                },
                {
                    'name': 'cross_border_transactions',
                    'weight': 0.6,
                    'description': 'Frequent cross-border transactions'
                }
            ]

            # Temporal risk factors
            self.risk_factors_config['temporal'] = [
                {
                    'name': 'weekend_activity',
                    'weight': 0.3,
                    'description': 'Increased activity on weekends'
                },
                {
                    'name': 'late_night_transactions',
                    'weight': 0.5,
                    'description': 'Transactions during late night hours'
                },
                {
                    'name': 'holiday_season_spike',
                    'weight': 0.4,
                    'description': 'Unusual spike during holiday seasons'
                },
                {
                    'name': 'time_pattern_anomaly',
                    'weight': 0.6,
                    'description': 'Deviations from normal time patterns'
                }
            ]

            # Geographic risk factors
            self.risk_factors_config['geographic'] = [
                {
                    'name': 'high_risk_location',
                    'weight': 0.7,
                    'description': 'Transaction from high-risk geographic areas'
                },
                {
                    'name': 'location_velocity',
                    'weight': 0.8,
                    'description': 'Impossible travel between locations'
                },
                {
                    'name': 'foreign_ip_access',
                    'weight': 0.6,
                    'description': 'Access from foreign IP addresses'
                },
                {
                    'name': 'proxy_vpn_usage',
                    'weight': 0.5,
                    'description': 'Usage of proxy or VPN services'
                }
            ]

            # Network risk factors
            self.risk_factors_config['network'] = [
                {
                    'name': 'suspicious_network_connections',
                    'weight': 0.7,
                    'description': 'Connections to known malicious networks'
                },
                {
                    'name': 'device_fingerprint_anomaly',
                    'weight': 0.6,
                    'description': 'Unusual device fingerprint patterns'
                },
                {
                    'name': 'multiple_ip_addresses',
                    'weight': 0.5,
                    'description': 'Usage of multiple IP addresses'
                }
            ]

            # Historical risk factors
            self.risk_factors_config['historical'] = [
                {
                    'name': 'previous_fraud_history',
                    'weight': 0.9,
                    'description': 'History of fraudulent activities'
                },
                {
                    'name': 'chargeback_frequency',
                    'weight': 0.7,
                    'description': 'High frequency of chargebacks'
                },
                {
                    'name': 'complaint_history',
                    'weight': 0.6,
                    'description': 'History of complaints'
                }
            ]

            # Contextual risk factors
            self.risk_factors_config['contextual'] = [
                {
                    'name': 'current_scam_trends',
                    'weight': 0.5,
                    'description': 'Alignment with current scam trends'
                },
                {
                    'name': 'seasonal_patterns',
                    'weight': 0.3,
                    'description': 'Seasonal scam patterns'
                },
                {
                    'name': 'market_conditions',
                    'weight': 0.2,
                    'description': 'Market and economic conditions'
                }
            ]

            logger.info("[Risk Engine] Risk factor configurations loaded")

        except Exception as e:
            logger.error(f"[Risk Engine] Error loading risk factor configurations: {str(e)}")

    async def _initialize_ml_models(self) -> None:
        """
        Initialize machine learning models
        """
        try:
            # Initialize Random Forest for risk classification
            self.models['risk_classifier'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )

            # Initialize Isolation Forest for anomaly detection
            self.models['anomaly_detector'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            )

            # Initialize scaler
            self.scalers['feature_scaler'] = StandardScaler()

            logger.info("[Risk Engine] ML models initialized")

        except Exception as e:
            logger.error(f"[Risk Engine] Error initializing ML models: {str(e)}")

    async def _load_trained_models(self) -> None:
        """
        Load pre-trained models if available
        """
        try:
            model_dir = "models/risk_engine"
            if os.path.exists(model_dir):
                # Load risk classifier
                classifier_path = os.path.join(model_dir, "risk_classifier.joblib")
                if os.path.exists(classifier_path):
                    self.models['risk_classifier'] = joblib.load(classifier_path)
                    logger.info("[Risk Engine] Loaded trained risk classifier")

                # Load anomaly detector
                anomaly_path = os.path.join(model_dir, "anomaly_detector.joblib")
                if os.path.exists(anomaly_path):
                    self.models['anomaly_detector'] = joblib.load(anomaly_path)
                    logger.info("[Risk Engine] Loaded trained anomaly detector")

                # Load scaler
                scaler_path = os.path.join(model_dir, "feature_scaler.joblib")
                if os.path.exists(scaler_path):
                    self.scalers['feature_scaler'] = joblib.load(scaler_path)
                    logger.info("[Risk Engine] Loaded feature scaler")

        except Exception as e:
            logger.warning(f"[Risk Engine] Could not load trained models: {str(e)}")

    async def _initialize_feature_importance(self) -> None:
        """
        Initialize feature importance tracking
        """
        try:
            # Initialize feature importance dictionary
            self.feature_importance = {
                'behavioral': {},
                'financial': {},
                'temporal': {},
                'geographic': {},
                'network': {},
                'historical': {},
                'contextual': {}
            }

            # Set default importance scores
            for category in self.feature_importance:
                for factor_config in self.risk_factors_config.get(category, []):
                    factor_name = factor_config['name']
                    self.feature_importance[category][factor_name] = factor_config['weight']

            logger.info("[Risk Engine] Feature importance tracking initialized")

        except Exception as e:
            logger.error(f"[Risk Engine] Error initializing feature importance: {str(e)}")

    async def assess_risk(self, entity_id: str, entity_type: str,
                        context_data: Dict[str, Any],
                        historical_data: Dict[str, Any] = None) -> RiskAssessment:
        """
        Perform comprehensive risk assessment
        """
        try:
            logger.debug(f"[Risk Engine] Assessing risk for {entity_type} {entity_id}")

            # Extract risk factors
            risk_factors = await self._extract_risk_factors(
                entity_id, entity_type, context_data, historical_data
            )

            # Calculate category scores
            category_scores = await self._calculate_category_scores(risk_factors)

            # Apply ML models for enhanced scoring
            ml_enhanced_score = await self._apply_ml_scoring(
                entity_id, entity_type, context_data, risk_factors
            )

            # Calculate overall risk score
            overall_score = await self._calculate_overall_risk_score(
                category_scores, ml_enhanced_score
            )

            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)

            # Calculate confidence
            confidence = await self._calculate_confidence(risk_factors, overall_score)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                risk_level, risk_factors, context_data
            )

            # Create risk assessment
            assessment = RiskAssessment(
                entity_id=entity_id,
                entity_type=entity_type,
                overall_score=overall_score,
                risk_level=risk_level,
                confidence=confidence,
                risk_factors=risk_factors,
                recommendations=recommendations,
                timestamp=datetime.utcnow(),
                metadata={
                    'category_scores': category_scores,
                    'ml_enhanced_score': ml_enhanced_score,
                    'assessment_method': 'advanced_ml_enhanced'
                }
            )

            # Store assessment for learning
            await self._store_risk_assessment(assessment)

            return assessment

        except Exception as e:
            logger.error(f"[Risk Engine] Error assessing risk: {str(e)}")
            # Return default low-risk assessment
            return RiskAssessment(
                entity_id=entity_id,
                entity_type=entity_type,
                overall_score=0.1,
                risk_level=RiskLevel.VERY_LOW,
                confidence=0.5,
                risk_factors=[],
                recommendations=["Unable to complete risk assessment"],
                timestamp=datetime.utcnow()
            )

    async def _extract_risk_factors(self, entity_id: str, entity_type: str,
                                  context_data: Dict[str, Any],
                                  historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract risk factors from context and historical data
        """
        try:
            risk_factors = []

            # Extract behavioral factors
            behavioral_factors = await self._extract_behavioral_factors(context_data, historical_data)
            risk_factors.extend(behavioral_factors)

            # Extract financial factors
            financial_factors = await self._extract_financial_factors(context_data, historical_data)
            risk_factors.extend(financial_factors)

            # Extract temporal factors
            temporal_factors = await self._extract_temporal_factors(context_data, historical_data)
            risk_factors.extend(temporal_factors)

            # Extract geographic factors
            geographic_factors = await self._extract_geographic_factors(context_data, historical_data)
            risk_factors.extend(geographic_factors)

            # Extract network factors
            network_factors = await self._extract_network_factors(context_data, historical_data)
            risk_factors.extend(network_factors)

            # Extract historical factors
            historical_factors = await self._extract_historical_factors(historical_data)
            risk_factors.extend(historical_factors)

            # Extract contextual factors
            contextual_factors = await self._extract_contextual_factors(context_data, historical_data)
            risk_factors.extend(contextual_factors)

            return risk_factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting risk factors: {str(e)}")
            return []

    async def _extract_behavioral_factors(self, context_data: Dict[str, Any],
                                        historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract behavioral risk factors
        """
        try:
            factors = []

            # Unusual transaction pattern
            transaction_pattern = context_data.get('transaction_pattern', {})
            if transaction_pattern.get('is_unusual', False):
                factors.append(RiskFactor(
                    name='unusual_transaction_pattern',
                    category=RiskFactorCategory.BEHAVIORAL,
                    weight=0.8,
                    value=0.8,
                    description='Unusual transaction pattern detected'
                ))

            # Multiple failed attempts
            failed_attempts = context_data.get('failed_attempts', 0)
            if failed_attempts > 2:
                factors.append(RiskFactor(
                    name='multiple_failed_attempts',
                    category=RiskFactorCategory.BEHAVIORAL,
                    weight=0.7,
                    value=min(failed_attempts / 10, 1.0),
                    description=f'Multiple failed attempts: {failed_attempts}'
                ))

            # Rapid succession transactions
            rapid_transactions = context_data.get('rapid_succession_count', 0)
            if rapid_transactions > 5:
                factors.append(RiskFactor(
                    name='rapid_succession_transactions',
                    category=RiskFactorCategory.BEHAVIORAL,
                    weight=0.6,
                    value=min(rapid_transactions / 20, 1.0),
                    description=f'High transaction velocity: {rapid_transactions} in short period'
                ))

            # Off-hours activity
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:
                factors.append(RiskFactor(
                    name='off_hours_activity',
                    category=RiskFactorCategory.BEHAVIORAL,
                    weight=0.5,
                    value=0.6,
                    description='Activity during off-hours'
                ))

            # New account behavior
            account_age = context_data.get('account_age_days', 0)
            if account_age < 30:
                factors.append(RiskFactor(
                    name='new_account_behavior',
                    category=RiskFactorCategory.BEHAVIORAL,
                    weight=0.7,
                    value=0.8,
                    description=f'New account: {account_age} days old'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting behavioral factors: {str(e)}")
            return []

    async def _extract_financial_factors(self, context_data: Dict[str, Any],
                                      historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract financial risk factors
        """
        try:
            factors = []

            # High transaction amount
            amount = context_data.get('amount', 0)
            if amount > 50000:
                factors.append(RiskFactor(
                    name='high_transaction_amount',
                    category=RiskFactorCategory.FINANCIAL,
                    weight=0.6,
                    value=min(amount / 500000, 1.0),
                    description=f'High transaction amount: ₹{amount:,}'
                ))

            # Round amount preference
            if amount > 0 and amount % 1000 == 0:
                factors.append(RiskFactor(
                    name='round_amount_preference',
                    category=RiskFactorCategory.FINANCIAL,
                    weight=0.4,
                    value=0.7,
                    description='Round number amount preference'
                ))

            # Amount velocity
            total_amount_24h = context_data.get('total_amount_24h', 0)
            if total_amount_24h > 100000:
                factors.append(RiskFactor(
                    name='amount_velocity',
                    category=RiskFactorCategory.FINANCIAL,
                    weight=0.7,
                    value=min(total_amount_24h / 1000000, 1.0),
                    description=f'High amount velocity: ₹{total_amount_24h:,} in 24h'
                ))

            # Unusual payment method
            payment_method = context_data.get('payment_method', '')
            if payment_method in ['cryptocurrency', 'gift_card', 'prepaid_card']:
                factors.append(RiskFactor(
                    name='unusual_payment_method',
                    category=RiskFactorCategory.FINANCIAL,
                    weight=0.5,
                    value=0.6,
                    description=f'Unusual payment method: {payment_method}'
                ))

            # Cross-border transactions
            cross_border_count = context_data.get('cross_border_count_24h', 0)
            if cross_border_count > 0:
                factors.append(RiskFactor(
                    name='cross_border_transactions',
                    category=RiskFactorCategory.FINANCIAL,
                    weight=0.6,
                    value=min(cross_border_count / 5, 1.0),
                    description=f'Cross-border transactions: {cross_border_count}'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting financial factors: {str(e)}")
            return []

    async def _extract_temporal_factors(self, context_data: Dict[str, Any],
                                     historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract temporal risk factors
        """
        try:
            factors = []

            current_time = datetime.now()

            # Weekend activity
            if current_time.weekday() >= 5:  # Saturday or Sunday
                factors.append(RiskFactor(
                    name='weekend_activity',
                    category=RiskFactorCategory.TEMPORAL,
                    weight=0.3,
                    value=0.4,
                    description='Weekend activity'
                ))

            # Late night transactions
            if current_time.hour >= 22 or current_time.hour <= 5:
                factors.append(RiskFactor(
                    name='late_night_transactions',
                    category=RiskFactorCategory.TEMPORAL,
                    weight=0.5,
                    value=0.6,
                    description='Late night transaction activity'
                ))

            # Holiday season spike
            month = current_time.month
            if month in [11, 12]:  # November, December (holiday season)
                factors.append(RiskFactor(
                    name='holiday_season_spike',
                    category=RiskFactorCategory.TEMPORAL,
                    weight=0.4,
                    value=0.5,
                    description='Holiday season activity'
                ))

            # Time pattern anomaly (would need historical data)
            if historical_data:
                avg_hourly_activity = historical_data.get('avg_hourly_activity', {})
                current_hour_activity = avg_hourly_activity.get(current_time.hour, 0)
                if current_hour_activity > 0:
                    current_activity = context_data.get('current_hour_activity', 0)
                    if current_activity > current_hour_activity * 2:
                        factors.append(RiskFactor(
                            name='time_pattern_anomaly',
                            category=RiskFactorCategory.TEMPORAL,
                            weight=0.6,
                            value=0.7,
                            description='Significant deviation from normal time pattern'
                        ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting temporal factors: {str(e)}")
            return []

    async def _extract_geographic_factors(self, context_data: Dict[str, Any],
                                        historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract geographic risk factors
        """
        try:
            factors = []

            location = context_data.get('location', {})

            # High-risk location
            high_risk_locations = [
                (28.6139, 77.2090),  # Delhi
                (19.0760, 72.8777),  # Mumbai
                (12.9716, 77.5946),  # Bangalore
            ]

            lat, lon = location.get('lat'), location.get('lon')
            if lat and lon:
                for risk_lat, risk_lon in high_risk_locations:
                    distance = self._calculate_distance(lat, lon, risk_lat, risk_lon)
                    if distance < 50:  # Within 50km
                        factors.append(RiskFactor(
                            name='high_risk_location',
                            category=RiskFactorCategory.GEOGRAPHIC,
                            weight=0.7,
                            value=0.6,
                            description='Transaction from high-risk geographic area'
                        ))
                        break

                # Location velocity (impossible travel)
                if historical_data and 'previous_locations' in historical_data:
                    for prev_loc in historical_data['previous_locations'][-3:]:  # Last 3 locations
                        prev_time = prev_loc.get('timestamp')
                        if prev_time:
                            time_diff = (current_time - datetime.fromisoformat(prev_time)).total_seconds()
                            distance = self._calculate_distance(
                                lat, lon, prev_loc.get('lat'), prev_loc.get('lon')
                            )
                            # If traveled more than 500km in less than 1 hour
                            if distance > 500 and time_diff < 3600:
                                factors.append(RiskFactor(
                                    name='location_velocity',
                                    category=RiskFactorCategory.GEOGRAPHIC,
                                    weight=0.8,
                                    value=0.9,
                                    description='Impossible travel velocity detected'
                                ))
                                break

            # Foreign IP access
            ip_country = context_data.get('ip_country', '')
            if ip_country and ip_country.upper() != 'IN':
                factors.append(RiskFactor(
                    name='foreign_ip_access',
                    category=RiskFactorCategory.GEOGRAPHIC,
                    weight=0.6,
                    value=0.7,
                    description=f'Access from foreign IP: {ip_country}'
                ))

            # Proxy/VPN usage
            is_proxy = context_data.get('is_proxy_or_vpn', False)
            if is_proxy:
                factors.append(RiskFactor(
                    name='proxy_vpn_usage',
                    category=RiskFactorCategory.GEOGRAPHIC,
                    weight=0.5,
                    value=0.6,
                    description='Proxy or VPN usage detected'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting geographic factors: {str(e)}")
            return []

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two geographic coordinates in kilometers
        """
        try:
            from math import radians, cos, sin, asin, sqrt

            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth's radius in kilometers
            return c * r
        except Exception:
            return 0

    async def _extract_network_factors(self, context_data: Dict[str, Any],
                                     historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract network risk factors
        """
        try:
            factors = []

            # Suspicious network connections
            suspicious_ips = context_data.get('suspicious_network_connections', [])
            if suspicious_ips:
                factors.append(RiskFactor(
                    name='suspicious_network_connections',
                    category=RiskFactorCategory.NETWORK,
                    weight=0.7,
                    value=min(len(suspicious_ips) / 5, 1.0),
                    description=f'Suspicious network connections: {len(suspicious_ips)}'
                ))

            # Device fingerprint anomaly
            device_fingerprint = context_data.get('device_fingerprint', {})
            if historical_data and 'device_fingerprints' in historical_data:
                known_fingerprints = historical_data['device_fingerprints']
                current_fingerprint = device_fingerprint.get('hash', '')
                if current_fingerprint not in known_fingerprints:
                    factors.append(RiskFactor(
                        name='device_fingerprint_anomaly',
                        category=RiskFactorCategory.NETWORK,
                        weight=0.6,
                        value=0.7,
                        description='Unusual device fingerprint detected'
                    ))

            # Multiple IP addresses
            recent_ips = context_data.get('recent_ip_addresses', [])
            if len(set(recent_ips)) > 3:
                factors.append(RiskFactor(
                    name='multiple_ip_addresses',
                    category=RiskFactorCategory.NETWORK,
                    weight=0.5,
                    value=min(len(set(recent_ips)) / 10, 1.0),
                    description=f'Multiple IP addresses used: {len(set(recent_ips))}'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting network factors: {str(e)}")
            return []

    async def _extract_historical_factors(self, historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract historical risk factors
        """
        try:
            factors = []

            if not historical_data:
                return factors

            # Previous fraud history
            fraud_history = historical_data.get('fraud_history', {})
            if fraud_history.get('has_fraud', False):
                factors.append(RiskFactor(
                    name='previous_fraud_history',
                    category=RiskFactorCategory.HISTORICAL,
                    weight=0.9,
                    value=0.9,
                    description='Previous fraud history detected'
                ))

            # Chargeback frequency
            chargeback_count = historical_data.get('chargeback_count_30d', 0)
            if chargeback_count > 2:
                factors.append(RiskFactor(
                    name='chargeback_frequency',
                    category=RiskFactorCategory.HISTORICAL,
                    weight=0.7,
                    value=min(chargeback_count / 10, 1.0),
                    description=f'High chargeback frequency: {chargeback_count} in 30 days'
                ))

            # Complaint history
            complaint_count = historical_data.get('complaint_count', 0)
            if complaint_count > 0:
                factors.append(RiskFactor(
                    name='complaint_history',
                    category=RiskFactorCategory.HISTORICAL,
                    weight=0.6,
                    value=min(complaint_count / 5, 1.0),
                    description=f'Previous complaints: {complaint_count}'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting historical factors: {str(e)}")
            return []

    async def _extract_contextual_factors(self, context_data: Dict[str, Any],
                                       historical_data: Dict[str, Any] = None) -> List[RiskFactor]:
        """
        Extract contextual risk factors
        """
        try:
            factors = []

            # Current scam trends
            current_scam_type = context_data.get('scam_type', '')
            trending_scams = ['UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION']
            if current_scam_type in trending_scams:
                factors.append(RiskFactor(
                    name='current_scam_trends',
                    category=RiskFactorCategory.CONTEXTUAL,
                    weight=0.5,
                    value=0.6,
                    description=f'Alignment with current scam trend: {current_scam_type}'
                ))

            # Seasonal patterns
            current_month = datetime.now().month
            seasonal_scams = {
                11: 'FESTIVE_SCAM',    # Diwali season
                12: 'HOLIDAY_SCAM',    # Christmas/New Year
                3: 'FESTIVE_SCAM',     # Holi season
                10: 'FESTIVE_SCAM'     # Durga Puja/Dussehra
            }
            if current_month in seasonal_scams:
                factors.append(RiskFactor(
                    name='seasonal_patterns',
                    category=RiskFactorCategory.CONTEXTUAL,
                    weight=0.3,
                    value=0.4,
                    description=f'Seasonal scam pattern: {seasonal_scams[current_month]}'
                ))

            return factors

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting contextual factors: {str(e)}")
            return []

    async def _calculate_category_scores(self, risk_factors: List[RiskFactor]) -> Dict[str, float]:
        """
        Calculate risk scores for each category
        """
        try:
            category_scores = {}
            category_factors = {}

            # Group factors by category
            for factor in risk_factors:
                category = factor.category.value
                if category not in category_factors:
                    category_factors[category] = []
                category_factors[category].append(factor)

            # Calculate scores for each category
            for category, factors in category_factors.items():
                if not factors:
                    category_scores[category] = 0.0
                    continue

                # Weighted average of factor values
                weighted_sum = sum(f.value * f.weight for f in factors)
                weight_sum = sum(f.weight for f in factors)

                if weight_sum > 0:
                    category_score = weighted_sum / weight_sum
                else:
                    category_score = 0.0

                # Apply category weight
                category_weight = self.category_weights.get(RiskFactorCategory(category), 0.1)
                category_scores[category] = category_score * category_weight

            return category_scores

        except Exception as e:
            logger.error(f"[Risk Engine] Error calculating category scores: {str(e)}")
            return {}

    async def _apply_ml_scoring(self, entity_id: str, entity_type: str,
                              context_data: Dict[str, Any],
                              risk_factors: List[RiskFactor]) -> float:
        """
        Apply machine learning models for enhanced scoring
        """
        try:
            # Extract features for ML models
            features = await self._extract_ml_features(context_data, risk_factors)

            if len(features) == 0:
                return 0.5  # Default neutral score

            # Prepare feature vector
            feature_vector = np.array(list(features.values())).reshape(1, -1)

            # Apply scaling if scaler is available
            if 'feature_scaler' in self.scalers:
                feature_vector = self.scalers['feature_scaler'].transform(feature_vector)

            # Apply risk classifier if available and trained
            if 'risk_classifier' in self.models and hasattr(self.models['risk_classifier'], 'feature_importances_'):
                try:
                    risk_proba = self.models['risk_classifier'].predict_proba(feature_vector)[0]
                    if len(risk_proba) > 1:
                        ml_score = risk_proba[1]  # Probability of high risk
                    else:
                        ml_score = risk_proba[0]
                except Exception:
                    ml_score = 0.5
            else:
                ml_score = 0.5

            # Apply anomaly detection if available
            if 'anomaly_detector' in self.models:
                try:
                    anomaly_score = self.models['anomaly_detector'].decision_function(feature_vector)[0]
                    # Normalize anomaly score to [0, 1]
                    anomaly_score_normalized = max(0, min(1, (anomaly_score + 0.5)))
                    ml_score = (ml_score + anomaly_score_normalized) / 2
                except Exception:
                    pass  # Keep original ml_score

            return ml_score

        except Exception as e:
            logger.error(f"[Risk Engine] Error applying ML scoring: {str(e)}")
            return 0.5

    async def _extract_ml_features(self, context_data: Dict[str, Any],
                                risk_factors: List[RiskFactor]) -> Dict[str, float]:
        """
        Extract features for machine learning models
        """
        try:
            features = {}

            # Numerical features
            features['amount'] = float(context_data.get('amount', 0))
            features['failed_attempts'] = float(context_data.get('failed_attempts', 0))
            features['rapid_succession_count'] = float(context_data.get('rapid_succession_count', 0))
            features['account_age_days'] = float(context_data.get('account_age_days', 0))
            features['total_amount_24h'] = float(context_data.get('total_amount_24h', 0))
            features['cross_border_count_24h'] = float(context_data.get('cross_border_count_24h', 0))
            features['current_hour'] = float(datetime.now().hour)
            features['current_day_of_week'] = float(datetime.now().weekday())

            # Location features
            location = context_data.get('location', {})
            features['latitude'] = float(location.get('lat', 0))
            features['longitude'] = float(location.get('lon', 0))

            # Risk factor features
            category_scores = await self._calculate_category_scores(risk_factors)
            for category, score in category_scores.items():
                features[f'category_{category}'] = score

            # Network features
            features['suspicious_connections_count'] = float(len(context_data.get('suspicious_network_connections', [])))
            features['recent_ip_count'] = float(len(set(context_data.get('recent_ip_addresses', []))))

            # Historical features
            if 'historical_data' in context_data:
                hist_data = context_data['historical_data']
                features['historical_fraud_count'] = float(hist_data.get('fraud_count', 0))
                features['historical_complaint_count'] = float(hist_data.get('complaint_count', 0))
                features['historical_chargeback_count'] = float(hist_data.get('chargeback_count_30d', 0))
            else:
                features['historical_fraud_count'] = 0.0
                features['historical_complaint_count'] = 0.0
                features['historical_chargeback_count'] = 0.0

            return features

        except Exception as e:
            logger.error(f"[Risk Engine] Error extracting ML features: {str(e)}")
            return {}

    async def _calculate_overall_risk_score(self, category_scores: Dict[str, float],
                                          ml_enhanced_score: float) -> float:
        """
        Calculate overall risk score from category scores and ML enhancement
        """
        try:
            # Calculate weighted sum of category scores
            category_total = sum(category_scores.values())
            category_weights_sum = sum(self.category_weights.values())

            if category_weights_sum > 0:
                category_normalized_score = category_total / category_weights_sum
            else:
                category_normalized_score = 0.0

            # Combine with ML-enhanced score
            # Weight: 70% category-based, 30% ML-enhanced
            overall_score = (category_normalized_score * 0.7) + (ml_enhanced_score * 0.3)

            # Ensure score is in [0, 1] range
            overall_score = max(0.0, min(1.0, overall_score))

            return overall_score

        except Exception as e:
            logger.error(f"[Risk Engine] Error calculating overall risk score: {str(e)}")
            return 0.5

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """
        Determine risk level from score
        """
        if score >= self.risk_thresholds.critical:
            return RiskLevel.CRITICAL
        elif score >= self.risk_thresholds.very_high:
            return RiskLevel.VERY_HIGH
        elif score >= self.risk_thresholds.high:
            return RiskLevel.HIGH
        elif score >= self.risk_thresholds.medium:
            return RiskLevel.MEDIUM
        elif score >= self.risk_thresholds.low:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    async def _calculate_confidence(self, risk_factors: List[RiskFactor],
                                  overall_score: float) -> float:
        """
        Calculate confidence in risk assessment
        """
        try:
            if not risk_factors:
                return 0.3  # Low confidence with no factors

            # Base confidence from number of factors
            factor_confidence = min(len(risk_factors) / 10, 1.0)

            # Confidence from score extremity
            score_confidence = abs(overall_score - 0.5) * 2  # Higher confidence for extreme scores

            # Factor weight consistency
            weight_variance = np.var([f.weight for f in risk_factors])
            consistency_confidence = 1.0 - min(weight_variance, 1.0)

            # Combine confidences
            overall_confidence = (factor_confidence * 0.4 + score_confidence * 0.4 + consistency_confidence * 0.2)

            return max(0.1, min(1.0, overall_confidence))

        except Exception as e:
            logger.error(f"[Risk Engine] Error calculating confidence: {str(e)}")
            return 0.5

    async def _generate_recommendations(self, risk_level: RiskLevel,
                                      risk_factors: List[RiskFactor],
                                      context_data: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on risk assessment
        """
        try:
            recommendations = []

            if risk_level in [RiskLevel.CRITICAL, RiskLevel.VERY_HIGH]:
                recommendations.extend([
                    "IMMEDIATE ACTION REQUIRED: Block transaction/account",
                    "Initiate emergency response protocol",
                    "Contact law enforcement immediately",
                    "Document all evidence for investigation"
                ])

            elif risk_level == RiskLevel.HIGH:
                recommendations.extend([
                    "Enhanced monitoring required",
                    "Request additional verification",
                    "Consider temporary transaction limits",
                    "Alert fraud investigation team"
                ])

            elif risk_level == RiskLevel.MEDIUM:
                recommendations.extend([
                    "Increased monitoring recommended",
                    "Verify user identity through additional channels",
                    "Review transaction history for patterns",
                    "Set up alerts for future transactions"
                ])

            else:
                recommendations.extend([
                    "Standard monitoring procedures",
                    "Continue normal operations",
                    "Periodic review recommended"
                ])

            # Add specific recommendations based on risk factors
            for factor in risk_factors:
                if factor.name == 'high_transaction_amount':
                    recommendations.append("Verify large transaction legitimacy")
                elif factor.name == 'foreign_ip_access':
                    recommendations.append("Verify user location and identity")
                elif factor.name == 'multiple_failed_attempts':
                    recommendations.append("Implement temporary account lock")
                elif factor.name == 'new_account_behavior':
                    recommendations.append("Enhanced verification for new accounts")

            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    unique_recommendations.append(rec)
                    seen.add(rec)

            return unique_recommendations[:10]  # Limit to top 10 recommendations

        except Exception as e:
            logger.error(f"[Risk Engine] Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations"]

    async def _store_risk_assessment(self, assessment: RiskAssessment) -> None:
        """
        Store risk assessment for learning and auditing
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO risk_assessments (
                        entity_id, entity_type, overall_score, risk_level,
                        confidence, risk_factors, recommendations, timestamp,
                        assessment_version, metadata
                    ) VALUES (
                        :entity_id, :entity_type, :overall_score, :risk_level,
                        :confidence, :risk_factors, :recommendations, :timestamp,
                        :assessment_version, :metadata
                    )
                """)

                db.execute(query, {
                    'entity_id': assessment.entity_id,
                    'entity_type': assessment.entity_type,
                    'overall_score': assessment.overall_score,
                    'risk_level': assessment.risk_level.value,
                    'confidence': assessment.confidence,
                    'risk_factors': json.dumps([asdict(f) for f in assessment.risk_factors]),
                    'recommendations': json.dumps(assessment.recommendations),
                    'timestamp': assessment.timestamp,
                    'assessment_version': assessment.assessment_version,
                    'metadata': json.dumps(assessment.metadata)
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Risk Engine] Error storing risk assessment: {str(e)}")

    async def batch_assess_risk(self, entities: List[Dict[str, Any]]) -> List[RiskAssessment]:
        """
        Perform batch risk assessment
        """
        try:
            assessments = []

            for entity_data in entities:
                entity_id = entity_data.get('entity_id')
                entity_type = entity_data.get('entity_type', 'unknown')
                context_data = entity_data.get('context_data', {})
                historical_data = entity_data.get('historical_data')

                if entity_id:
                    assessment = await self.assess_risk(
                        entity_id, entity_type, context_data, historical_data
                    )
                    assessments.append(assessment)

            return assessments

        except Exception as e:
            logger.error(f"[Risk Engine] Error in batch risk assessment: {str(e)}")
            return []

    async def update_model_feedback(self, entity_id: str, actual_outcome: str,
                                  feedback_data: Dict[str, Any]) -> bool:
        """
        Update models based on feedback
        """
        try:
            # Store feedback for model retraining
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO model_feedback (
                        entity_id, actual_outcome, feedback_data, timestamp,
                        model_version
                    ) VALUES (
                        :entity_id, :actual_outcome, :feedback_data, :timestamp,
                        :model_version
                    )
                """)

                db.execute(query, {
                    'entity_id': entity_id,
                    'actual_outcome': actual_outcome,
                    'feedback_data': json.dumps(feedback_data),
                    'timestamp': datetime.utcnow(),
                    'model_version': self.model_version
                })

                db.commit()

            # Update feature importance based on feedback
            await self._update_feature_importance(feedback_data)

            logger.info(f"[Risk Engine] Model feedback updated for {entity_id}")
            return True

        except Exception as e:
            logger.error(f"[Risk Engine] Error updating model feedback: {str(e)}")
            return False

    async def _update_feature_importance(self, feedback_data: Dict[str, Any]) -> None:
        """
        Update feature importance based on feedback
        """
        try:
            predicted_factors = feedback_data.get('predicted_factors', [])
            actual_risk_factors = feedback_data.get('actual_risk_factors', [])

            # Simple importance update (more sophisticated methods would be used in production)
            learning_rate = self.learning_rate

            for category in self.feature_importance:
                for factor_name in self.feature_importance[category]:
                    # Adjust importance based on prediction accuracy
                    if factor_name in predicted_factors and factor_name in actual_risk_factors:
                        # Factor was correctly predicted
                        self.feature_importance[category][factor_name] *= (1 + learning_rate * 0.1)
                    elif factor_name in predicted_factors and factor_name not in actual_risk_factors:
                        # False positive
                        self.feature_importance[category][factor_name] *= (1 - learning_rate * 0.05)
                    elif factor_name not in predicted_factors and factor_name in actual_risk_factors:
                        # False negative
                        self.feature_importance[category][factor_name] *= (1 + learning_rate * 0.15)

                    # Keep importance in reasonable range
                    self.feature_importance[category][factor_name] = max(0.1, min(1.0, self.feature_importance[category][factor_name]))

        except Exception as e:
            logger.error(f"[Risk Engine] Error updating feature importance: {str(e)}")

    async def get_risk_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get risk assessment statistics
        """
        try:
            with SessionLocal() as db:
                result = db.execute(text("""
                    SELECT
                        risk_level,
                        COUNT(*) as assessment_count,
                        AVG(overall_score) as avg_score,
                        AVG(confidence) as avg_confidence
                    FROM risk_assessments
                    WHERE timestamp >= NOW() - INTERVAL ':days_back days'
                    GROUP BY risk_level
                    ORDER BY assessment_count DESC
                """), {'days_back': days_back}).fetchall()

                statistics = {
                    'total_assessments': sum(row.assessment_count for row in result),
                    'risk_level_distribution': {},
                    'average_scores': {},
                    'period_days': days_back
                }

                for row in result:
                    statistics['risk_level_distribution'][row.risk_level] = row.assessment_count
                    statistics['average_scores'][row.risk_level] = float(row.avg_score) if row.avg_score else 0

                # Get feature importance statistics
                statistics['feature_importance'] = self.feature_importance

                return statistics

        except Exception as e:
            logger.error(f"[Risk Engine] Error getting risk statistics: {str(e)}")
            return {}

    async def get_engine_status(self) -> Dict[str, Any]:
        """
        Get risk engine status
        """
        try:
            return {
                'models_loaded': list(self.models.keys()),
                'scalers_loaded': list(self.scalers.keys()),
                'risk_categories': list(RiskFactorCategory),
                'risk_levels': list(RiskLevel),
                'category_weights': {cat.value: weight for cat, weight in self.category_weights.items()},
                'feature_importance_categories': list(self.feature_importance.keys()),
                'model_version': self.model_version,
                'learning_rate': self.learning_rate
            }

        except Exception as e:
            logger.error(f"[Risk Engine] Error getting engine status: {str(e)}")
            return {'error': str(e)}

# Global risk scoring engine instance
advanced_risk_scoring_engine = AdvancedRiskScoringEngine()