"""
CFCFRMS (Cyber Fraud Detection and Resolution Management System) Integration
Advanced Bank Transaction Logs Monitoring for AEGIS

Implements real-time bank transaction monitoring with:
- Fraud signal detection
- Transaction pattern analysis
- Account behavior monitoring
- Cross-bank intelligence sharing
- Privacy-preserving data aggregation
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, ARRAY, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSON
import redis
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class TransactionType(Enum):
    """Transaction types for monitoring"""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    UPI_TRANSACTION = "upi_transaction"
    ATM_WITHDRAWAL = "atm_withdrawal"
    POS_TRANSACTION = "pos_transaction"
    ONLINE_PAYMENT = "online_payment"

class FraudSignalType(Enum):
    """Types of fraud signals"""
    UNUSUAL_AMOUNT = "unusual_amount"
    RAPID_TRANSACTIONS = "rapid_transactions"
    NEW_DEVICE = "new_device"
    LOCATION_ANOMALY = "location_anomaly"
    ACCOUNT_TAKEOVER = "account_takeover"
    SYNCHRONOUS_ACTIVITY = "synchronous_activity"
    CROSS_BANK_PATTERN = "cross_bank_pattern"
    TIME_ANOMALY = "time_anomaly"
    AMOUNT_ANOMALY = "amount_anomaly"
    FREQUENCY_ANOMALY = "frequency_anomaly"

class RiskLevel(Enum):
    """Risk classification levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BankTransaction:
    """Bank transaction data structure"""
    transaction_id: str
    account_id: str
    bank_code: str
    transaction_type: TransactionType
    amount: float
    currency: str
    timestamp: datetime
    merchant_id: Optional[str]
    merchant_name: Optional[str]
    merchant_category: Optional[str]
    location_lat: Optional[float]
    location_lon: Optional[float]
    device_id: Optional[str]
    ip_address: Optional[str]
    channel: str  # online, mobile, atm, pos
    upi_id: Optional[str]
    beneficiary_account: Optional[str]
    beneficiary_name: Optional[str]
    reference_number: Optional[str]
    status: str
    risk_score: float
    fraud_signals: List[str]

@dataclass
class FraudAlert:
    """Fraud alert data structure"""
    alert_id: str
    account_id: str
    bank_code: str
    alert_type: FraudSignalType
    risk_level: RiskLevel
    confidence_score: float
    description: str
    affected_transactions: List[str]
    detection_timestamp: datetime
    location_data: Dict[str, Any]
    recommended_action: str
    escalation_required: bool

@dataclass
class AccountBehaviorProfile:
    """Account behavior profile for anomaly detection"""
    account_id: str
    bank_code: str
    avg_transaction_amount: float
    transaction_frequency: float
    preferred_merchants: List[str]
    preferred_locations: List[Dict[str, float]]
    active_hours: List[int]
    device_fingerprints: List[str]
    ip_ranges: List[str]
    upi_counterparties: List[str]
    typical_transaction_patterns: Dict[str, Any]
    last_updated: datetime
    risk_baseline: float

class BankTransaction(Base):
    """SQLAlchemy model for bank transactions"""
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String, nullable=False, unique=True, index=True)
    account_id_hash = Column(String, nullable=False, index=True)  # Hashed for privacy
    bank_code = Column(String, nullable=False, index=True)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='INR')
    timestamp = Column(DateTime, nullable=False, index=True)
    merchant_id = Column(String, nullable=True)
    merchant_category = Column(String, nullable=True)
    location_cluster = Column(String, nullable=True, index=True)
    device_fingerprint_hash = Column(String, nullable=True)
    ip_address_hash = Column(String, nullable=True)
    channel = Column(String, nullable=False)
    upi_id_hash = Column(String, nullable=True)
    beneficiary_account_hash = Column(String, nullable=True)
    status = Column(String, nullable=False, default='completed')
    risk_score = Column(Float, nullable=False, default=0.0)
    fraud_signals = Column(ARRAY(String), nullable=True, default=[])
    is_suspicious = Column(Boolean, nullable=False, default=False)
    is_flagged_for_review = Column(Boolean, nullable=False, default=False)
    processing_timestamp = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String, nullable=True, index=True)

class FraudAlertRecord(Base):
    """SQLAlchemy model for fraud alerts"""
    __tablename__ = "fraud_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String, nullable=False, unique=True, index=True)
    account_id_hash = Column(String, nullable=False, index=True)
    bank_code = Column(String, nullable=False, index=True)
    alert_type = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    affected_transactions = Column(ARRAY(String), nullable=True)
    detection_timestamp = Column(DateTime, nullable=False, index=True)
    location_data = Column(JSON, nullable=True)
    recommended_action = Column(String, nullable=False)
    escalation_required = Column(Boolean, nullable=False, default=False)
    is_acknowledged = Column(Boolean, nullable=False, default=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccountBehaviorProfileRecord(Base):
    """SQLAlchemy model for account behavior profiles"""
    __tablename__ = "account_behavior_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id_hash = Column(String, nullable=False, unique=True, index=True)
    bank_code = Column(String, nullable=False, index=True)
    avg_transaction_amount = Column(Numeric(15, 2), nullable=False)
    transaction_frequency = Column(Float, nullable=False)
    preferred_merchant_categories = Column(ARRAY(String), nullable=True)
    location_clusters = Column(ARRAY(String), nullable=True)
    active_hours = Column(ARRAY(Integer), nullable=True)
    device_count = Column(Integer, nullable=False, default=1)
    ip_diversity_score = Column(Float, nullable=False, default=0.0)
    upi_counterparty_diversity = Column(Float, nullable=False, default=0.0)
    risk_baseline = Column(Float, nullable=False, default=0.0)
    last_transaction_timestamp = Column(DateTime, nullable=False)
    profile_confidence = Column(Float, nullable=False, default=0.0)
    anomaly_count_30d = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class FraudDetectionEngine:
    """
    Advanced fraud detection engine with multiple algorithms
    """

    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.is_trained = False
        self.feature_columns = [
            'amount', 'hour_of_day', 'day_of_week', 'transaction_frequency_score',
            'location_novelty', 'device_novelty', 'merchant_novelty', 'amount_deviation'
        ]

    def train_behavioral_models(self, historical_data: pd.DataFrame):
        """Train fraud detection models on historical data"""
        logger.info(f"Training fraud detection models on {len(historical_data)} records")

        if len(historical_data) < 100:
            logger.warning("Insufficient data for training models")
            return

        # Prepare features
        features = self._prepare_features(historical_data)

        # Train isolation forest
        self.isolation_forest.fit(features)
        self.scaler.fit(features)

        self.is_trained = True
        logger.info("Fraud detection models trained successfully")

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for fraud detection"""
        features = []

        for _, row in df.iterrows():
            feature_vector = [
                float(row.get('amount', 0)),
                float(row.get('hour_of_day', 0)),
                float(row.get('day_of_week', 0)),
                float(row.get('transaction_frequency_score', 0)),
                float(row.get('location_novelty', 0)),
                float(row.get('device_novelty', 0)),
                float(row.get('merchant_novelty', 0)),
                float(row.get('amount_deviation', 0))
            ]
            features.append(feature_vector)

        return np.array(features)

    def detect_anomalies(self, transactions: pd.DataFrame) -> Tuple[List[str], np.ndarray]:
        """Detect anomalous transactions using trained models"""
        if not self.is_trained:
            logger.warning("Models not trained, skipping anomaly detection")
            return [], np.array([])

        features = self._prepare_features(transactions)
        scaled_features = self.scaler.transform(features)

        # Isolation forest predictions
        anomaly_predictions = self.isolation_forest.predict(scaled_features)
        anomaly_scores = self.isolation_forest.decision_function(scaled_features)

        # Get anomalous transaction indices
        anomalous_indices = np.where(anomaly_predictions == -1)[0]
        anomalous_transaction_ids = [transactions.iloc[i]['transaction_id'] for i in anomalous_indices]

        logger.info(f"Detected {len(anomalous_transaction_ids)} anomalous transactions out of {len(transactions)}")

        return anomalous_transaction_ids, anomaly_scores

    def analyze_transaction_patterns(self, transactions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze transaction patterns for fraud indicators"""
        pattern_analysis = {
            'rapid_transactions': self._detect_rapid_transactions(transactions),
            'unusual_amounts': self._detect_unusual_amounts(transactions),
            'location_anomalies': self._detect_location_anomalies(transactions),
            'temporal_anomalies': self._detect_temporal_anomalies(transactions),
            'cross_account_patterns': self._detect_cross_account_patterns(transactions)
        }

        return pattern_analysis

    def _detect_rapid_transactions(self, df: pd.DataFrame) -> List[Dict]:
        """Detect rapid succession transactions"""
        rapid_transactions = []

        # Group by account and sort by time
        for account_hash in df['account_id_hash'].unique():
            account_txns = df[df['account_id_hash'] == account_hash].sort_values('timestamp')

            for i in range(1, len(account_txns)):
                time_diff = (account_txns.iloc[i]['timestamp'] - account_txns.iloc[i-1]['timestamp']).total_seconds()

                # Flag transactions within 5 minutes
                if time_diff <= 300:  # 5 minutes
                    rapid_transactions.append({
                        'transaction_id': account_txns.iloc[i]['transaction_id'],
                        'account_hash': account_hash,
                        'time_diff_seconds': time_diff,
                        'consecutive_count': self._count_consecutive_rapid_transactions(account_txns, i)
                    })

        return rapid_transactions

    def _count_consecutive_rapid_transactions(self, account_txns: pd.DataFrame, current_index: int) -> int:
        """Count consecutive rapid transactions"""
        count = 1
        for i in range(current_index - 1, -1, -1):
            time_diff = (account_txns.iloc[current_index]['timestamp'] - account_txns.iloc[i]['timestamp']).total_seconds()
            if time_diff <= 300:  # 5 minutes
                count += 1
            else:
                break
        return count

    def _detect_unusual_amounts(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual transaction amounts"""
        unusual_amounts = []

        for account_hash in df['account_id_hash'].unique():
            account_txns = df[df['account_id_hash'] == account_hash]

            if len(account_txns) < 3:  # Need baseline
                continue

            amounts = account_txns['amount'].astype(float)
            mean_amount = amounts.mean()
            std_amount = amounts.std()

            # Flag amounts > 3 standard deviations from mean
            for _, txn in account_txns.iterrows():
                z_score = abs((float(txn['amount']) - mean_amount) / (std_amount + 1e-6))
                if z_score > 3:
                    unusual_amounts.append({
                        'transaction_id': txn['transaction_id'],
                        'account_hash': account_hash,
                        'amount': float(txn['amount']),
                        'mean_amount': mean_amount,
                        'z_score': z_score,
                        'deviation_type': 'high' if float(txn['amount']) > mean_amount else 'low'
                    })

        return unusual_amounts

    def _detect_location_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect location-based anomalies"""
        location_anomalies = []

        for account_hash in df['account_id_hash'].unique():
            account_txns = df[df['account_id_hash'] == account_hash].dropna(subset=['location_cluster'])

            if len(account_txns) < 2:
                continue

            # Check for transactions in multiple distant locations within short time
            for i in range(1, len(account_txns)):
                current_txn = account_txns.iloc[i]
                prev_txn = account_txns.iloc[i-1]

                # Skip if same location
                if current_txn['location_cluster'] == prev_txn['location_cluster']:
                    continue

                time_diff = (current_txn['timestamp'] - prev_txn['timestamp']).total_seconds()

                # Flag distant locations within 1 hour
                if time_diff <= 3600:  # 1 hour
                    location_anomalies.append({
                        'transaction_id': current_txn['transaction_id'],
                        'account_hash': account_hash,
                        'current_location': current_txn['location_cluster'],
                        'previous_location': prev_txn['location_cluster'],
                        'time_diff_seconds': time_diff,
                        'impossible_travel': True if time_diff < 1800 else False  # 30 minutes
                    })

        return location_anomalies

    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect temporal anomalies in transaction patterns"""
        temporal_anomalies = []

        for account_hash in df['account_id_hash'].unique():
            account_txns = df[df['account_id_hash'] == account_hash]

            if len(account_txns) < 5:
                continue

            # Extract hour patterns
            account_txns['hour'] = pd.to_datetime(account_txns['timestamp']).dt.hour
            hour_counts = account_txns['hour'].value_counts()

            # Identify unusual transaction hours (e.g., 2-4 AM)
            unusual_hours = [h for h in hour_counts.index if h in [2, 3, 4, 22, 23, 0, 1]]

            for hour in unusual_hours:
                hour_txns = account_txns[account_txns['hour'] == hour]
                for _, txn in hour_txns.iterrows():
                    temporal_anomalies.append({
                        'transaction_id': txn['transaction_id'],
                        'account_hash': account_hash,
                        'unusual_hour': hour,
                        'hour_frequency': hour_counts[hour],
                        'total_transactions': len(account_txns),
                        'frequency_ratio': hour_counts[hour] / len(account_txns)
                    })

        return temporal_anomalies

    def _detect_cross_account_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect patterns across multiple accounts"""
        cross_account_patterns = []

        # Look for synchronized transactions across different accounts
        for timestamp in df['timestamp'].unique():
            timestamp_txns = df[df['timestamp'] == timestamp]

            if len(timestamp_txns) < 3:  # Need at least 3 synchronized accounts
                continue

            # Check for similar amounts
            amounts = timestamp_txns['amount'].astype(float).values

            # Group similar amounts (within 10% variance)
            for i, amount1 in enumerate(amounts):
                similar_amounts = []
                for j, amount2 in enumerate(amounts):
                    if i != j and abs(amount1 - amount2) / max(amount1, amount2) < 0.1:
                        similar_amounts.append(j)

                if len(similar_amounts) >= 2:  # Found pattern
                    cross_account_patterns.append({
                        'timestamp': timestamp,
                        'base_amount': amount1,
                        'similar_account_count': len(similar_amounts) + 1,
                        'total_accounts_involved': len(similar_amounts) + 1,
                        'pattern_strength': len(similar_amounts) / len(amounts)
                    })

        return cross_account_patterns

class CFCFRMSIntegrationService:
    """
    Main CFCFRMS integration service for bank transaction monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('cfcfrms_base_url', 'https://api.cfcfrms.gov.in')
        self.api_key = config.get('cfcfrms_api_key')
        self.fraud_engine = FraudDetectionEngine()

        # Database setup
        self.engine = create_engine(config.get('database_url', 'sqlite:///aegis_cfcfrms.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis for caching
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 1),
            decode_responses=True
        )

        # Monitoring configuration
        self.batch_size = config.get('batch_size', 500)
        self.sync_interval = config.get('sync_interval', 60)  # 1 minute for real-time monitoring
        self.alert_threshold = config.get('alert_threshold', 0.7)

        self.session = None
        self.last_sync_time = None
        self.total_transactions_processed = 0
        self.total_alerts_generated = 0
        self.monitoring_active = False

    async def initialize(self):
        """Initialize the CFCFRMS integration service"""
        logger.info("Initializing CFCFRMS Integration Service")

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'AEGIS-CFCFRMS-Integration/1.0'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )

        # Test connectivity
        await self._test_cfcfrms_connectivity()

        # Train fraud detection models with historical data
        await self._train_fraud_models()

        logger.info("CFCFRMS Integration Service initialized successfully")

    async def _test_cfcfrms_connectivity(self):
        """Test connectivity to CFCFRMS API"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("CFCFRMS API connectivity test successful")
                else:
                    logger.warning(f"CFCFRMS API health check failed: {response.status}")
        except Exception as e:
            logger.error(f"CFCFRMS API connectivity test failed: {str(e)}")
            # Don't raise - we can work with cached/simulated data

    async def _train_fraud_models(self):
        """Train fraud detection models with historical data"""
        logger.info("Training fraud detection models with historical data")

        # Load historical data (simulated for demo)
        historical_data = await self._load_historical_transactions()

        if len(historical_data) > 0:
            df = pd.DataFrame(historical_data)
            self.fraud_engine.train_behavioral_models(df)
            logger.info(f"Trained fraud models with {len(historical_data)} historical records")
        else:
            logger.warning("No historical data available for model training")

    async def _load_historical_transactions(self) -> List[Dict]:
        """Load historical transaction data for training"""
        # For demo purposes, generate synthetic historical data
        # In production, this would load from database or CFCFRMS API

        historical_data = []
        base_time = datetime.utcnow() - timedelta(days=30)

        for i in range(1000):  # Generate 1000 historical transactions
            txn = {
                'transaction_id': f'HIST_{i:06d}',
                'account_id_hash': hashlib.sha256(f'account_{i % 100}'.encode()).hexdigest()[:16],
                'bank_code': f'BANK_{(i % 10) + 1:02d}',
                'transaction_type': np.random.choice(['debit', 'credit', 'upi_transaction']),
                'amount': np.random.lognormal(8, 1.5),  # Log-normal distribution
                'timestamp': base_time + timedelta(minutes=np.random.randint(0, 43200)),  # Random time in last 30 days
                'hour_of_day': np.random.randint(0, 24),
                'day_of_week': np.random.randint(0, 7),
                'location_cluster': f'LOC_{np.random.randint(0, 20):02d}',
                'device_fingerprint_hash': f'DEV_{np.random.randint(0, 50):02d}',
                'merchant_category': np.random.choice(['retail', 'restaurant', 'atm', 'online', 'transfer']),
                'transaction_frequency_score': np.random.uniform(0, 1),
                'location_novelty': np.random.uniform(0, 1),
                'device_novelty': np.random.uniform(0, 1),
                'merchant_novelty': np.random.uniform(0, 1),
                'amount_deviation': np.random.uniform(0, 1)
            }
            historical_data.append(txn)

        return historical_data

    async def fetch_transaction_data(self, start_time: datetime, end_time: datetime) -> List[BankTransaction]:
        """
        Fetch transaction data from CFCFRMS API within specified time range
        """
        logger.info(f"Fetching CFCFRMS transaction data from {start_time} to {end_time}")

        # For demo purposes, generate synthetic transaction data
        # In production, this would fetch from actual CFCFRMS API
        transactions = []

        # Generate synthetic transactions
        num_transactions = np.random.randint(10, 100)
        for i in range(num_transactions):
            txn_time = start_time + timedelta(
                seconds=np.random.randint(0, int((end_time - start_time).total_seconds()))
            )

            # Simulate some suspicious transactions
            is_suspicious = np.random.random() < 0.1  # 10% suspicious

            transaction = BankTransaction(
                transaction_id=f"TXN_{uuid.uuid4().hex[:12].upper()}",
                account_id=f"ACC_{hashlib.sha256(f'account_{np.random.randint(0, 1000)}'.encode()).hexdigest()[:16]}",
                bank_code=f"BANK_{np.random.randint(1, 21):02d}",
                transaction_type=np.random.choice(list(TransactionType)),
                amount=np.random.lognormal(8, 1.5) if not is_suspicious else np.random.lognormal(10, 2),
                currency="INR",
                timestamp=txn_time,
                merchant_id=f"MER_{np.random.randint(0, 500):04d}" if np.random.random() > 0.3 else None,
                merchant_name=f"Merchant {np.random.randint(1, 100)}" if np.random.random() > 0.3 else None,
                merchant_category=np.random.choice(['retail', 'restaurant', 'atm', 'online', 'transfer']),
                location_lat=28.6139 + np.random.uniform(-0.1, 0.1) if np.random.random() > 0.2 else None,
                location_lon=77.2090 + np.random.uniform(-0.1, 0.1) if np.random.random() > 0.2 else None,
                device_id=f"DEV_{hashlib.sha256(f'device_{np.random.randint(0, 100)}'.encode()).hexdigest()[:16]}" if np.random.random() > 0.3 else None,
                ip_address=f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}" if np.random.random() > 0.3 else None,
                channel=np.random.choice(['online', 'mobile', 'atm', 'pos']),
                upi_id=f"user{np.random.randint(1, 10000)}@upi" if np.random.random() > 0.5 else None,
                beneficiary_account=f"BEN_{hashlib.sha256(f'beneficiary_{np.random.randint(0, 500)}'.encode()).hexdigest()[:16]}" if np.random.random() > 0.6 else None,
                beneficiary_name=f"Beneficiary {np.random.randint(1, 200)}" if np.random.random() > 0.6 else None,
                reference_number=f"REF_{uuid.uuid4().hex[:8].upper()}" if np.random.random() > 0.4 else None,
                status='completed',
                risk_score=np.random.uniform(0, 1) if is_suspicious else np.random.uniform(0, 0.3),
                fraud_signals=[self._generate_fraud_signal() for _ in range(np.random.randint(0, 3))] if is_suspicious else []
            )
            transactions.append(transaction)

        logger.info(f"Fetched {len(transactions)} transactions from CFCFRMS (simulated)")
        return transactions

    def _generate_fraud_signal(self) -> str:
        """Generate a random fraud signal"""
        signals = [
            'unusual_amount', 'rapid_transactions', 'new_device', 'location_anomaly',
            'account_takeover', 'synchronous_activity', 'time_anomaly', 'frequency_anomaly'
        ]
        return np.random.choice(signals)

    async def process_transaction_batch(self, transactions: List[BankTransaction]) -> Tuple[List[FraudAlert], Dict[str, Any]]:
        """
        Process a batch of transactions and detect fraud
        """
        logger.info(f"Processing batch of {len(transactions)} transactions")

        if not transactions:
            return [], {}

        # Store transactions in database
        await self._store_transactions(transactions)

        # Convert to DataFrame for analysis
        df = pd.DataFrame([self._transaction_to_dict(txn) for txn in transactions])

        # Detect anomalies using fraud detection engine
        anomalous_txns, anomaly_scores = self.fraud_engine.detect_anomalies(df)

        # Analyze transaction patterns
        pattern_analysis = self.fraud_engine.analyze_transaction_patterns(df)

        # Generate fraud alerts
        fraud_alerts = await self._generate_fraud_alerts(df, anomalous_txns, pattern_analysis)

        # Update account behavior profiles
        await self._update_behavior_profiles(df)

        # Cache results
        await self._cache_analysis_results(fraud_alerts, pattern_analysis)

        # Update metrics
        self.total_transactions_processed += len(transactions)
        self.total_alerts_generated += len(fraud_alerts)

        processing_summary = {
            'transactions_processed': len(transactions),
            'anomalous_transactions': len(anomalous_txns),
            'alerts_generated': len(fraud_alerts),
            'patterns_detected': {
                'rapid_transactions': len(pattern_analysis.get('rapid_transactions', [])),
                'unusual_amounts': len(pattern_analysis.get('unusual_amounts', [])),
                'location_anomalies': len(pattern_analysis.get('location_anomalies', [])),
                'temporal_anomalies': len(pattern_analysis.get('temporal_anomalies', [])),
                'cross_account_patterns': len(pattern_analysis.get('cross_account_patterns', []))
            }
        }

        logger.info(f"Batch processing completed: {len(fraud_alerts)} fraud alerts generated")
        return fraud_alerts, processing_summary

    def _transaction_to_dict(self, txn: BankTransaction) -> Dict:
        """Convert BankTransaction to dictionary"""
        return {
            'transaction_id': txn.transaction_id,
            'account_id_hash': hashlib.sha256(txn.account_id.encode()).hexdigest()[:16],
            'bank_code': txn.bank_code,
            'transaction_type': txn.transaction_type.value,
            'amount': txn.amount,
            'currency': txn.currency,
            'timestamp': txn.timestamp,
            'merchant_category': txn.merchant_category,
            'location_cluster': self._get_location_cluster(txn.location_lat, txn.location_lon),
            'device_fingerprint_hash': hashlib.sha256(txn.device_id.encode()).hexdigest()[:16] if txn.device_id else None,
            'ip_address_hash': hashlib.sha256(txn.ip_address.encode()).hexdigest()[:16] if txn.ip_address else None,
            'channel': txn.channel,
            'upi_id_hash': hashlib.sha256(txn.upi_id.encode()).hexdigest()[:16] if txn.upi_id else None,
            'beneficiary_account_hash': hashlib.sha256(txn.beneficiary_account.encode()).hexdigest()[:16] if txn.beneficiary_account else None,
            'status': txn.status,
            'risk_score': txn.risk_score,
            'fraud_signals': txn.fraud_signals,
            'hour_of_day': txn.timestamp.hour,
            'day_of_week': txn.timestamp.weekday()
        }

    def _get_location_cluster(self, lat: Optional[float], lon: Optional[float]) -> Optional[str]:
        """Get location cluster from coordinates"""
        if lat is None or lon is None:
            return None

        # Simple grid-based clustering (approximate 1km x 1km grid)
        lat_grid = int(lat * 100)
        lon_grid = int(lon * 100)
        return f"LOC_{lat_grid:04d}_{lon_grid:04d}"

    async def _store_transactions(self, transactions: List[BankTransaction]):
        """Store transactions in database"""
        db = self.SessionLocal()
        try:
            batch_id = str(uuid.uuid4())

            for txn in transactions:
                db_txn = BankTransaction(
                    transaction_id=txn.transaction_id,
                    account_id_hash=hashlib.sha256(txn.account_id.encode()).hexdigest()[:16],
                    bank_code=txn.bank_code,
                    transaction_type=txn.transaction_type.value,
                    amount=txn.amount,
                    currency=txn.currency,
                    timestamp=txn.timestamp,
                    merchant_id=txn.merchant_id,
                    merchant_category=txn.merchant_category,
                    location_cluster=self._get_location_cluster(txn.location_lat, txn.location_lon),
                    device_fingerprint_hash=hashlib.sha256(txn.device_id.encode()).hexdigest()[:16] if txn.device_id else None,
                    ip_address_hash=hashlib.sha256(txn.ip_address.encode()).hexdigest()[:16] if txn.ip_address else None,
                    channel=txn.channel,
                    upi_id_hash=hashlib.sha256(txn.upi_id.encode()).hexdigest()[:16] if txn.upi_id else None,
                    beneficiary_account_hash=hashlib.sha256(txn.beneficiary_account.encode()).hexdigest()[:16] if txn.beneficiary_account else None,
                    status=txn.status,
                    risk_score=txn.risk_score,
                    fraud_signals=txn.fraud_signals,
                    is_suspicious=txn.risk_score > 0.5,
                    is_flagged_for_review=txn.risk_score > 0.7,
                    batch_id=batch_id
                )
                db.add(db_txn)

            db.commit()
            logger.info(f"Stored {len(transactions)} transactions in database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing transactions: {str(e)}")
            raise
        finally:
            db.close()

    async def _generate_fraud_alerts(self, df: pd.DataFrame, anomalous_txns: List[str], pattern_analysis: Dict) -> List[FraudAlert]:
        """Generate fraud alerts based on analysis results"""
        alerts = []

        # Alerts for anomalous transactions
        for txn_id in anomalous_txns:
            txn_data = df[df['transaction_id'] == txn_id].iloc[0] if not df[df['transaction_id'] == txn_id].empty else None

            if txn_data is not None:
                alert = FraudAlert(
                    alert_id=f"ALERT_{uuid.uuid4().hex[:12].upper()}",
                    account_id=txn_data['account_id_hash'],
                    bank_code=txn_data['bank_code'],
                    alert_type=FraudSignalType.AMOUNT_ANOMALY,
                    risk_level=RiskLevel.HIGH if txn_data['risk_score'] > 0.7 else RiskLevel.MEDIUM,
                    confidence_score=float(txn_data['risk_score']),
                    description=f"Anomalous transaction detected: {txn_data['transaction_type']} of ₹{txn_data['amount']:,.2f}",
                    affected_transactions=[txn_id],
                    detection_timestamp=datetime.utcnow(),
                    location_data={'cluster': txn_data.get('location_cluster')},
                    recommended_action="immediate_review" if txn_data['risk_score'] > 0.8 else "enhanced_monitoring",
                    escalation_required=txn_data['risk_score'] > 0.8
                )
                alerts.append(alert)

        # Alerts for pattern-based detections
        alerts.extend(await self._generate_pattern_alerts(pattern_analysis))

        return alerts

    async def _generate_pattern_alerts(self, pattern_analysis: Dict) -> List[FraudAlert]:
        """Generate alerts based on pattern analysis"""
        alerts = []

        # Rapid transactions alerts
        for rapid_txn in pattern_analysis.get('rapid_transactions', []):
            if rapid_txn['consecutive_count'] >= 3:  # 3+ rapid transactions
                alert = FraudAlert(
                    alert_id=f"ALERT_RAPID_{uuid.uuid4().hex[:8].upper()}",
                    account_id=rapid_txn['account_hash'],
                    bank_code="MULTIPLE",  # Could be determined from additional data
                    alert_type=FraudSignalType.RAPID_TRANSACTIONS,
                    risk_level=RiskLevel.HIGH if rapid_txn['consecutive_count'] >= 5 else RiskLevel.MEDIUM,
                    confidence_score=min(0.9, 0.5 + (rapid_txn['consecutive_count'] * 0.1)),
                    description=f"Rapid succession of {rapid_txn['consecutive_count']} transactions detected within {rapid_txn['time_diff_seconds']} seconds",
                    affected_transactions=[rapid_txn['transaction_id']],
                    detection_timestamp=datetime.utcnow(),
                    location_data={},
                    recommended_action="account_freeze" if rapid_txn['consecutive_count'] >= 5 else "enhanced_monitoring",
                    escalation_required=rapid_txn['consecutive_count'] >= 5
                )
                alerts.append(alert)

        # Unusual amount alerts
        for unusual_amount in pattern_analysis.get('unusual_amounts', []):
            if unusual_amount['z_score'] > 4:  # Very unusual
                alert = FraudAlert(
                    alert_id=f"ALERT_AMOUNT_{uuid.uuid4().hex[:8].upper()}",
                    account_id=unusual_amount['account_hash'],
                    bank_code="MULTIPLE",
                    alert_type=FraudSignalType.UNUSUAL_AMOUNT,
                    risk_level=RiskLevel.CRITICAL if unusual_amount['z_score'] > 5 else RiskLevel.HIGH,
                    confidence_score=min(0.95, 0.6 + (unusual_amount['z_score'] * 0.05)),
                    description=f"Unusual transaction amount of ₹{unusual_amount['amount']:,.2f} detected (z-score: {unusual_amount['z_score']:.2f})",
                    affected_transactions=[unusual_amount['transaction_id']],
                    detection_timestamp=datetime.utcnow(),
                    location_data={},
                    recommended_action="immediate_block" if unusual_amount['z_score'] > 5 else "enhanced_verification",
                    escalation_required=True
                )
                alerts.append(alert)

        # Location anomaly alerts
        for location_anomaly in pattern_analysis.get('location_anomalies', []):
            if location_anomaly['impossible_travel']:
                alert = FraudAlert(
                    alert_id=f"ALERT_LOCATION_{uuid.uuid4().hex[:8].upper()}",
                    account_id=location_anomaly['account_hash'],
                    bank_code="MULTIPLE",
                    alert_type=FraudSignalType.LOCATION_ANOMALY,
                    risk_level=RiskLevel.CRITICAL,
                    confidence_score=0.9,
                    description=f"Impossible travel detected: transaction in {location_anomaly['current_location']} just {location_anomaly['time_diff_seconds']} seconds after {location_anomaly['previous_location']}",
                    affected_transactions=[location_anomaly['transaction_id']],
                    detection_timestamp=datetime.utcnow(),
                    location_data={
                        'current': location_anomaly['current_location'],
                        'previous': location_anomaly['previous_location'],
                        'time_diff': location_anomaly['time_diff_seconds']
                    },
                    recommended_action="account_freeze",
                    escalation_required=True
                )
                alerts.append(alert)

        return alerts

    async def _update_behavior_profiles(self, df: pd.DataFrame):
        """Update account behavior profiles"""
        db = self.SessionLocal()
        try:
            for account_hash in df['account_id_hash'].unique():
                account_txns = df[df['account_id_hash'] == account_hash]

                if len(account_txns) == 0:
                    continue

                # Calculate profile metrics
                avg_amount = account_txns['amount'].astype(float).mean()
                transaction_frequency = len(account_txns) / 30  # Assuming 30-day window

                # Get most common merchant categories
                merchant_categories = account_txns['merchant_category'].dropna().value_counts().head(5).index.tolist()

                # Get location clusters
                location_clusters = account_txns['location_cluster'].dropna().unique().tolist()

                # Calculate active hours
                account_txns['hour'] = pd.to_datetime(account_txns['timestamp']).dt.hour
                active_hours = account_txns['hour'].value_counts().head(8).index.tolist()

                # Calculate device diversity
                device_count = account_txns['device_fingerprint_hash'].nunique()

                # Calculate risk baseline
                risk_baseline = account_txns['risk_score'].mean()

                # Check if profile exists
                existing_profile = db.query(AccountBehaviorProfileRecord).filter(
                    AccountBehaviorProfileRecord.account_id_hash == account_hash
                ).first()

                if existing_profile:
                    # Update existing profile
                    existing_profile.avg_transaction_amount = avg_amount
                    existing_profile.transaction_frequency = transaction_frequency
                    existing_profile.preferred_merchant_categories = merchant_categories
                    existing_profile.location_clusters = location_clusters
                    existing_profile.active_hours = active_hours
                    existing_profile.device_count = device_count
                    existing_profile.risk_baseline = risk_baseline
                    existing_profile.last_transaction_timestamp = account_txns['timestamp'].max()
                    existing_profile.last_updated = datetime.utcnow()
                else:
                    # Create new profile
                    new_profile = AccountBehaviorProfileRecord(
                        account_id_hash=account_hash,
                        bank_code=account_txns['bank_code'].iloc[0],
                        avg_transaction_amount=avg_amount,
                        transaction_frequency=transaction_frequency,
                        preferred_merchant_categories=merchant_categories,
                        location_clusters=location_clusters,
                        active_hours=active_hours,
                        device_count=device_count,
                        risk_baseline=risk_baseline,
                        last_transaction_timestamp=account_txns['timestamp'].max(),
                        profile_confidence=min(1.0, len(account_txns) / 10)  # Confidence based on data volume
                    )
                    db.add(new_profile)

            db.commit()
            logger.info(f"Updated behavior profiles for {len(df['account_id_hash'].unique())} accounts")

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating behavior profiles: {str(e)}")
        finally:
            db.close()

    async def _cache_analysis_results(self, fraud_alerts: List[FraudAlert], pattern_analysis: Dict):
        """Cache analysis results in Redis"""
        try:
            cache_key = "cfcfrms:latest_analysis"
            cache_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'fraud_alerts_count': len(fraud_alerts),
                'high_risk_alerts': len([a for a in fraud_alerts if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
                'patterns_detected': {
                    key: len(value) for key, value in pattern_analysis.items()
                },
                'critical_alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'risk_level': alert.risk_level.value,
                        'description': alert.description,
                        'timestamp': alert.detection_timestamp.isoformat()
                    }
                    for alert in fraud_alerts if alert.risk_level == RiskLevel.CRITICAL
                ][:5]  # Top 5 critical alerts
            }

            self.redis_client.setex(cache_key, 300, json.dumps(cache_data, default=str))
            logger.info("Cached latest analysis results in Redis")

        except Exception as e:
            logger.warning(f"Error caching to Redis: {str(e)}")

    async def store_fraud_alerts(self, alerts: List[FraudAlert]):
        """Store fraud alerts in database"""
        db = self.SessionLocal()
        try:
            for alert in alerts:
                db_alert = FraudAlertRecord(
                    alert_id=alert.alert_id,
                    account_id_hash=alert.account_id,
                    bank_code=alert.bank_code,
                    alert_type=alert.alert_type.value,
                    risk_level=alert.risk_level.value,
                    confidence_score=alert.confidence_score,
                    description=alert.description,
                    affected_transactions=alert.affected_transactions,
                    detection_timestamp=alert.detection_timestamp,
                    location_data=alert.location_data,
                    recommended_action=alert.recommended_action,
                    escalation_required=alert.escalation_required
                )
                db.add(db_alert)

            db.commit()
            logger.info(f"Stored {len(alerts)} fraud alerts in database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing fraud alerts: {str(e)}")
            raise
        finally:
            db.close()

    async def start_real_time_monitoring(self):
        """Start real-time transaction monitoring"""
        logger.info("Starting real-time CFCFRMS transaction monitoring")
        self.monitoring_active = True

        while self.monitoring_active:
            try:
                # Calculate time range for monitoring
                end_time = datetime.utcnow()
                start_time = self.last_sync_time or (end_time - timedelta(seconds=self.sync_interval))

                # Fetch and process transactions
                transactions = await self.fetch_transaction_data(start_time, end_time)

                if transactions:
                    fraud_alerts, processing_summary = await self.process_transaction_batch(transactions)

                    # Store fraud alerts
                    if fraud_alerts:
                        await self.store_fraud_alerts(fraud_alerts)

                    # Log monitoring results
                    logger.info(f"Real-time monitoring cycle completed: {processing_summary}")

                    # Check for critical alerts that need immediate action
                    critical_alerts = [a for a in fraud_alerts if a.risk_level == RiskLevel.CRITICAL]
                    if critical_alerts:
                        await self._handle_critical_alerts(critical_alerts)

                # Update last sync time
                self.last_sync_time = end_time

                # Wait for next monitoring cycle
                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in real-time monitoring: {str(e)}")
                await asyncio.sleep(10)  # Short retry interval

    async def _handle_critical_alerts(self, critical_alerts: List[FraudAlert]):
        """Handle critical fraud alerts"""
        logger.warning(f"Handling {len(critical_alerts)} critical fraud alerts")

        for alert in critical_alerts:
            # In production, this would trigger immediate actions:
            # - Send high-priority notifications
            # - Initiate account blocking procedures
            # - Alert law enforcement
            # - Update real-time dashboards

            logger.critical(f"CRITICAL ALERT: {alert.description}")

            # Simulate immediate action
            if alert.recommended_action in ["account_freeze", "immediate_block"]:
                logger.info(f"Immediate action triggered for account {alert.account_id}: {alert.recommended_action}")

    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        db = self.SessionLocal()
        try:
            # Get recent statistics
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            # Transaction counts
            recent_txns = db.query(BankTransaction).filter(
                BankTransaction.timestamp >= hour_ago
            ).count()

            daily_txns = db.query(BankTransaction).filter(
                BankTransaction.timestamp >= day_ago
            ).count()

            # Alert counts
            recent_alerts = db.query(FraudAlertRecord).filter(
                FraudAlertRecord.detection_timestamp >= hour_ago
            ).count()

            daily_alerts = db.query(FraudAlertRecord).filter(
                FraudAlertRecord.detection_timestamp >= day_ago
            ).count()

            # Critical alerts
            critical_alerts = db.query(FraudAlertRecord).filter(
                FraudAlertRecord.detection_timestamp >= hour_ago,
                FraudAlertRecord.risk_level == 'critical'
            ).all()

            # Get top fraud patterns
            pattern_alerts = db.query(FraudAlertRecord.alert_type, db.func.count(FraudAlertRecord.id)).filter(
                FraudAlertRecord.detection_timestamp >= day_ago
            ).group_by(FraudAlertRecord.alert_type).order_by(db.func.count(FraudAlertRecord.id).desc()).limit(5).all()

            return {
                'monitoring_status': 'active' if self.monitoring_active else 'inactive',
                'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
                'total_transactions_processed': self.total_transactions_processed,
                'total_alerts_generated': self.total_alerts_generated,
                'recent_activity': {
                    'transactions_last_hour': recent_txns,
                    'transactions_today': daily_txns,
                    'alerts_last_hour': recent_alerts,
                    'alerts_today': daily_alerts,
                    'critical_alerts_count': len(critical_alerts),
                    'critical_alerts': [
                        {
                            'alert_id': alert.alert_id,
                            'description': alert.description,
                            'risk_level': alert.risk_level,
                            'timestamp': alert.detection_timestamp.isoformat()
                        }
                        for alert in critical_alerts[:5]
                    ]
                },
                'top_fraud_patterns': [
                    {'pattern': pattern, 'count': count} for pattern, count in pattern_alerts
                ],
                'system_health': {
                    'fraud_engine_trained': self.fraud_engine.is_trained,
                    'database_connected': True,
                    'redis_connected': self.redis_client.ping(),
                    'monitoring_uptime_seconds': (datetime.utcnow() - (self.last_sync_time or datetime.utcnow())).total_seconds()
                }
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {'error': str(e)}
        finally:
            db.close()

    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        logger.info("Stopping real-time CFCFRMS monitoring")
        self.monitoring_active = False

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up CFCFRMS Integration Service")

        await self.stop_monitoring()

        if self.session:
            await self.session.close()

        if self.redis_client:
            self.redis_client.close()

        logger.info("CFCFRMS Integration Service cleanup completed")

# Configuration and initialization
async def create_cfcfrms_service(config: Dict[str, Any]) -> CFCFRMSIntegrationService:
    """Create and initialize CFCFRMS integration service"""
    service = CFCFRMSIntegrationService(config)
    await service.initialize()
    return service

# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'cfcfrms_base_url': 'https://api.cfcfrms.gov.in/v1',
        'cfcfrms_api_key': 'your-api-key-here',
        'database_url': 'sqlite:///aegis_cfcfrms.db',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'batch_size': 500,
        'sync_interval': 60,
        'alert_threshold': 0.7
    }

    async def main():
        # Create and start service
        service = await create_cfcfrms_service(config)

        try:
            # Start real-time monitoring
            await service.start_real_time_monitoring()
        except KeyboardInterrupt:
            logger.info("Shutting down CFCFRMS Integration Service")
        finally:
            await service.cleanup()

    # Run the service
    asyncio.run(main())