"""
Kafka-based Data Ingestion Pipeline
Real-time data streaming from NCRP, CFCFRMS, and I4C sources
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import aioredis
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
from data_sources.ncrp_integration import ncrp_integration
from data_sources.bank_integration import bank_integration
from data_sources.i4c_integration import i4c_integration

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """
    Data source types for ingestion
    """
    NCRP = "ncrp"
    BANK = "bank"
    I4C = "i4c"
    SYSTEM = "system"

class DataPriority(Enum):
    """
    Data processing priority levels
    """
    CRITICAL = 1    # Immediate processing (e.g., active threats)
    HIGH = 2        # High priority (e.g., suspicious transactions)
    NORMAL = 3      # Normal processing
    LOW = 4         # Batch processing (e.g., historical data)

@dataclass
class DataMessage:
    """
    Standardized data message format
    """
    message_id: str
    source_type: DataSourceType
    source_id: str
    timestamp: datetime
    priority: DataPriority
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_attempts: int = 0
    max_retries: int = 3

class KafkaDataIngestion:
    """
    Kafka-based data ingestion pipeline for real-time cybercrime data
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = {}
        self.redis_client = None
        self.is_running = False

        # Kafka topics
        self.topics = {
            DataSourceType.NCRP: "ncrp-complaints",
            DataSourceType.BANK: "bank-transactions",
            DataSourceType.I4C: "i4c-crime-data",
            DataSourceType.SYSTEM: "system-events"
        }

        # Processing queues
        self.processing_queues = {
            DataSourceType.NCRP: asyncio.Queue(),
            DataSourceType.BANK: asyncio.Queue(),
            DataSourceType.I4C: asyncio.Queue(),
            DataSourceType.SYSTEM: asyncio.Queue()
        }

        # Data processors
        self.data_processors = {}
        self.error_handlers = {}

        # Metrics
        self.metrics = {
            'messages_produced': 0,
            'messages_consumed': 0,
            'processing_errors': 0,
            'messages_by_source': {source.value: 0 for source in DataSourceType},
            'avg_processing_time': 0.0,
            'queue_sizes': {source.value: 0 for source in DataSourceType}
        }

    async def initialize(self) -> bool:
        """
        Initialize Kafka producer, consumers, and Redis connection
        """
        try:
            logger.info("[Kafka Ingestion] Initializing data ingestion pipeline...")

            # Initialize Redis for caching and coordination
            self.redis_client = await aioredis.from_url("redis://localhost:6379", decode_responses=True)

            # Initialize Kafka producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str),
                key_serializer=lambda k: k.encode() if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432
            )

            await self.producer.start()
            logger.info("[Kafka Ingestion] Kafka producer started")

            # Initialize consumers for each topic
            for source_type, topic in self.topics.items():
                consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=f"aegis-{source_type.value}-processor",
                    value_deserializer=lambda v: json.loads(v.decode()),
                    auto_offset_reset='latest',
                    enable_auto_commit=False,
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=3000
                )
                await consumer.start()
                self.consumers[source_type] = consumer
                logger.info(f"[Kafka Ingestion] Consumer started for {source_type.value}")

            # Register default processors
            await self._register_default_processors()

            self.is_running = True
            logger.info("[Kafka Ingestion] Pipeline initialized successfully")

            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error initializing pipeline: {str(e)}")
            return False

    async def _register_default_processors(self) -> None:
        """
        Register default data processors for each source type
        """
        # NCRP complaint processor
        self.data_processors[DataSourceType.NCRP] = self._process_ncrp_message

        # Bank transaction processor
        self.data_processors[DataSourceType.BANK] = self._process_bank_message

        # I4C crime data processor
        self.data_processors[DataSourceType.I4C] = self._process_i4c_message

        # System event processor
        self.data_processors[DataSourceType.SYSTEM] = self._process_system_message

        # Default error handler
        self.error_handlers['default'] = self._handle_processing_error

    async def start_ingestion(self) -> None:
        """
        Start the data ingestion process
        """
        try:
            logger.info("[Kafka Ingestion] Starting data ingestion...")

            # Start consumer tasks for each source
            consumer_tasks = []
            for source_type in self.topics.keys():
                task = asyncio.create_task(
                    self._consume_messages(source_type)
                )
                consumer_tasks.append(task)

            # Start processing tasks for each queue
            processing_tasks = []
            for source_type in DataSourceType:
                task = asyncio.create_task(
                    self._process_queue(source_type)
                )
                processing_tasks.append(task)

            # Start metrics collection
            metrics_task = asyncio.create_task(
                self._collect_metrics()
            )

            # Start health monitoring
            health_task = asyncio.create_task(
                self._health_monitor()
            )

            logger.info("[Kafka Ingestion] Data ingestion started")

            # Wait for all tasks (they run indefinitely)
            await asyncio.gather(
                *consumer_tasks, *processing_tasks,
                metrics_task, health_task,
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error starting ingestion: {str(e)}")
            await self.shutdown()

    async def _consume_messages(self, source_type: DataSourceType) -> None:
        """
        Consume messages from Kafka topic
        """
        try:
            consumer = self.consumers[source_type]
            queue = self.processing_queues[source_type]

            logger.info(f"[Kafka Ingestion] Starting consumer for {source_type.value}")

            while self.is_running:
                try:
                    # Poll for messages
                    msg_pack = await consumer.getmany(timeout_ms=1000, max_records=100)

                    for topic_partition, messages in msg_pack.items():
                        for message in messages:
                            try:
                                # Parse message
                                data_message = self._parse_message(message.value, source_type)

                                if data_message:
                                    # Add to processing queue
                                    await queue.put(data_message)
                                    self.metrics['messages_consumed'] += 1
                                    self.metrics['messages_by_source'][source_type.value] += 1

                                # Commit offset
                                await consumer.commit()

                            except Exception as e:
                                logger.error(f"[Kafka Ingestion] Error processing message from {source_type.value}: {str(e)}")
                                self.metrics['processing_errors'] += 1

                except Exception as e:
                    logger.error(f"[Kafka Ingestion] Consumer error for {source_type.value}: {str(e)}")
                    await asyncio.sleep(1)  # Brief pause before retry

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Fatal error in consumer for {source_type.value}: {str(e)}")

    def _parse_message(self, raw_message: Dict, source_type: DataSourceType) -> Optional[DataMessage]:
        """
        Parse raw message into standardized format
        """
        try:
            # Extract basic fields
            message_id = raw_message.get('message_id', str(uuid.uuid4()))
            source_id = raw_message.get('source_id', 'unknown')
            timestamp = datetime.fromisoformat(raw_message.get('timestamp', datetime.utcnow().isoformat()))

            # Determine priority
            priority = self._determine_priority(raw_message, source_type)

            # Extract data and metadata
            data = raw_message.get('data', {})
            metadata = raw_message.get('metadata', {})

            # Create standardized message
            message = DataMessage(
                message_id=message_id,
                source_type=source_type,
                source_id=source_id,
                timestamp=timestamp,
                priority=priority,
                data=data,
                metadata=metadata
            )

            return message

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error parsing message: {str(e)}")
            return None

    def _determine_priority(self, message: Dict, source_type: DataSourceType) -> DataPriority:
        """
        Determine processing priority based on message content
        """
        try:
            # Critical indicators
            critical_indicators = [
                'active_threat',
                'immediate_danger',
                'emergency',
                'high_risk',
                'suspicious_activity'
            ]

            # Check for critical indicators
            for indicator in critical_indicators:
                if indicator in str(message).lower():
                    return DataPriority.CRITICAL

            # High priority indicators
            high_indicators = [
                'suspicious',
                'anomaly',
                'unusual',
                'fraud_signals',
                'high_amount'
            ]

            for indicator in high_indicators:
                if indicator in str(message).lower():
                    return DataPriority.HIGH

            # Source-specific priority logic
            if source_type == DataSourceType.NCRP:
                amount = message.get('data', {}).get('amount', 0)
                if amount > 50000:  # High value complaints
                    return DataPriority.HIGH

            elif source_type == DataSourceType.BANK:
                risk_score = message.get('data', {}).get('risk_score', 0)
                if risk_score > 0.8:  # High risk transactions
                    return DataPriority.HIGH

            return DataPriority.NORMAL

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error determining priority: {str(e)}")
            return DataPriority.NORMAL

    async def _process_queue(self, source_type: DataSourceType) -> None:
        """
        Process messages from the queue
        """
        try:
            queue = self.processing_queues[source_type]
            processor = self.data_processors.get(source_type)

            if not processor:
                logger.warning(f"[Kafka Ingestion] No processor registered for {source_type.value}")
                return

            logger.info(f"[Kafka Ingestion] Starting processor for {source_type.value}")

            while self.is_running:
                try:
                    # Get message from queue
                    message = await queue.get()

                    # Process message
                    start_time = datetime.utcnow()
                    success = await processor(message)
                    processing_time = (datetime.utcnow() - start_time).total_seconds()

                    # Update metrics
                    self._update_processing_metrics(processing_time)

                    if not success:
                        # Handle processing failure
                        await self._handle_processing_failure(message, source_type)

                    # Mark task as done
                    queue.task_done()

                except Exception as e:
                    logger.error(f"[Kafka Ingestion] Error processing queue for {source_type.value}: {str(e)}")
                    self.metrics['processing_errors'] += 1
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Fatal error in processor for {source_type.value}: {str(e)}")

    async def _process_ncrp_message(self, message: DataMessage) -> bool:
        """
        Process NCRP complaint message
        """
        try:
            data = message.data

            # Validate required fields
            if not all(key in data for key in ['scam_type', 'amount', 'victim_location']):
                logger.warning(f"[Kafka Ingestion] Invalid NCRP message: missing required fields")
                return False

            # Store complaint in database
            await self._store_ncrp_complaint(data)

            # Cache for real-time access
            await self._cache_complaint_data(message.message_id, data)

            # Trigger AI prediction if high priority
            if message.priority in [DataPriority.CRITICAL, DataPriority.HIGH]:
                await self._trigger_ai_prediction(data, 'ncrp')

            # Publish processed event
            await self._publish_processed_event(message, 'ncrp_processed')

            logger.debug(f"[Kafka Ingestion] Processed NCRP complaint: {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error processing NCRP message: {str(e)}")
            return False

    async def _process_bank_message(self, message: DataMessage) -> bool:
        """
        Process bank transaction message
        """
        try:
            data = message.data

            # Validate required fields
            if not all(key in data for key in ['transaction_id', 'bank_code', 'transaction_type', 'amount']):
                logger.warning(f"[Kafka Ingestion] Invalid bank message: missing required fields")
                return False

            # Store transaction in database
            await self._store_bank_transaction(data)

            # Check for suspicious patterns
            is_suspicious = await self._analyze_transaction_suspicion(data)

            if is_suspicious:
                # Cache suspicious transaction
                await self._cache_suspicious_transaction(message.message_id, data)

                # Trigger AI analysis
                await self._trigger_ai_prediction(data, 'bank')

                # Publish alert
                await self._publish_alert(message, data)

            # Publish processed event
            await self._publish_processed_event(message, 'bank_processed')

            logger.debug(f"[Kafka Ingestion] Processed bank transaction: {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error processing bank message: {str(e)}")
            return False

    async def _process_i4c_message(self, message: DataMessage) -> bool:
        """
        Process I4C crime data message
        """
        try:
            data = message.data

            # Validate required fields
            if not all(key in data for key in ['crime_id', 'scam_type', 'modus_operandi']):
                logger.warning(f"[Kafka Ingestion] Invalid I4C message: missing required fields")
                return False

            # Store crime data in database
            await self._store_i4c_crime_data(data)

            # Update pattern database
            await self._update_pattern_database(data)

            # Publish processed event
            await self._publish_processed_event(message, 'i4c_processed')

            logger.debug(f"[Kafka Ingestion] Processed I4C crime data: {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error processing I4C message: {str(e)}")
            return False

    async def _process_system_message(self, message: DataMessage) -> bool:
        """
        Process system event message
        """
        try:
            data = message.data

            # Handle different system events
            event_type = data.get('event_type', 'unknown')

            if event_type == 'model_prediction':
                await self._handle_model_prediction(data)
            elif event_type == 'alert_triggered':
                await self._handle_alert_triggered(data)
            elif event_type == 'system_health':
                await self._handle_system_health(data)
            elif event_type == 'learning_update':
                await self._handle_learning_update(data)

            logger.debug(f"[Kafka Ingestion] Processed system message: {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error processing system message: {str(e)}")
            return False

    async def _store_ncrp_complaint(self, data: Dict) -> None:
        """
        Store NCRP complaint in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO ncrp_complaints (
                        complaint_id, scam_type, amount, victim_location,
                        victim_age_group, victim_gender, digital_footprint,
                        ip_address, status, created_at
                    ) VALUES (
                        :complaint_id, :scam_type, :amount,
                        ST_GeomFromText('POINT(:lon :lat)', 4326),
                        :age_group, :gender, :digital_footprint, :ip_address,
                        'received', NOW()
                    )
                    ON CONFLICT (complaint_id) DO UPDATE SET
                        updated_at = NOW()
                """)

                location = data['victim_location']
                db.execute(query, {
                    'complaint_id': data.get('complaint_id', str(uuid.uuid4())),
                    'scam_type': data['scam_type'],
                    'amount': data['amount'],
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'age_group': data.get('victim_details', {}).get('age_group', '18-25'),
                    'gender': data.get('victim_details', {}).get('gender', 'prefer_not_to_say'),
                    'digital_footprint': json.dumps(data.get('digital_footprint', {})),
                    'ip_address': data.get('victim_details', {}).get('ip_address', '0.0.0.0')
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error storing NCRP complaint: {str(e)}")

    async def _store_bank_transaction(self, data: Dict) -> None:
        """
        Store bank transaction in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO bank_transactions (
                        transaction_id, bank_code, transaction_type, amount,
                        account_hash, upi_id, merchant_hash, location,
                        risk_score, fraud_signals, is_suspicious, timestamp, batch_id
                    ) VALUES (
                        :transaction_id, :bank_code, :transaction_type, :amount,
                        :account_hash, :upi_id, :merchant_hash,
                        ST_GeomFromText('POINT(:lon :lat)', 4326),
                        :risk_score, :fraud_signals, :is_suspicious, :timestamp, :batch_id
                    )
                    ON CONFLICT (transaction_id) DO NOTHING
                """)

                location = data['location']
                db.execute(query, {
                    'transaction_id': data['transaction_id'],
                    'bank_code': data['bank_code'],
                    'transaction_type': data['transaction_type'],
                    'amount': data['amount'],
                    'account_hash': data.get('account_hash', ''),
                    'upi_id': data.get('upi_id'),
                    'merchant_hash': data.get('merchant_hash'),
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'risk_score': data.get('risk_score', 0.0),
                    'fraud_signals': json.dumps(data.get('fraud_signals', {})),
                    'is_suspicious': data.get('is_suspicious', False),
                    'timestamp': data['timestamp'],
                    'batch_id': data.get('batch_id', str(uuid.uuid4()))
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error storing bank transaction: {str(e)}")

    async def _store_i4c_crime_data(self, data: Dict) -> None:
        """
        Store I4C crime data in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO i4c_crime_data (
                        crime_id, modus_operandi, repeat_offender, criminal_network,
                        location, date_range_start, date_range_end, scam_type,
                        victim_profile, outcome, conviction_rate, severity_score,
                        data_source, imported_at
                    ) VALUES (
                        :crime_id, :modus_operandi, :repeat_offender, :criminal_network,
                        ST_GeomFromText('POINT(:lon :lat)', 4326),
                        :date_range_start, :date_range_end, :scam_type,
                        :victim_profile, :outcome, :conviction_rate, :severity_score,
                        :data_source, NOW()
                    )
                    ON CONFLICT (crime_id) DO UPDATE SET
                        updated_at = NOW()
                """)

                location = data.get('location', {'lat': 0, 'lon': 0})
                db.execute(query, {
                    'crime_id': data['crime_id'],
                    'modus_operandi': data['modus_operandi'],
                    'repeat_offender': data.get('repeat_offender', False),
                    'criminal_network': data.get('criminal_network'),
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'date_range_start': data['date_range_start'],
                    'date_range_end': data['date_range_end'],
                    'scam_type': data['scam_type'],
                    'victim_profile': json.dumps(data.get('victim_profile', {})),
                    'outcome': data.get('outcome', 'unknown'),
                    'conviction_rate': data.get('conviction_rate', 0.0),
                    'severity_score': data.get('severity_score', 5),
                    'data_source': data.get('data_source', 'I4C_Import')
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error storing I4C crime data: {str(e)}")

    async def _analyze_transaction_suspicion(self, data: Dict) -> bool:
        """
        Analyze transaction for suspicious patterns
        """
        try:
            # Check if already marked suspicious
            if data.get('is_suspicious', False):
                return True

            # Analyze fraud signals
            fraud_signals = data.get('fraud_signals', {})
            suspicious_signals = [
                fraud_signals.get('unusual_amount', False),
                fraud_signals.get('new_account', False),
                fraud_signals.get('multiple_attempts', False),
                fraud_signals.get('off_hours', False),
                fraud_signals.get('high_velocity', False),
                fraud_signals.get('geolocation_mismatch', False),
                fraud_signals.get('suspicious_pattern', False)
            ]

            # Consider suspicious if multiple signals present
            suspicious_count = sum(suspicious_signals)
            risk_score = data.get('risk_score', 0.0)

            return suspicious_count >= 2 or risk_score > 0.7

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error analyzing transaction suspicion: {str(e)}")
            return False

    async def _cache_complaint_data(self, message_id: str, data: Dict) -> None:
        """
        Cache complaint data for real-time access
        """
        try:
            cache_key = f"complaint:{message_id}"
            await self.redis_client.setex(
                cache_key,
                timedelta(hours=24),  # Cache for 24 hours
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error caching complaint data: {str(e)}")

    async def _cache_suspicious_transaction(self, message_id: str, data: Dict) -> None:
        """
        Cache suspicious transaction for real-time monitoring
        """
        try:
            cache_key = f"suspicious_txn:{message_id}"
            await self.redis_client.setex(
                cache_key,
                timedelta(hours=6),  # Cache for 6 hours
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error caching suspicious transaction: {str(e)}")

    async def _trigger_ai_prediction(self, data: Dict, source_type: str) -> None:
        """
        Trigger AI prediction for high-priority data
        """
        try:
            # Create AI prediction request
            prediction_request = {
                'event_type': 'trigger_prediction',
                'source_type': source_type,
                'data': data,
                'priority': 'high',
                'timestamp': datetime.utcnow().isoformat()
            }

            # Publish to system topic
            await self._publish_system_message(prediction_request)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error triggering AI prediction: {str(e)}")

    async def _publish_processed_event(self, original_message: DataMessage, event_type: str) -> None:
        """
        Publish processed event notification
        """
        try:
            event = {
                'event_type': event_type,
                'original_message_id': original_message.message_id,
                'source_type': original_message.source_type.value,
                'processed_at': datetime.utcnow().isoformat(),
                'processing_time_ms': (datetime.utcnow() - original_message.timestamp).total_seconds() * 1000
            }

            await self._publish_system_message(event)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error publishing processed event: {str(e)}")

    async def _publish_alert(self, message: DataMessage, data: Dict) -> None:
        """
        Publish alert for suspicious activity
        """
        try:
            alert = {
                'event_type': 'suspicious_activity_alert',
                'message_id': message.message_id,
                'source_type': message.source_type.value,
                'alert_data': data,
                'severity': 'high' if message.priority == DataPriority.CRITICAL else 'medium',
                'timestamp': datetime.utcnow().isoformat()
            }

            await self._publish_system_message(alert)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error publishing alert: {str(e)}")

    async def _publish_system_message(self, data: Dict) -> None:
        """
        Publish message to system topic
        """
        try:
            message = DataMessage(
                message_id=str(uuid.uuid4()),
                source_type=DataSourceType.SYSTEM,
                source_id='kafka_pipeline',
                timestamp=datetime.utcnow(),
                priority=DataPriority.NORMAL,
                data=data,
                metadata={'producer': 'kafka_ingestion'}
            )

            await self.producer.send_and_wait(
                self.topics[DataSourceType.SYSTEM],
                value=asdict(message),
                key=message.message_id
            )

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error publishing system message: {str(e)}")

    async def _handle_processing_failure(self, message: DataMessage, source_type: DataSourceType) -> None:
        """
        Handle processing failure for a message
        """
        try:
            message.processing_attempts += 1

            if message.processing_attempts < message.max_retries:
                # Retry processing
                logger.warning(f"[Kafka Ingestion] Retrying message {message.message_id} (attempt {message.processing_attempts})")
                await self.processing_queues[source_type].put(message)
            else:
                # Max retries reached, move to dead letter queue
                logger.error(f"[Kafka Ingestion] Max retries reached for message {message.message_id}")
                await self._move_to_dead_letter_queue(message)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error handling processing failure: {str(e)}")

    async def _move_to_dead_letter_queue(self, message: DataMessage) -> None:
        """
        Move failed message to dead letter queue
        """
        try:
            dead_letter_key = f"dlq:{message.source_type.value}:{message.message_id}"
            await self.redis_client.setex(
                dead_letter_key,
                timedelta(days=7),  # Keep for 7 days
                json.dumps(asdict(message))
            )

            logger.warning(f"[Kafka Ingestion] Message {message.message_id} moved to DLQ")

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error moving to DLQ: {str(e)}")

    async def _update_pattern_database(self, data: Dict) -> None:
        """
        Update pattern database with new crime data
        """
        try:
            # Extract modus operandi patterns
            mo = data.get('modus_operandi', '')
            scam_type = data.get('scam_type', '')

            # Update pattern frequency in Redis
            pattern_key = f"pattern:{scam_type}"
            await self.redis_client.hincrby(pattern_key, 'frequency', 1)
            await self.redis_client.expire(pattern_key, timedelta(days=30))

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error updating pattern database: {str(e)}")

    async def _handle_model_prediction(self, data: Dict) -> None:
        """Handle model prediction event"""
        # Cache prediction results
        prediction_id = data.get('prediction_id')
        if prediction_id:
            await self.redis_client.setex(
                f"prediction:{prediction_id}",
                timedelta(hours=1),
                json.dumps(data)
            )

    async def _handle_alert_triggered(self, data: Dict) -> None:
        """Handle alert triggered event"""
        # Store alert in database
        alert_id = data.get('alert_id')
        if alert_id:
            # Implementation would store alert in database
            pass

    async def _handle_system_health(self, data: Dict) -> None:
        """Handle system health event"""
        # Update system health metrics
        health_status = data.get('status', 'unknown')
        await self.redis_client.setex(
            "system_health",
            timedelta(minutes=5),
            health_status
        )

    async def _handle_learning_update(self, data: Dict) -> None:
        """Handle learning update event"""
        # Update model learning metrics
        model_type = data.get('model_type')
        if model_type:
            learning_key = f"learning:{model_type}"
            await self.redis_client.hset(learning_key, mapping=data)
            await self.redis_client.expire(learning_key, timedelta(days=1))

    def _update_processing_metrics(self, processing_time: float) -> None:
        """Update processing time metrics"""
        # Calculate rolling average
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (current_avg * 0.9) + (processing_time * 0.1)

    async def _collect_metrics(self) -> None:
        """Collect and publish metrics periodically"""
        try:
            while self.is_running:
                # Update queue sizes
                for source_type, queue in self.processing_queues.items():
                    self.metrics['queue_sizes'][source_type.value] = queue.qsize()

                # Publish metrics to monitoring system
                metrics_data = {
                    'event_type': 'metrics_update',
                    'metrics': self.metrics,
                    'timestamp': datetime.utcnow().isoformat()
                }

                await self._publish_system_message(metrics_data)

                # Sleep for 30 seconds
                await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error collecting metrics: {str(e)}")

    async def _health_monitor(self) -> None:
        """Monitor system health"""
        try:
            while self.is_running:
                # Check consumer health
                for source_type, consumer in self.consumers.items():
                    # Check if consumer is responsive
                    try:
                        # Simple health check - get consumer position
                        position = await consumer.position(consumer.assignment()[0] if consumer.assignment() else None)
                    except Exception as e:
                        logger.error(f"[Kafka Ingestion] Consumer {source_type.value} unhealthy: {str(e)}")

                # Check Redis health
                try:
                    await self.redis_client.ping()
                except Exception as e:
                    logger.error(f"[Kafka Ingestion] Redis unhealthy: {str(e)}")

                # Sleep for 60 seconds
                await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Health monitor error: {str(e)}")

    async def produce_data(self, source_type: DataSourceType, data: Dict,
                          priority: DataPriority = DataPriority.NORMAL,
                          source_id: str = None) -> bool:
        """
        Produce data to Kafka topic
        """
        try:
            message = DataMessage(
                message_id=str(uuid.uuid4()),
                source_type=source_type,
                source_id=source_id or f"producer_{source_type.value}",
                timestamp=datetime.utcnow(),
                priority=priority,
                data=data,
                metadata={'producer': 'kafka_ingestion'}
            )

            await self.producer.send_and_wait(
                self.topics[source_type],
                value=asdict(message),
                key=message.message_id
            )

            self.metrics['messages_produced'] += 1
            return True

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error producing data: {str(e)}")
            return False

    async def shutdown(self) -> None:
        """
        Shutdown the ingestion pipeline
        """
        try:
            logger.info("[Kafka Ingestion] Shutting down ingestion pipeline...")

            self.is_running = False

            # Stop consumers
            for consumer in self.consumers.values():
                await consumer.stop()

            # Stop producer
            if self.producer:
                await self.producer.stop()

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            logger.info("[Kafka Ingestion] Pipeline shutdown complete")

        except Exception as e:
            logger.error(f"[Kafka Ingestion] Error during shutdown: {str(e)}")

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status
        """
        return {
            'is_running': self.is_running,
            'metrics': self.metrics,
            'queue_sizes': {source.value: queue.qsize() for source, queue in self.processing_queues.items()},
            'connected_consumers': len(self.consumers),
            'redis_connected': self.redis_client is not None
        }

# Global ingestion service instance
kafka_ingestion = KafkaDataIngestion()