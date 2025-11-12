"""
Secure Kafka-based Data Ingestion Pipeline for AEGIS
Advanced Real-time Data Processing with Security and Privacy

Implements comprehensive data ingestion pipeline with:
- Apache Kafka for real-time streaming
- End-to-end encryption and security
- Schema validation and data quality
- Multi-source data ingestion
- Privacy-preserving data processing
- Real-time monitoring and alerting
- Fault tolerance and recovery
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import redis
import yaml
from pydantic import BaseModel, ValidationError
import prometheus_client as prom
import structlog
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

Base = declarative_base()

class DataSource(Enum):
    """Data source types"""
    NCRP = "ncrp"
    CFCFRMS = "cfcfrms"
    I4C = "i4c"
    BANK_TRANSACTIONS = "bank_transactions"
    citizen_reports = "citizen_reports"
    LEA_FEEDBACK = "lea_feedback"
    SYSTEM_ALERTS = "system_alerts"

class DataPriority(Enum):
    """Data message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class ProcessingStatus(Enum):
    """Data processing status"""
    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSED = "processed"
    FAILED = "failed"
    QUARANTINED = "quarantined"

@dataclass
class IngestionMetrics:
    """Pipeline ingestion metrics"""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    messages_quarantined: int = 0
    processing_latency_ms: float = 0.0
    throughput_msgs_per_sec: float = 0.0
    error_rate: float = 0.0
    last_message_timestamp: Optional[datetime] = None
    kafka_lag: int = 0

# Prometheus metrics
MESSAGES_RECEIVED_TOTAL = prom.Counter('kafka_messages_received_total', 'Total messages received', ['source', 'topic'])
MESSAGES_PROCESSED_TOTAL = prom.Counter('kafka_messages_processed_total', 'Total messages processed', ['source', 'status'])
PROCESSING_LATENCY = prom.Histogram('kafka_processing_latency_seconds', 'Message processing latency')
ERROR_RATE = prom.Gauge('kafka_error_rate', 'Current error rate')
THROUGHPUT = prom.Gauge('kafka_throughput_msgs_per_sec', 'Current throughput')
KAFKA_LAG = prom.Gauge('kafka_consumer_lag', 'Kafka consumer lag')

class DataSchemaValidator:
    """Schema validator for incoming data messages"""

    def __init__(self):
        self.schemas = {
            'ncrp_complaint': self._get_ncrp_schema(),
            'bank_transaction': self._get_bank_transaction_schema(),
            'i4c_crime_record': self._get_i4c_schema(),
            'citizen_report': self._get_citizen_report_schema(),
            'lea_feedback': self._get_lea_feedback_schema(),
            'system_alert': self._get_system_alert_schema()
        }

    def validate_message(self, message_type: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate message against its schema"""
        if message_type not in self.schemas:
            return False, f"Unknown message type: {message_type}"

        try:
            schema = self.schemas[message_type]
            # Use Pydantic for validation
            validated_data = schema(**data)
            return True, None
        except ValidationError as e:
            return False, f"Validation error: {str(e)}"
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"

    def _get_ncrp_schema(self):
        """NCRP complaint schema"""
        class NCRPComplaint(BaseModel):
            complaint_id: str
            timestamp: datetime
            scam_type: str
            amount: float
            victim_location: Dict[str, float]
            digital_fingerprints: List[str] = []
            urgency_level: str = "medium"

            class Config:
                extra = "forbid"

        return NCRPComplaint

    def _get_bank_transaction_schema(self):
        """Bank transaction schema"""
        class BankTransaction(BaseModel):
            transaction_id: str
            account_id: str
            amount: float
            transaction_type: str
            timestamp: datetime
            location: Optional[Dict[str, float]] = None
            risk_score: float = 0.0

            class Config:
                extra = "forbid"

        return BankTransaction

    def _get_i4c_schema(self):
        """I4C crime record schema"""
        class I4CCrimeRecord(BaseModel):
            case_id: str
            crime_date: datetime
            crime_category: str
            location: Dict[str, float]
            financial_loss: Optional[float] = None
            sophistication_level: str = "medium"

            class Config:
                extra = "forbid"

        return I4CCrimeRecord

    def _get_citizen_report_schema(self):
        """Citizen report schema"""
        class CitizenReport(BaseModel):
            report_id: str
            scam_type: str
            amount: float
            location: Dict[str, float]
            timestamp: datetime
            contact_consent: bool = False

            class Config:
                extra = "forbid"

        return CitizenReport

    def _get_lea_feedback_schema(self):
        """LEA feedback schema"""
        class LEAFeedback(BaseModel):
            feedback_id: str
            alert_id: str
            action: str
            timestamp: datetime
            notes: Optional[str] = None

            class Config:
                extra = "forbid"

        return LEAFeedback

    def _get_system_alert_schema(self):
        """System alert schema"""
        class SystemAlert(BaseModel):
            alert_id: str
            alert_type: str
            severity: str
            message: str
            timestamp: datetime
            source: str

            class Config:
                extra = "forbid"

        return SystemAlert

class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.symmetric_key = config.get('encryption_key').encode()
        self.cipher_suite = Fernet(self.symmetric_key)

        # Load or generate RSA key pair for asymmetric encryption
        self._load_or_generate_rsa_keys()

    def _load_or_generate_rsa_keys(self):
        """Load or generate RSA key pairs"""
        private_key_path = self.config.get('private_key_path', 'kafka_private_key.pem')
        public_key_path = self.config.get('public_key_path', 'kafka_public_key.pem')

        try:
            # Try to load existing keys
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )

            with open(public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            logger.info("Loaded existing RSA keys")
        except FileNotFoundError:
            # Generate new keys
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()

            # Save keys
            with open(private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            with open(public_key_path, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            logger.info("Generated new RSA keys")

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data using symmetric encryption"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data using symmetric encryption"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise

    def encrypt_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt entire message for secure transmission"""
        try:
            # Serialize message
            message_json = json.dumps(message, default=str)

            # Encrypt with symmetric key
            encrypted_message = self.encrypt_sensitive_data(message_json)

            return {
                'encrypted_payload': encrypted_message,
                'encryption_method': 'AES-256',
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': str(uuid.uuid4())
            }
        except Exception as e:
            logger.error(f"Message encryption error: {str(e)}")
            raise

    def decrypt_message(self, encrypted_message: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt entire message"""
        try:
            if 'encrypted_payload' not in encrypted_message:
                return encrypted_message  # Not encrypted

            decrypted_json = self.decrypt_sensitive_data(encrypted_message['encrypted_payload'])
            return json.loads(decrypted_json)
        except Exception as e:
            logger.error(f"Message decryption error: {str(e)}")
            raise

class DataQualityChecker:
    """Data quality validation and enhancement"""

    def __init__(self):
        self.quality_rules = {
            'required_fields': self._get_required_fields_rules(),
            'data_ranges': self._get_data_range_rules(),
            'format_validation': self._get_format_validation_rules(),
            'business_rules': self._get_business_rules()
        }

    def check_data_quality(self, message_type: str, data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Check data quality and return results"""
        issues = []
        enhancements = {}

        # Check required fields
        required_fields = self.quality_rules['required_fields'].get(message_type, [])
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(f"Missing required field: {field}")

        # Check data ranges
        range_rules = self.quality_rules['data_ranges'].get(message_type, {})
        for field, (min_val, max_val) in range_rules.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if not (min_val <= value <= max_val):
                        issues.append(f"Value {value} for field {field} outside range [{min_val}, {max_val}]")
                except (ValueError, TypeError):
                    issues.append(f"Invalid numeric value for field {field}")

        # Check format validation
        format_rules = self.quality_rules['format_validation'].get(message_type, {})
        for field, validation_func in format_rules.items():
            if field in data and data[field] is not None:
                if not validation_func(data[field]):
                    issues.append(f"Invalid format for field {field}")

        # Apply business rules and enhancements
        business_rules = self.quality_rules['business_rules'].get(message_type, [])
        for rule_func in business_rules:
            try:
                rule_issues, rule_enhancements = rule_func(data)
                issues.extend(rule_issues)
                enhancements.update(rule_enhancements)
            except Exception as e:
                logger.warning(f"Business rule error: {str(e)}")

        # Calculate quality score
        quality_score = max(0, 100 - len(issues) * 10)
        enhancements['quality_score'] = quality_score

        is_high_quality = quality_score >= 80
        return is_high_quality, issues, enhancements

    def _get_required_fields_rules(self) -> Dict[str, List[str]]:
        """Define required fields for each message type"""
        return {
            'ncrp_complaint': ['complaint_id', 'timestamp', 'scam_type', 'amount', 'victim_location'],
            'bank_transaction': ['transaction_id', 'account_id', 'amount', 'transaction_type', 'timestamp'],
            'i4c_crime_record': ['case_id', 'crime_date', 'crime_category', 'location'],
            'citizen_report': ['report_id', 'scam_type', 'amount', 'location', 'timestamp'],
            'lea_feedback': ['feedback_id', 'alert_id', 'action', 'timestamp'],
            'system_alert': ['alert_id', 'alert_type', 'severity', 'message', 'timestamp']
        }

    def _get_data_range_rules(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Define valid ranges for numeric fields"""
        return {
            'ncrp_complaint': {
                'amount': (100, 10000000),  # ₹100 to ₹1 crore
                'urgency_level': (1, 5)
            },
            'bank_transaction': {
                'amount': (0.01, 100000000),  # ₹0.01 to ₹10 crore
                'risk_score': (0, 1)
            },
            'citizen_report': {
                'amount': (100, 10000000)
            }
        }

    def _get_format_validation_rules(self) -> Dict[str, Dict[str, Callable]]:
        """Define format validation functions"""
        def validate_timestamp(value):
            try:
                datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return True
            except ValueError:
                return False

        def validate_location(value):
            return isinstance(value, dict) and 'lat' in value and 'lon' in value

        def validate_coordinates(value):
            try:
                lat, lon = float(value.get('lat', 0)), float(value.get('lon', 0))
                return -90 <= lat <= 90 and -180 <= lon <= 180
            except (ValueError, TypeError):
                return False

        return {
            'ncrp_complaint': {
                'timestamp': validate_timestamp,
                'victim_location': validate_location
            },
            'bank_transaction': {
                'timestamp': validate_timestamp,
                'location': lambda x: x is None or validate_location(x)
            },
            'i4c_crime_record': {
                'crime_date': validate_timestamp,
                'location': validate_location
            },
            'citizen_report': {
                'timestamp': validate_timestamp,
                'location': validate_location
            }
        }

    def _get_business_rules(self) -> Dict[str, List[Callable]]:
        """Define business rule validation functions"""
        def validate_scam_amount_consistency(data):
            issues = []
            enhancements = {}

            if 'scam_type' in data and 'amount' in data:
                scam_type = data['scam_type']
                amount = float(data['amount'])

                # Business rule: Different scam types have typical amount ranges
                if scam_type == 'FAKE_LOAN_APP' and amount > 50000:
                    issues.append("Unusually high amount for fake loan app")
                elif scam_type == 'UPI_PHISHING' and amount > 100000:
                    issues.append("Unusually high amount for UPI phishing")

                # Add amount categorization
                if amount < 1000:
                    enhancements['amount_category'] = 'small'
                elif amount < 10000:
                    enhancements['amount_category'] = 'medium'
                elif amount < 100000:
                    enhancements['amount_category'] = 'large'
                else:
                    enhancements['amount_category'] = 'very_large'

            return issues, enhancements

        def validate_transaction_risk_score(data):
            issues = []
            enhancements = {}

            if 'amount' in data and 'transaction_type' in data:
                amount = float(data['amount'])
                txn_type = data['transaction_type']

                # Calculate risk score if not provided
                if 'risk_score' not in data:
                    risk_score = 0.1  # Base risk

                    # Amount-based risk
                    if amount > 100000:
                        risk_score += 0.3
                    elif amount > 50000:
                        risk_score += 0.2
                    elif amount > 10000:
                        risk_score += 0.1

                    # Transaction type risk
                    high_risk_types = ['TRANSFER_OUT', 'UPI_TRANSACTION', 'ONLINE_PAYMENT']
                    if txn_type in high_risk_types:
                        risk_score += 0.2

                    enhancements['calculated_risk_score'] = min(1.0, risk_score)

            return issues, enhancements

        return {
            'ncrp_complaint': [validate_scam_amount_consistency],
            'bank_transaction': [validate_transaction_risk_score],
            'citizen_report': [validate_scam_amount_consistency]
        }

class KafkaPipelineManager:
    """Main Kafka pipeline manager for data ingestion"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kafka_config = config.get('kafka', {})
        self.encryption_manager = EncryptionManager(config.get('encryption', {}))
        self.schema_validator = DataSchemaValidator()
        self.quality_checker = DataQualityChecker()

        # Database setup
        self.engine = create_engine(config.get('database_url', 'sqlite:///aegis_kafka.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis for caching and metrics
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 3),
            decode_responses=True
        )

        # Pipeline components
        self.producer = None
        self.consumers = {}
        self.metrics = IngestionMetrics()
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_workers', 10))

        # Topic configuration
        self.topics = {
            'ingest_raw': 'aegis-raw-data',
            'process_validated': 'aegis-validated-data',
            'alerts': 'aegis-alerts',
            'dead_letter': 'aegis-dead-letter',
            'monitoring': 'aegis-monitoring'
        }

        # Shutdown handling
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown_event.set()

    async def initialize(self):
        """Initialize the Kafka pipeline"""
        logger.info("Initializing Kafka Data Ingestion Pipeline")

        # Initialize Kafka producer
        await self._initialize_producer()

        # Initialize consumers for each topic
        await self._initialize_consumers()

        # Test Kafka connectivity
        await self._test_kafka_connectivity()

        # Start Prometheus metrics server
        self._start_metrics_server()

        logger.info("Kafka pipeline initialized successfully")

    async def _initialize_producer(self):
        """Initialize Kafka producer with security configuration"""
        producer_config = {
            'bootstrap_servers': self.kafka_config.get('bootstrap_servers', 'localhost:9092'),
            'value_serializer': lambda v: json.dumps(v, default=str).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'acks': 'all',
            'retries': 3,
            'batch_size': 16384,
            'linger_ms': 10,
            'compression_type': 'gzip'
        }

        # Add SSL configuration if specified
        if self.kafka_config.get('ssl_enabled', False):
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(self.kafka_config.get('ca_cert_path'))
            ssl_context.load_cert_chain(
                self.kafka_config.get('cert_path'),
                self.kafka_config.get('key_path')
            )
            producer_config['security_protocol'] = 'SSL'
            producer_config['ssl_context'] = ssl_context

        # Add SASL configuration if specified
        if self.kafka_config.get('sasl_enabled', False):
            producer_config.update({
                'security_protocol': 'SASL_SSL',
                'sasl_mechanism': self.kafka_config.get('sasl_mechanism', 'PLAIN'),
                'sasl_plain_username': self.kafka_config.get('sasl_username'),
                'sasl_plain_password': self.kafka_config.get('sasl_password')
            })

        self.producer = AIOKafkaProducer(**producer_config)
        await self.producer.start()
        logger.info("Kafka producer initialized")

    async def _initialize_consumers(self):
        """Initialize Kafka consumers for different topics"""
        consumer_config = {
            'bootstrap_servers': self.kafka_config.get('bootstrap_servers', 'localhost:9092'),
            'value_deserializer': lambda v: json.loads(v.decode('utf-8')),
            'key_deserializer': lambda k: k.decode('utf-8') if k else None,
            'group_id': 'aegis-data-processor',
            'auto_offset_reset': 'latest',
            'enable_auto_commit': False,
            'max_poll_records': 100,
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 3000
        }

        # Add security configuration (same as producer)
        if self.kafka_config.get('ssl_enabled', False):
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(self.kafka_config.get('ca_cert_path'))
            consumer_config['security_protocol'] = 'SSL'
            consumer_config['ssl_context'] = ssl_context

        if self.kafka_config.get('sasl_enabled', False):
            consumer_config.update({
                'security_protocol': 'SASL_SSL',
                'sasl_mechanism': self.kafka_config.get('sasl_mechanism', 'PLAIN'),
                'sasl_plain_username': self.kafka_config.get('sasl_username'),
                'sasl_plain_password': self.kafka_config.get('sasl_password')
            })

        # Create consumer for raw data ingestion
        raw_consumer = AIOKafkaConsumer(
            self.topics['ingest_raw'],
            **consumer_config
        )
        self.consumers['raw'] = raw_consumer

        # Create consumer for validated data processing
        validated_consumer = AIOKafkaConsumer(
            self.topics['process_validated'],
            **consumer_config
        )
        self.consumers['validated'] = validated_consumer

        logger.info("Kafka consumers initialized")

    async def _test_kafka_connectivity(self):
        """Test Kafka connectivity"""
        try:
            # Test producer by sending a test message
            test_message = {
                'type': 'test',
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Kafka connectivity test'
            }

            await self.producer.send_and_wait(
                self.topics['monitoring'],
                key='test',
                value=test_message
            )
            logger.info("Kafka connectivity test successful")

        except Exception as e:
            logger.error(f"Kafka connectivity test failed: {str(e)}")
            raise

    def _start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            metrics_port = self.config.get('metrics_port', 8001)
            prom.start_http_server(metrics_port)
            logger.info(f"Prometheus metrics server started on port {metrics_port}")
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {str(e)}")

    async def ingest_data(self, data_source: DataSource, message: Dict[str, Any], priority: DataPriority = DataPriority.NORMAL) -> bool:
        """
        Ingest data into the Kafka pipeline
        """
        start_time = time.time()

        try:
            # Validate message schema
            message_type = message.get('type', data_source.value)
            is_valid, validation_error = self.schema_validator.validate_message(message_type, message)

            if not is_valid:
                logger.error(f"Schema validation failed: {validation_error}")
                await self._send_to_dead_letter_queue(data_source, message, f"Schema validation failed: {validation_error}")
                return False

            # Check data quality
            is_high_quality, quality_issues, enhancements = self.quality_checker.check_data_quality(message_type, message)

            # Add metadata
            enriched_message = {
                'id': str(uuid.uuid4()),
                'source': data_source.value,
                'type': message_type,
                'timestamp': datetime.utcnow().isoformat(),
                'priority': priority.value,
                'quality_score': enhancements.get('quality_score', 100),
                'quality_issues': quality_issues,
                'data': message,
                **enhancements
            }

            # Encrypt sensitive data if required
            if self.config.get('encrypt_messages', False):
                enriched_message = self.encryption_manager.encrypt_message(enriched_message)

            # Send to raw data topic
            await self.producer.send_and_wait(
                self.topics['ingest_raw'],
                key=f"{data_source.value}_{message.get('id', 'unknown')}",
                value=enriched_message
            )

            # Update metrics
            self.metrics.messages_received += 1
            self.metrics.last_message_timestamp = datetime.utcnow()
            MESSAGES_RECEIVED_TOTAL.labels(source=data_source.value, topic=self.topics['ingest_raw']).inc()

            # Log successful ingestion
            processing_time = (time.time() - start_time) * 1000
            logger.info(
                "Data ingested successfully",
                source=data_source.value,
                message_type=message_type,
                processing_time_ms=processing_time,
                quality_score=enriched_message.get('quality_score', 100)
            )

            PROCESSING_LATENCY.observe(processing_time / 1000)

            return True

        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
            await self._send_to_dead_letter_queue(data_source, message, f"Ingestion failed: {str(e)}")
            self.metrics.messages_failed += 1
            MESSAGES_PROCESSED_TOTAL.labels(source=data_source.value, status='failed').inc()
            return False

    async def _send_to_dead_letter_queue(self, data_source: DataSource, message: Dict[str, Any], error_reason: str):
        """Send failed messages to dead letter queue"""
        dead_letter_message = {
            'original_message': message,
            'source': data_source.value,
            'error_reason': error_reason,
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': 0
        }

        try:
            await self.producer.send_and_wait(
                self.topics['dead_letter'],
                key=f"dlq_{data_source.value}",
                value=dead_letter_message
            )
            logger.warning(f"Message sent to dead letter queue: {error_reason}")
        except Exception as e:
            logger.error(f"Failed to send to dead letter queue: {str(e)}")

    async def process_raw_data(self):
        """Process messages from raw data topic"""
        logger.info("Starting raw data processing consumer")

        consumer = self.consumers['raw']
        await consumer.start()

        try:
            async for msg in consumer:
                if self.shutdown_event.is_set():
                    break

                await self._process_raw_message(msg)

        except Exception as e:
            logger.error(f"Raw data processing error: {str(e)}")
        finally:
            await consumer.stop()

    async def _process_raw_message(self, msg):
        """Process individual raw message"""
        start_time = time.time()

        try:
            # Decrypt message if encrypted
            if isinstance(msg.value, dict) and 'encrypted_payload' in msg.value:
                message_data = self.encryption_manager.decrypt_message(msg.value)
            else:
                message_data = msg.value

            source = message_data.get('source')
            message_type = message_data.get('type')
            priority = message_data.get('priority', DataPriority.NORMAL.value)
            data = message_data.get('data')

            # Additional processing and validation
            processed_data = await self._enrich_message_data(message_data)

            # Route to appropriate processing topic
            if message_data.get('quality_score', 100) >= 70:
                await self.producer.send_and_wait(
                    self.topics['process_validated'],
                    key=f"{source}_{message_type}",
                    value=processed_data
                )

                self.metrics.messages_processed += 1
                MESSAGES_PROCESSED_TOTAL.labels(source=source, status='processed').inc()
            else:
                await self._send_to_dead_letter_queue(
                    DataSource(source),
                    data,
                    f"Low quality score: {message_data.get('quality_score', 0)}"
                )
                self.metrics.messages_quarantined += 1

            # Update processing metrics
            processing_time = (time.time() - start_time) * 1000
            self.metrics.processing_latency_ms = processing_time

            # Calculate throughput (simple moving average)
            current_time = datetime.utcnow()
            if self.metrics.last_message_timestamp:
                time_diff = (current_time - self.metrics.last_message_timestamp).total_seconds()
                if time_diff > 0:
                    self.metrics.throughput_msgs_per_sec = 1.0 / time_diff

            self.metrics.last_message_timestamp = current_time

            # Update Prometheus metrics
            PROCESSING_LATENCY.observe(processing_time / 1000)
            THROUGHPUT.set(self.metrics.throughput_msgs_per_sec)

            # Commit offset
            await consumer.commit()

        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}")
            self.metrics.messages_failed += 1
            MESSAGES_PROCESSED_TOTAL.labels(source='unknown', status='failed').inc()

    async def _enrich_message_data(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich message data with additional context"""
        enriched_data = message_data.copy()

        try:
            # Add processing timestamp
            enriched_data['processed_at'] = datetime.utcnow().isoformat()

            # Add geographic clustering if location data present
            data = message_data.get('data', {})
            if 'location' in data or 'victim_location' in data:
                location = data.get('location') or data.get('victim_location')
                if isinstance(location, dict) and 'lat' in location and 'lon' in location:
                    # Add location cluster
                    location_cluster = self._get_location_cluster(location['lat'], location['lon'])
                    enriched_data['location_cluster'] = location_cluster

                    # Add geographic context
                    enriched_data['geographic_context'] = self._get_geographic_context(location['lat'], location['lon'])

            # Add temporal context
            if 'timestamp' in data:
                timestamp = data['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                enriched_data['temporal_context'] = {
                    'hour_of_day': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'month': timestamp.month,
                    'is_weekend': timestamp.weekday() >= 5,
                    'is_business_hours': 9 <= timestamp.hour <= 17
                }

            # Add priority-based routing
            priority = message_data.get('priority', DataPriority.NORMAL.value)
            if priority >= DataPriority.HIGH.value:
                enriched_data['requires_immediate_processing'] = True

            return enriched_data

        except Exception as e:
            logger.warning(f"Message enrichment failed: {str(e)}")
            return message_data

    def _get_location_cluster(self, lat: float, lon: float) -> str:
        """Get location cluster from coordinates"""
        # Simple grid-based clustering (approximately 1km x 1km grid)
        lat_grid = int(lat * 100)
        lon_grid = int(lon * 100)
        return f"cluster_{lat_grid:04d}_{lon_grid:04d}"

    def _get_geographic_context(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get geographic context for coordinates"""
        # Simplified geographic context (in production, use reverse geocoding)
        context = {
            'urban_density': 'high' if 28.0 <= lat <= 29.0 and 76.5 <= lon <= 78.0 else 'medium',
            'region': 'north_india' if lat > 20 else 'south_india',
            'coastal': False  # Simplified
        }
        return context

    async def process_validated_data(self):
        """Process messages from validated data topic"""
        logger.info("Starting validated data processing consumer")

        consumer = self.consumers['validated']
        await consumer.start()

        try:
            async for msg in consumer:
                if self.shutdown_event.is_set():
                    break

                await self._process_validated_message(msg)

        except Exception as e:
            logger.error(f"Validated data processing error: {str(e)}")
        finally:
            await consumer.stop()

    async def _process_validated_message(self, msg):
        """Process individual validated message"""
        try:
            message_data = msg.value
            source = message_data.get('source')
            message_type = message_data.get('type')
            data = message_data.get('data')

            # Route to appropriate processing pipeline
            if source == DataSource.NCRP.value:
                await self._process_ncrp_data(message_data)
            elif source == DataSource.CFCFRMS.value:
                await self._process_cfcfrms_data(message_data)
            elif source == DataSource.I4C.value:
                await self._process_i4c_data(message_data)
            elif source == 'citizen_reports':
                await self._process_citizen_report(message_data)
            else:
                await self._process_generic_data(message_data)

            await consumer.commit()

        except Exception as e:
            logger.error(f"Validated message processing failed: {str(e)}")

    async def _process_ncrp_data(self, message_data: Dict[str, Any]):
        """Process NCRP data"""
        # In production, this would trigger NCRP-specific processing
        logger.info("Processing NCRP data", message_id=message_data.get('id'))

        # Store in database, trigger predictions, etc.
        await self._store_processed_data(message_data)

    async def _process_cfcfrms_data(self, message_data: Dict[str, Any]):
        """Process CFCFRMS data"""
        logger.info("Processing CFCFRMS data", message_id=message_data.get('id'))

        # Trigger fraud detection, etc.
        await self._store_processed_data(message_data)

    async def _process_i4c_data(self, message_data: Dict[str, Any]):
        """Process I4C data"""
        logger.info("Processing I4C data", message_id=message_data.get('id'))

        # Update historical patterns, etc.
        await self._store_processed_data(message_data)

    async def _process_citizen_report(self, message_data: Dict[str, Any]):
        """Process citizen report"""
        logger.info("Processing citizen report", message_id=message_data.get('id'))

        # Trigger immediate analysis if high priority
        if message_data.get('priority', 2) >= DataPriority.HIGH.value:
            await self._send_alert(message_data, 'high_priority_citizen_report')

        await self._store_processed_data(message_data)

    async def _process_generic_data(self, message_data: Dict[str, Any]):
        """Process generic data"""
        logger.info("Processing generic data", source=message_data.get('source'))
        await self._store_processed_data(message_data)

    async def _store_processed_data(self, message_data: Dict[str, Any]):
        """Store processed data in database"""
        # Implement database storage logic
        pass

    async def _send_alert(self, message_data: Dict[str, Any], alert_type: str):
        """Send alert message"""
        alert_message = {
            'alert_id': str(uuid.uuid4()),
            'alert_type': alert_type,
            'source_message_id': message_data.get('id'),
            'source': message_data.get('source'),
            'severity': 'high' if message_data.get('priority', 2) >= DataPriority.HIGH.value else 'medium',
            'message': f"High priority {message_data.get('type')} received",
            'timestamp': datetime.utcnow().isoformat(),
            'data': message_data
        }

        try:
            await self.producer.send_and_wait(
                self.topics['alerts'],
                key=alert_type,
                value=alert_message
            )
            logger.info("Alert sent successfully", alert_type=alert_type)
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")

    async def start_pipeline(self):
        """Start the complete data ingestion pipeline"""
        logger.info("Starting Kafka data ingestion pipeline")

        # Start all processing tasks
        tasks = [
            asyncio.create_task(self.process_raw_data()),
            asyncio.create_task(self.process_validated_data()),
            asyncio.create_task(self._monitor_pipeline_health()),
            asyncio.create_task(self._update_metrics())
        ]

        try:
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            logger.info("Shutdown signal received, stopping pipeline")

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
        finally:
            # Cancel all tasks
            for task in tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _monitor_pipeline_health(self):
        """Monitor pipeline health and performance"""
        while not self.shutdown_event.is_set():
            try:
                # Calculate error rate
                total_messages = self.metrics.messages_received
                failed_messages = self.metrics.messages_failed

                if total_messages > 0:
                    self.metrics.error_rate = failed_messages / total_messages
                    ERROR_RATE.set(self.metrics.error_rate)

                # Log health status
                logger.info(
                    "Pipeline health status",
                    messages_received=self.metrics.messages_received,
                    messages_processed=self.metrics.messages_processed,
                    messages_failed=self.metrics.messages_failed,
                    error_rate=self.metrics.error_rate,
                    throughput=self.metrics.throughput_msgs_per_sec
                )

                # Check for health issues
                if self.metrics.error_rate > 0.1:  # 10% error rate
                    logger.warning("High error rate detected", error_rate=self.metrics.error_rate)

                if self.metrics.throughput_msgs_per_sec < 1.0:  # Low throughput
                    logger.warning("Low throughput detected", throughput=self.metrics.throughput_msgs_per_sec)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _update_metrics(self):
        """Update pipeline metrics"""
        while not self.shutdown_event.is_set():
            try:
                # Cache metrics in Redis
                metrics_data = {
                    'messages_received': self.metrics.messages_received,
                    'messages_processed': self.metrics.messages_processed,
                    'messages_failed': self.metrics.messages_failed,
                    'error_rate': self.metrics.error_rate,
                    'throughput': self.metrics.throughput_msgs_per_sec,
                    'last_message_timestamp': self.metrics.last_message_timestamp.isoformat() if self.metrics.last_message_timestamp else None,
                    'updated_at': datetime.utcnow().isoformat()
                }

                self.redis_client.setex(
                    'kafka_pipeline_metrics',
                    300,  # 5 minutes TTL
                    json.dumps(metrics_data, default=str)
                )

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Metrics update error: {str(e)}")
                await asyncio.sleep(30)

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'status': 'running' if not self.shutdown_event.is_set() else 'stopped',
            'metrics': asdict(self.metrics),
            'topics': self.topics,
            'consumers_active': len(self.consumers),
            'last_updated': datetime.utcnow().isoformat()
        }

    async def cleanup(self):
        """Cleanup pipeline resources"""
        logger.info("Cleaning up Kafka pipeline")

        # Stop producer
        if self.producer:
            await self.producer.stop()

        # Stop consumers
        for consumer in self.consumers.values():
            await consumer.stop()

        # Close thread pool
        self.executor.shutdown(wait=True)

        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()

        logger.info("Kafka pipeline cleanup completed")

# Configuration and initialization
async def create_kafka_pipeline(config: Dict[str, Any]) -> KafkaPipelineManager:
    """Create and initialize Kafka pipeline"""
    pipeline = KafkaPipelineManager(config)
    await pipeline.initialize()
    return pipeline

# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'kafka': {
            'bootstrap_servers': 'localhost:9092',
            'ssl_enabled': False,
            'sasl_enabled': False
        },
        'encryption': {
            'encryption_key': Fernet.generate_key().decode()
        },
        'database_url': 'sqlite:///aegis_kafka.db',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'encrypt_messages': True,
        'max_workers': 10,
        'metrics_port': 8001
    }

    async def main():
        # Create and start pipeline
        pipeline = await create_kafka_pipeline(config)

        try:
            # Start the pipeline
            await pipeline.start_pipeline()
        except KeyboardInterrupt:
            logger.info("Shutting down Kafka pipeline")
        finally:
            await pipeline.cleanup()

    # Run the pipeline
    asyncio.run(main())