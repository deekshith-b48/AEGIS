"""
Advanced Data Streams Architecture
Complete data pipeline orchestration and management system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from data_sources.ncrp_integration import ncrp_integration
from data_sources.bank_integration import bank_integration
from data_sources.i4c_integration import i4c_integration
from data_pipeline.kafka_ingestion import kafka_ingestion
from privacy.data_fusion import privacy_preserving_fusion
from data_warehouse.feature_store import feature_store
from data_warehouse.data_warehouse import data_warehouse
from ai_models.cst_transformer import cst_transformer_service
from ai_models.federated_causal_graph import federated_causal_graph
from ai_models.behavioral_digital_twin import behavioral_digital_twin
from risk_engine.advanced_risk_scoring import advanced_risk_scoring_engine
from integrations.npci_digital_cordon import npci_digital_cordon
from alerts.multi_channel_alerts import multi_channel_alerts

logger = logging.getLogger(__name__)

class StreamStatus(Enum):
    """Data stream status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"

class StreamType(Enum):
    """Data stream types"""
    NCRP_COMPLAINTS = "ncrp_complaints"
    BANK_TRANSACTIONS = "bank_transactions"
    I4C_CRIME_DATA = "i4c_crime_data"
    REAL_TIME_ALERTS = "real_time_alerts"
    BATCH_PROCESSING = "batch_processing"
    ML_PREDICTIONS = "ml_predictions"
    PRIVACY_PRESERVED = "privacy_preserved"
    RISK_ASSESSMENTS = "risk_assessments"

@dataclass
class DataStream:
    """Data stream configuration and status"""
    stream_id: str
    stream_type: StreamType
    source_system: str
    destination_systems: List[str]
    status: StreamStatus
    priority: int  # 1-10, where 10 is highest
    processing_rate: int  # records per second
    error_count: int = 0
    last_processed: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    health_metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.health_metrics is None:
            self.health_metrics = {}

@dataclass
class StreamConfiguration:
    """Stream processing configuration"""
    batch_size: int = 100
    processing_interval: int = 5  # seconds
    retry_attempts: int = 3
    timeout_seconds: int = 30
    enable_backpressure: bool = True
    max_queue_size: int = 10000

class AdvancedDataStreamsArchitecture:
    """
    Master orchestrator for all data streams in Project AEGIS
    """

    def __init__(self):
        self.streams = {}
        self.stream_configs = {}
        self.stream_metrics = {}
        self.is_running = False

        # Component references
        self.components = {
            'ncrp': ncrp_integration,
            'bank': bank_integration,
            'i4c': i4c_integration,
            'kafka': kafka_ingestion,
            'privacy': privacy_preserving_fusion,
            'feature_store': feature_store,
            'data_warehouse': data_warehouse,
            'cst_transformer': cst_transformer_service,
            'federated_graph': federated_causal_graph,
            'behavioral_twin': behavioral_digital_twin,
            'risk_engine': advanced_risk_scoring_engine,
            'npci_cordon': npci_digital_cordon,
            'alerts': multi_channel_alerts
        }

        # Global configuration
        self.global_config = StreamConfiguration()

        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.health_thresholds = {
            'max_error_rate': 0.05,  # 5% error rate
            'min_processing_rate': 10,  # records per minute
            'max_queue_size': 0.8  # 80% of max queue size
        }

    async def initialize(self) -> bool:
        """Initialize the complete data streams architecture"""
        try:
            logger.info("[Data Streams] Initializing advanced data streams architecture...")

            # Initialize all components
            initialization_success = await self._initialize_components()
            if not initialization_success:
                raise Exception("Component initialization failed")

            # Define data streams
            await self._define_data_streams()

            # Start monitoring
            await self._start_health_monitoring()

            self.is_running = True
            logger.info("[Data Streams] Architecture initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error initializing architecture: {str(e)}")
            return False

    async def _initialize_components(self) -> bool:
        """Initialize all components in the correct order"""
        try:
            logger.info("[Data Streams] Initializing components...")

            # Initialize in dependency order
            init_order = [
                ('kafka', kafka_ingestion),
                ('ncrp', ncrp_integration),
                ('bank', bank_integration),
                ('i4c', i4c_integration),
                ('privacy', privacy_preserving_fusion),
                ('feature_store', feature_store),
                ('data_warehouse', data_warehouse),
                ('cst_transformer', cst_transformer_service),
                ('federated_graph', federated_causal_graph),
                ('behavioral_twin', behavioral_digital_twin),
                ('risk_engine', advanced_risk_scoring_engine),
                ('npci_cordon', npci_digital_cordon),
                ('alerts', multi_channel_alerts)
            ]

            for name, component in init_order:
                try:
                    if hasattr(component, 'initialize'):
                        success = await component.initialize()
                        if not success:
                            logger.error(f"[Data Streams] Failed to initialize {name}")
                            return False
                        logger.info(f"[Data Streams] ✓ {name} initialized")
                    else:
                        logger.info(f"[Data Streams] ✓ {name} ready (no init required)")
                except Exception as e:
                    logger.error(f"[Data Streams] Error initializing {name}: {str(e)}")
                    return False

            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error initializing components: {str(e)}")
            return False

    async def _define_data_streams(self) -> None:
        """Define all data streams"""
        try:
            # NCRP Complaint Stream
            self.streams['ncrp_complaints'] = DataStream(
                stream_id='ncrp_complaints_stream',
                stream_type=StreamType.NCRP_COMPLAINTS,
                source_system='NCRP',
                destination_systems=['kafka', 'privacy', 'feature_store', 'data_warehouse'],
                status=StreamStatus.ACTIVE,
                priority=9,
                processing_rate=50,
                metadata={
                    'schema': 'ncrp_complaints',
                    'encryption': 'aes256',
                    'retention_days': 365
                }
            )

            # Bank Transaction Stream
            self.streams['bank_transactions'] = DataStream(
                stream_id='bank_transactions_stream',
                stream_type=StreamType.BANK_TRANSACTIONS,
                source_system='CFCFRMS',
                destination_systems=['kafka', 'privacy', 'risk_engine', 'npci_cordon'],
                status=StreamStatus.ACTIVE,
                priority=8,
                processing_rate=100,
                metadata={
                    'schema': 'bank_transactions',
                    'real_time': True,
                    'suspicious_only': True
                }
            )

            # I4C Crime Data Stream
            self.streams['i4c_crime_data'] = DataStream(
                stream_id='i4c_crime_data_stream',
                stream_type=StreamType.I4C_CRIME_DATA,
                source_system='I4C',
                destination_systems=['kafka', 'data_warehouse', 'federated_graph', 'behavioral_twin'],
                status=StreamStatus.ACTIVE,
                priority=7,
                processing_rate=20,
                metadata={
                    'schema': 'i4c_crime_data',
                    'batch_mode': True,
                    'historical': True
                }
            )

            # AI Prediction Stream
            self.streams['ml_predictions'] = DataStream(
                stream_id='ml_predictions_stream',
                stream_type=StreamType.ML_PREDICTIONS,
                source_system='AEGIS_AI',
                destination_systems=['kafka', 'feature_store', 'alerts', 'data_warehouse'],
                status=StreamStatus.ACTIVE,
                priority=10,
                processing_rate=30,
                metadata={
                    'models': ['cst_transformer', 'federated_graph', 'behavioral_twin'],
                    'real_time_inference': True
                }
            )

            # Risk Assessment Stream
            self.streams['risk_assessments'] = DataStream(
                stream_id='risk_assessments_stream',
                stream_type=StreamType.RISK_ASSESSMENTS,
                source_system='RiskEngine',
                destination_systems=['kafka', 'alerts', 'npci_cordon', 'data_warehouse'],
                status=StreamStatus.ACTIVE,
                priority=9,
                processing_rate=40,
                metadata={
                    'scoring_method': 'advanced_ml',
                    'thresholds': {'high': 0.7, 'critical': 0.9}
                }
            )

            # Privacy-Preserved Stream
            self.streams['privacy_preserved'] = DataStream(
                stream_id='privacy_preserved_stream',
                stream_type=StreamType.PRIVACY_PRESERVED,
                source_system='PrivacyEngine',
                destination_systems=['data_warehouse', 'feature_store'],
                status=StreamStatus.ACTIVE,
                priority=6,
                processing_rate=25,
                metadata={
                    'privacy_level': 'high',
                    'k_anonymity': 50,
                    'differential_privacy': True,
                    'epsilon': 0.5
                }
            )

            # Real-time Alerts Stream
            self.streams['real_time_alerts'] = DataStream(
                stream_id='real_time_alerts_stream',
                stream_type=StreamType.REAL_TIME_ALERTS,
                source_system='AlertSystem',
                destination_systems=['kafka', 'all_channels'],
                status=StreamStatus.ACTIVE,
                priority=10,
                processing_rate=10,
                metadata={
                    'channels': ['email', 'sms', 'whatsapp', 'push', 'dashboard'],
                    'escalation': True,
                    'retry_policy': 'exponential_backoff'
                }
            )

            logger.info(f"[Data Streams] ✓ Defined {len(self.streams)} data streams")

        except Exception as e:
            logger.error(f"[Data Streams] Error defining data streams: {str(e)}")

    async def start_all_streams(self) -> Dict[str, bool]:
        """Start all data streams"""
        try:
            logger.info("[Data Streams] Starting all data streams...")

            results = {}

            # Start data ingestion streams
            ncrp_success = await self._start_ncrp_stream()
            results['ncrp_complaints'] = ncrp_success

            bank_success = await self._start_bank_stream()
            results['bank_transactions'] = bank_success

            i4c_success = await self._start_i4c_stream()
            results['i4c_crime_data'] = i4c_success

            # Start AI processing streams
            ai_success = await self._start_ai_streams()
            results['ml_predictions'] = ai_success

            # Start processing streams
            processing_success = await self._start_processing_streams()
            results['risk_assessments'] = processing_success

            # Start output streams
            output_success = await self._start_output_streams()
            results['real_time_alerts'] = output_success

            logger.info(f"[Data Streams] Streams started: {sum(results.values())}/{len(results)}")
            return results

        except Exception as e:
            logger.error(f"[Data Streams] Error starting streams: {str(e)}")
            return {}

    async def _start_ncrp_stream(self) -> bool:
        """Start NCRP data stream"""
        try:
            logger.info("[Data Streams] Starting NCRP complaints stream...")

            # Fetch initial batch of complaints
            complaints = await self.components['ncrp'].get_complaints_batch(limit=1000, offset=0)

            # Send to Kafka
            for complaint in complaints:
                await self.components['kafka'].produce_data(
                    source_type='ncrp',
                    data=complaint,
                    priority='high' if complaint.get('amount', 0) > 50000 else 'normal',
                    source_id=complaint.get('complaint_id', 'unknown')
                )

            logger.info(f"[Data Streams] ✓ Processed {len(complaints)} NCRP complaints")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting NCRP stream: {str(e)}")
            return False

    async def _start_bank_stream(self) -> bool:
        """Start bank transaction stream"""
        try:
            logger.info("[Data Streams] Starting bank transactions stream...")

            # Get suspicious transactions
            suspicious_txns = await self.components['bank'].get_suspicious_transactions(hours_back=24)

            # Send to Kafka
            for txn in suspicious_txns:
                await self.components['kafka'].produce_data(
                    source_type='bank',
                    data=txn,
                    priority='high',
                    source_id=txn.get('transaction_id', 'unknown')
                )

            logger.info(f"[Data Streams] ✓ Processed {len(suspicious_txns)} suspicious transactions")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting bank stream: {str(e)}")
            return False

    async def _start_i4c_stream(self) -> bool:
        """Start I4C crime data stream"""
        try:
            logger.info("[Data Streams] Starting I4C crime data stream...")

            # Get training data
            i4c_data = await self.components['i4c'].get_training_data_for_ml(months_back=3)

            # Send to Kafka
            for crime in i4c_data:
                await self.components['kafka'].produce_data(
                    source_type='i4c',
                    data=crime,
                    priority='normal',
                    source_id=crime.get('crime_id', 'unknown')
                )

            logger.info(f"[Data Streams] ✓ Processed {len(i4c_data)} I4C crime records")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting I4C stream: {str(e)}")
            return False

    async def _start_ai_streams(self) -> bool:
        """Start AI processing streams"""
        try:
            logger.info("[Data Streams] Starting AI processing streams...")

            # Initialize AI models
            ai_success = await self.components['cst_transformer'].initialize()
            if not ai_success:
                logger.warning("[Data Streams] CST-Transformer initialization failed")

            # Generate predictions
            try:
                predictions = await self.components['cst_transformer'].predict_hotspots(hours_ahead=2)

                # Send predictions to Kafka
                for prediction in predictions:
                    await self.components['kafka'].produce_data(
                        source_type='ai',
                        data=prediction,
                        priority='high',
                        source_id='ml_prediction'
                    )

                logger.info(f"[Data Streams] ✓ Generated {len(predictions)} AI predictions")

            except Exception as e:
                logger.error(f"[Data Streams] Error generating AI predictions: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting AI streams: {str(e)}")
            return False

    async def _start_processing_streams(self) -> bool:
        """Start processing streams"""
        try:
            logger.info("[Data Streams] Starting processing streams...")

            # Initialize risk engine
            risk_success = await self.components['risk_engine'].initialize()
            if not risk_success:
                logger.warning("[Data Streams] Risk engine initialization failed")

            # Process sample risk assessments
            sample_assessments = [
                {
                    'entity_id': 'sample_entity_1',
                    'entity_type': 'transaction',
                    'context_data': {
                        'amount': 75000,
                        'transaction_type': 'IMPS',
                        'account_age_days': 15,
                        'failed_attempts': 3
                    },
                    'historical_data': {
                        'fraud_history': {'has_fraud': False},
                        'complaint_count': 0
                    }
                },
                {
                    'entity_id': 'sample_entity_2',
                    'entity_type': 'account',
                    'context_data': {
                        'amount': 250000,
                        'rapid_succession_count': 8,
                        'foreign_ip_access': True
                    }
                }
            ]

            for assessment_data in sample_assessments:
                try:
                    assessment = await self.components['risk_engine'].assess_risk(
                        entity_id=assessment_data['entity_id'],
                        entity_type=assessment_data['entity_type'],
                        context_data=assessment_data['context_data'],
                        historical_data=assessment_data.get('historical_data')
                    )

                    # Send to Kafka
                    await self.components['kafka'].produce_data(
                        source_type='risk',
                        data=asdict(assessment),
                        priority='high' if assessment.risk_level.value in ['critical', 'very_high'] else 'normal',
                        source_id='risk_assessment'
                    )

                except Exception as e:
                    logger.error(f"[Data Streams] Error in risk assessment: {str(e)}")

            logger.info(f"[Data Streams] ✓ Processed {len(sample_assessments)} risk assessments")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting processing streams: {str(e)}")
            return False

    async def _start_output_streams(self) -> bool:
        """Start output streams"""
        try:
            logger.info("[Data Streams] Starting output streams...")

            # Initialize alert system
            alert_success = await self.components['alerts'].initialize()
            if not alert_success:
                logger.warning("[Data Streams] Alert system initialization failed")

            # Send test alerts
            test_alerts = [
                {
                    'title': 'Test High-Risk Transaction Alert',
                    'message': 'A high-risk transaction has been detected requiring immediate attention.',
                    'severity': 'high',
                    'target_groups': ['cybercrime_team', 'banking_authorities']
                },
                {
                    'title': 'System Status Update',
                    'message': 'All data streams are operational and processing normally.',
                    'severity': 'info',
                    'target_groups': ['analytics_team']
                }
            ]

            for alert_data in test_alerts:
                try:
                    await self.components['alerts'].create_alert(
                        title=alert_data['title'],
                        message=alert_data['message'],
                        severity=self.components['alerts'].AlertSeverity[alert_data['severity'].upper()],
                        target_groups=alert_data['target_groups']
                    )
                except Exception as e:
                    logger.error(f"[Data Streams] Error creating alert: {str(e)}")

            logger.info(f"[Data Streams] ✓ Sent {len(test_alerts)} test alerts")
            return True

        except Exception as e:
            logger.error(f"[Data Streams] Error starting output streams: {str(e)}")
            return False

    async def _start_health_monitoring(self) -> None:
        """Start health monitoring for all streams"""
        try:
            logger.info("[Data Streams] Starting health monitoring...")

            while self.is_running:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)

        except Exception as e:
            logger.error(f"[Data Streams] Error in health monitoring: {str(e)}")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all streams"""
        try:
            health_status = {}

            for stream_id, stream in self.streams.items():
                # Check stream health
                stream_health = await self._check_stream_health(stream)
                self.streams[stream_id].health_metrics = stream_health

                # Update stream status if needed
                if stream_health['error_rate'] > self.health_thresholds['max_error_rate']:
                    if stream.status != StreamStatus.ERROR:
                        self.streams[stream_id].status = StreamStatus.ERROR
                        logger.warning(f"[Data Streams] Stream {stream_id} marked as ERROR")

                health_status[stream_id] = stream_health

            # Log overall health
            total_streams = len(self.streams)
            healthy_streams = sum(1 for h in health_status.values() if h['healthy'])
            health_percentage = (healthy_streams / total_streams * 100) if total_streams > 0 else 0

            logger.info(f"[Data Streams] Health check: {healthy_streams}/{total_streams} streams healthy ({health_percentage:.1f}%)")

        except Exception as e:
            logger.error(f"[Data Streams] Error performing health checks: {str(e)}")

    async def _check_stream_health(self, stream: DataStream) -> Dict[str, float]:
        """Check health of a specific stream"""
        try:
            health = {
                'healthy': True,
                'error_rate': 0.0,
                'processing_rate': 0.0,
                'queue_utilization': 0.0,
                'last_processed_minutes': 0.0
            }

            # Calculate error rate
            if stream.processing_rate > 0:
                health['error_rate'] = stream.error_count / (stream.processing_rate * 60)  # errors per minute

            # Check if stream was processed recently
            if stream.last_processed:
                time_diff = datetime.utcnow() - stream.last_processed
                health['last_processed_minutes'] = time_diff.total_seconds() / 60
            else:
                health['last_processed_minutes'] = float('inf')

            # Determine overall health
            health['healthy'] = (
                health['error_rate'] <= self.health_thresholds['max_error_rate'] and
                health['last_processed_minutes'] < 60
            )

            return health

        except Exception as e:
            logger.error(f"[Data Streams] Error checking stream health: {str(e)}")
            return {'healthy': False, 'error': str(e)}

    async def get_stream_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all streams"""
        try:
            status = {
                'architecture_status': 'active' if self.is_running else 'inactive',
                'total_streams': len(self.streams),
                'streams': {},
                'component_status': {},
                'global_metrics': {
                    'total_processed_today': 0,
                    'total_errors_today': 0,
                    'average_processing_rate': 0
                }
            }

            # Individual stream status
            for stream_id, stream in self.streams.items():
                status['streams'][stream_id] = {
                    'type': stream.stream_type.value,
                    'source': stream.source_system,
                    'destinations': stream.destination_systems,
                    'status': stream.status.value,
                    'priority': stream.priority,
                    'processing_rate': stream.processing_rate,
                    'error_count': stream.error_count,
                    'last_processed': stream.last_processed.isoformat() if stream.last_processed else None,
                    'health_metrics': stream.health_metrics
                }

            # Component status
            for name, component in self.components.items():
                try:
                    if hasattr(component, 'get_status'):
                        status['component_status'][name] = await component.get_status()
                    else:
                        status['component_status'][name] = 'available'
                except Exception as e:
                    status['component_status'][name] = f'error: {str(e)}'

            return status

        except Exception as e:
            logger.error(f"[Data Streams] Error getting stream status: {str(e)}")
            return {'error': str(e)}

    async def stop_all_streams(self) -> Dict[str, bool]:
        """Stop all data streams gracefully"""
        try:
            logger.info("[Data Streams] Stopping all data streams...")

            results = {}

            # Mark all streams as stopped
            for stream_id, stream in self.streams.items():
                stream.status = StreamStatus.STOPPED
                results[stream_id] = True

            self.is_running = False

            logger.info("[Data Streams] All streams stopped")
            return results

        except Exception as e:
            logger.error(f"[Data Streams] Error stopping streams: {str(e)}")
            return {}

    async def restart_stream(self, stream_id: str) -> bool:
        """Restart a specific stream"""
        try:
            if stream_id not in self.streams:
                logger.error(f"[Data Streams] Stream {stream_id} not found")
                return False

            stream = self.streams[stream_id]
            stream.status = StreamStatus.INITIALIZING

            # Restart based on stream type
            success = False
            if 'ncrp' in stream_id:
                success = await self._start_ncrp_stream()
            elif 'bank' in stream_id:
                success = await self._start_bank_stream()
            elif 'i4c' in stream_id:
                success = await self._start_i4c_stream()

            if success:
                stream.status = StreamStatus.ACTIVE
                logger.info(f"[Data Streams] ✓ Stream {stream_id} restarted successfully")
            else:
                stream.status = StreamStatus.ERROR
                logger.error(f"[Data Streams] ✗ Stream {stream_id} restart failed")

            return success

        except Exception as e:
            logger.error(f"[Data Streams] Error restarting stream {stream_id}: {str(e)}")
            return False

# Global architecture instance
data_streams_architecture = AdvancedDataStreamsArchitecture()