"""
Blockchain-based Audit Logging System
Hyperledger Fabric integration for immutable audit trails
"""

import asyncio
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Audit event types"""
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    COMPLAINT_CREATED = "complaint_created"
    COMPLAINT_UPDATED = "complaint_updated"
    TRANSACTION_FLAGGED = "transaction_flagged"
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    CORDON_CREATED = "cordon_created"
    CORDON_EXECUTED = "cordon_executed"
    CORDON_RELEASED = "cordon_released"
    AI_PREDICTION = "ai_prediction"
    RISK_ASSESSMENT = "risk_assessment"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_ERROR = "system_error"
    SECURITY_EVENT = "security_event"

class AuditSeverity(Enum):
    """Audit event severity"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BlockchainStatus(Enum):
    """Blockchain transaction status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    VERIFIED = "verified"

@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    blockchain_tx_id: Optional[str] = None
    blockchain_status: BlockchainStatus = BlockchainStatus.PENDING
    hash_value: str = ""

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.old_values is None:
            self.old_values = {}
        if self.new_values is None:
            self.new_values = {}
        # Calculate hash of the event
        self.hash_value = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the event"""
        try:
            event_data = {
                'event_id': self.event_id,
                'event_type': self.event_type.value,
                'severity': self.severity.value,
                'timestamp': self.timestamp.isoformat(),
                'user_id': self.user_id,
                'action': self.action,
                'resource_type': self.resource_type,
                'resource_id': self.resource_id,
                'old_values': self.old_values,
                'new_values': self.new_values,
                'metadata': self.metadata
            }
            event_json = json.dumps(event_data, sort_keys=True, separators=(',', ':'))
            return hashlib.sha256(event_json.encode()).hexdigest()
        except Exception as e:
            logger.error(f"[Blockchain Audit] Error calculating hash: {str(e)}")
            return ""

@dataclass
class BlockchainTransaction:
    """Blockchain transaction record"""
    tx_id: str
    block_hash: str
    block_number: int
    transaction_hash: str
    timestamp: datetime
    status: BlockchainStatus
    payload_hash: str
    signature: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class HyperledgerFabricIntegration:
    """
    Hyperledger Fabric integration for blockchain audit logging
    """

    def __init__(self):
        self.connection_config = {
            'peer_url': 'grpcs://localhost:7051',
            'channel_name': 'aegis-channel',
            'chaincode_name': 'audit-chaincode',
            'peer_org': 'Org1MSP',
            'peer_certificate': 'path/to/peer.crt',
            'peer_private_key': 'path/to/peer.key',
            'peer_root_cert': 'path/to/ca.crt'
        }

        self.crypto_suite = {
            'hash_algorithm': 'SHA256',
            'signature_algorithm': 'ECDSA',
            'key_size': 256
        }

        self.transaction_queue = asyncio.Queue()
        self.pending_transactions = {}
        self.confirmed_transactions = {}
        self.is_connected = False

        # Blockchain metrics
        self.metrics = {
            'total_transactions': 0,
            'confirmed_transactions': 0,
            'failed_transactions': 0,
            'average_confirmation_time': 0.0
        }

    async def initialize(self) -> bool:
        """Initialize Hyperledger Fabric integration"""
        try:
            logger.info("[Blockchain Audit] Initializing Hyperledger Fabric integration...")

            # In production, this would connect to actual Hyperledger Fabric network
            # For demo purposes, we'll simulate blockchain operations

            # Initialize crypto suite
            await self._initialize_crypto_suite()

            # Connect to Fabric network (simulation)
            await self._connect_to_fabric()

            # Start transaction processing
            await self._start_transaction_processor()

            # Start periodic cleanup
            asyncio.create_task(self._periodic_cleanup())

            self.is_connected = True
            logger.info("[Blockchain Audit] Hyperledger Fabric integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error initializing Fabric integration: {str(e)}")
            return False

    async def _initialize_crypto_suite(self) -> None:
        """Initialize cryptographic components"""
        try:
            # Generate master key for signing
            password = b"fabric_master_key_2025"
            salt = b"fabric_salt_2025"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.master_key = base64.urlsafe_b64encode(kdf.derive(password))

            logger.info("[Blockchain Audit] Crypto suite initialized")

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error initializing crypto suite: {str(e)}")

    async def _connect_to_fabric(self) -> None:
        """Connect to Hyperledger Fabric network"""
        try:
            # In production, this would establish actual gRPC connections
            # For demo, we'll simulate the connection
            logger.info("[Blockchain Audit] Connecting to Hyperledger Fabric network...")

            # Test connection (simulation)
            await asyncio.sleep(2)  # Simulate connection time

            # Check if we have required certificates (simulation)
            required_certs = ['peer_certificate', 'peer_private_key', 'peer_root_cert']
            for cert in required_certs:
                if not os.path.exists(self.connection_config.get(cert, f"/tmp/{cert}")):
                    # Create dummy certificates for demo
                    await self._create_demo_certificate(cert)

            logger.info("[Blockchain Audit] Connected to Hyperledger Fabric network")

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error connecting to Fabric: {str(e)}")

    async def _create_demo_certificate(self, cert_name: str) -> None:
        """Create demo certificate for testing"""
        try:
            cert_path = f"/tmp/{cert_name}"
            with open(cert_path, 'w') as f:
                f.write(f"# Demo certificate for {cert_name}\n")
            logger.debug(f"[Blockchain Audit] Created demo certificate: {cert_path}")
        except Exception as e:
            logger.error(f"[Blockchain Audit] Error creating demo certificate: {str(e)}")

    async def _start_transaction_processor(self) -> None:
        """Start transaction processing loop"""
        try:
            logger.info("[Blockchain Audit] Starting transaction processor...")

            while self.is_connected:
                try:
                    # Get transaction from queue
                    transaction = await asyncio.wait_for(
                        self.transaction_queue.get(),
                        timeout=1.0
                    )

                    # Process transaction
                    await self._process_transaction(transaction)

                except asyncio.TimeoutError:
                    # No transactions in queue
                    await asyncio.sleep(0.1)
                    continue
                except Exception as e:
                    logger.error(f"[Blockchain Audit] Error processing transaction: {str(e)}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error in transaction processor: {str(e)}")

    async def _process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process a blockchain transaction"""
        try:
            start_time = datetime.utcnow()
            tx_id = transaction['tx_id']
            event = transaction['event']

            logger.debug(f"[Blockchain Audit] Processing transaction {tx_id}")

            # Submit transaction to blockchain
            submission_result = await self._submit_transaction_to_blockchain(tx_id, event)

            if submission_result['success']:
                # Update event with blockchain details
                event.blockchain_tx_id = submission_result['tx_id']
                event.blockchain_status = BlockchainStatus.SUBMITTED
                self.pending_transactions[tx_id] = {
                    'event': event,
                    'submission_result': submission_result,
                    'submitted_at': start_time
                }

                # Wait for confirmation
                confirmation_result = await self._wait_for_confirmation(tx_id, submission_result['tx_id'])

                if confirmation_result['confirmed']:
                    event.blockchain_status = BlockchainStatus.CONFIRMED
                    event.blockchain_tx_id = confirmation_result['tx_id']

                    # Create blockchain transaction record
                    blockchain_tx = BlockchainTransaction(
                        tx_id=confirmation_result['tx_id'],
                        block_hash=confirmation_result['block_hash'],
                        block_number=confirmation_result['block_number'],
                        transaction_hash=confirmation_result['transaction_hash'],
                        timestamp=confirmation_result['timestamp'],
                        status=BlockchainStatus.CONFIRMED,
                        payload_hash=event.hash_value,
                        signature=await self._sign_transaction(event),
                        metadata={
                            'processing_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
                            'event_type': event.event_type.value,
                            'severity': event.severity.value
                        }
                    )

                    # Store blockchain transaction
                    await self._store_blockchain_transaction(blockchain_tx)

                    # Move from pending to confirmed
                    if tx_id in self.pending_transactions:
                        del self.pending_transactions[tx_id]
                    self.confirmed_transactions[tx_id] = blockchain_tx

                    # Update metrics
                    self.metrics['confirmed_transactions'] += 1
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    self.metrics['average_confirmation_time'] = (
                        (self.metrics['average_confirmation_time'] * (self.metrics['confirmed_transactions'] - 1) + processing_time) /
                        self.metrics['confirmed_transactions']
                    )

                    logger.info(f"[Blockchain Audit] Transaction {tx_id} confirmed in {processing_time:.2f}s")
                else:
                    event.blockchain_status = BlockchainStatus.FAILED
                    logger.warning(f"[Blockchain Audit] Transaction {tx_id} failed confirmation")

            else:
                event.blockchain_status = BlockchainStatus.FAILED
                logger.error(f"[Blockchain Audit] Failed to submit transaction {tx_id}")

            # Update event in database
            await self._update_audit_event_in_database(event)

            self.metrics['total_transactions'] += 1

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error processing transaction: {str(e)}")

    async def _submit_transaction_to_blockchain(self, tx_id: str, event: AuditEvent) -> Dict[str, Any]:
        """Submit transaction to Hyperledger Fabric blockchain"""
        try:
            # Create transaction proposal
            proposal = {
                'tx_id': tx_id,
                'chaincode_id': self.connection_config['chaincode_name'],
                'function': 'createAuditRecord',
                'args': [event.event_id, event.event_type.value, event.severity.value,
                         event.timestamp.isoformat(), event.user_id, event.action,
                         event.resource_type, event.resource_id,
                         json.dumps(event.old_values), json.dumps(event.new_values),
                         json.dumps(event.metadata)],
                'timestamp': datetime.utcnow().isoformat()
            }

            # Sign the proposal
            proposal['signature'] = await self._sign_transaction(proposal)

            # Submit to blockchain (simulation)
            # In production, this would use Fabric SDK
            await asyncio.sleep(1)  # Simulate blockchain processing time

            # Simulate successful submission
            blockchain_tx_id = f"blockchain_tx_{secrets.token_hex(8).upper()}"
            transaction_hash = hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest()

            submission_result = {
                'success': True,
                'tx_id': blockchain_tx_id,
                'transaction_hash': transaction_hash,
                'block_number': 1000 + len(self.confirmed_transactions),
                'timestamp': datetime.utcnow()
            }

            logger.debug(f"[Blockchain Audit] Submitted transaction {tx_id} to blockchain")
            return submission_result

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error submitting transaction to blockchain: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _wait_for_confirmation(self, tx_id: str, blockchain_tx_id: str,
                                timeout_seconds: int = 30) -> Dict[str, Any]:
        """Wait for blockchain transaction confirmation"""
        try:
            start_time = datetime.utcnow()

            while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
                # In production, this would query the blockchain for transaction status
                # For demo, we'll simulate confirmation

                await asyncio.sleep(2)  # Simulate blockchain confirmation time

                # Simulate successful confirmation
                confirmation_result = {
                    'confirmed': True,
                    'tx_id': blockchain_tx_id,
                    'block_hash': f"block_hash_{secrets.token_hex(16).upper()}",
                    'block_number': 1000 + len(self.confirmed_transactions),
                    'transaction_hash': hashlib.sha256(f"tx_{blockchain_tx_id}".encode()).hexdigest(),
                    'timestamp': datetime.utcnow()
                }

                return confirmation_result

            # Timeout occurred
            logger.warning(f"[Blockchain Audit] Timeout waiting for confirmation of {tx_id}")
            return {'confirmed': False, 'error': 'timeout'}

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error waiting for confirmation: {str(e)}")
            return {'confirmed': False, 'error': str(e)}

    async def _sign_transaction(self, transaction: Dict[str, Any]) -> str:
        """Sign transaction with master key"""
        try:
            # Create signature
            message = json.dumps(transaction, sort_keys=True, separators=(',', ':'))
            signature = hmac.new(
                self.master_key,
                message.encode(),
                hashlib.sha256
            ).digest()

            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error signing transaction: {str(e)}")
            return ""

    async def log_audit_event(self, event_type: AuditEventType, severity: AuditSeverity,
                             action: str, resource_type: str, resource_id: str = None,
                             user_id: str = None, session_id: str = None,
                             ip_address: str = None, user_agent: str = None,
                             old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None,
                             metadata: Dict[str, Any] = None) -> str:
        """Log an audit event to blockchain"""
        try:
            # Create audit event
            event = AuditEvent(
                event_id=f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}",
                event_type=event_type,
                severity=severity,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                metadata=metadata or {}
            )

            # Store event in database (pre-blockchain)
            await self._store_audit_event_in_database(event)

            # Submit to blockchain
            transaction = {
                'tx_id': f"tx_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}",
                'event': event
            }

            await self.transaction_queue.put(transaction)

            logger.info(f"[Blockchain Audit] Audit event logged: {event.event_id} ({event.event_type.value})")
            return event.event_id

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error logging audit event: {str(e)}")
            return ""

    async def _store_audit_event_in_database(self, event: AuditEvent) -> None:
        """Store audit event in database"""
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO audit_events (
                        event_id, event_type, severity, timestamp, user_id,
                        session_id, ip_address, user_agent, action,
                        resource_type, resource_id, old_values, new_values,
                        metadata, hash_value, blockchain_status,
                        blockchain_tx_id, created_at
                    ) VALUES (
                        :event_id, :event_type, :severity, :timestamp, :user_id,
                        :session_id, :ip_address, :user_agent, :action,
                        :resource_type, :resource_id, :old_values, :new_values,
                        :metadata, :hash_value, :blockchain_status,
                        :blockchain_tx_id, :created_at
                    )
                    ON CONFLICT (event_id) DO UPDATE SET
                        updated_at = NOW()
                """)

                db.execute(query, {
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'severity': event.severity.value,
                    'timestamp': event.timestamp,
                    'user_id': event.user_id,
                    'session_id': event.session_id,
                    'ip_address': event.ip_address,
                    'user_agent': event.user_agent,
                    'action': event.action,
                    'resource_type': event.resource_type,
                    'resource_id': event.resource_id,
                    'old_values': json.dumps(event.old_values),
                    'new_values': json.dumps(event.new_values),
                    'metadata': json.dumps(event.metadata),
                    'hash_value': event.hash_value,
                    'blockchain_status': event.blockchain_status.value,
                    'blockchain_tx_id': event.blockchain_tx_id,
                    'created_at': event.timestamp
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error storing audit event in database: {str(e)}")

    async def _update_audit_event_in_database(self, event: AuditEvent) -> None:
        """Update audit event in database"""
        try:
            with SessionLocal() as db:
                query = text("""
                    UPDATE audit_events
                    SET blockchain_status = :blockchain_status,
                        blockchain_tx_id = :blockchain_tx_id,
                        updated_at = NOW()
                    WHERE event_id = :event_id
                """)

                db.execute(query, {
                    'event_id': event.event_id,
                    'blockchain_status': event.blockchain_status.value,
                    'blockchain_tx_id': event.blockchain_tx_id
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error updating audit event in database: {str(e)}")

    async def _store_blockchain_transaction(self, transaction: BlockchainTransaction) -> None:
        """Store blockchain transaction in database"""
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO blockchain_transactions (
                        tx_id, block_hash, block_number, transaction_hash,
                        timestamp, status, payload_hash, signature,
                        metadata, created_at
                    ) VALUES (
                        :tx_id, :block_hash, :block_number, :transaction_hash,
                        :timestamp, :status, :payload_hash, :signature,
                        :metadata, :created_at
                    )
                    ON CONFLICT (tx_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = NOW()
                """)

                db.execute(query, {
                    'tx_id': transaction.tx_id,
                    'block_hash': transaction.block_hash,
                    'block_number': transaction.block_number,
                    'transaction_hash': transaction.transaction_hash,
                    'timestamp': transaction.timestamp,
                    'status': transaction.status.value,
                    'payload_hash': transaction.payload_hash,
                    'signature': transaction.signature,
                    'metadata': json.dumps(transaction.metadata),
                    'created_at': transaction.timestamp
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error storing blockchain transaction: {str(e)}")

    async def get_audit_trail(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit trail with optional filters"""
        try:
            if filters is None:
                filters = {}

            with SessionLocal() as db:
                # Build query
                where_clauses = []
                params = {}

                # Date range filter
                if 'start_date' in filters:
                    where_clauses.append("timestamp >= :start_date")
                    params['start_date'] = filters['start_date']
                if 'end_date' in filters:
                    where_clauses.append("timestamp <= :end_date")
                    params['end_date'] = filters['end_date']

                # Event type filter
                if 'event_types' in filters:
                    placeholders = ','.join([f":type_{i}" for i in range(len(filters['event_types']))])
                    where_clauses.append(f"event_type IN ({placeholders})")
                    for i, event_type in enumerate(filters['event_types']):
                        params[f"type_{i}"] = event_type.value

                # Severity filter
                if 'severities' in filters:
                    placeholders = ','.join([f":severity_{i}" for i in range(len(filters['severities']))])
                    where_clauses.append(f"severity IN ({placeholders})")
                    for i, severity in enumerate(filters['severities']):
                        params[f"severity_{i}"] = severity.value

                # User filter
                if 'user_id' in filters:
                    where_clauses.append("user_id = :user_id")
                    params['user_id'] = filters['user_id']

                # Resource type filter
                if 'resource_types' in filters:
                    placeholders = ','.join([f":resource_{i}" for i in range(len(filters['resource_types']))])
                    where_clauses.append(f"resource_type IN ({placeholders})")
                    for i, resource_type in enumerate(filters['resource_types']):
                        params[f"resource_{i}"] = resource_type

                # Build WHERE clause
                where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else "WHERE 1=1"

                # Build query
                query_text = f"""
                    SELECT
                        event_id, event_type, severity, timestamp, user_id,
                        session_id, ip_address, user_agent, action,
                        resource_type, resource_id, old_values, new_values,
                        metadata, hash_value, blockchain_status, blockchain_tx_id
                    FROM audit_events
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """

                result = db.execute(text(query_text), {**params, 'limit': limit}).fetchall()

                audit_trail = []
                for row in result:
                    audit_trail.append({
                        'event_id': row.event_id,
                        'event_type': row.event_type,
                        'severity': row.severity,
                        'timestamp': row.timestamp.isoformat(),
                        'user_id': row.user_id,
                        'session_id': row.session_id,
                        'ip_address': row.ip_address,
                        'user_agent': row.user_agent,
                        'action': row.action,
                        'resource_type': row.resource_type,
                        'resource_id': row.resource_id,
                        'old_values': json.loads(row.old_values) if row.old_values else {},
                        'new_values': json.loads(row.new_values) if row.new_values else {},
                        'metadata': json.loads(row.metadata) if row.metadata else {},
                        'hash_value': row.hash_value,
                        'blockchain_status': row.blockchain_status,
                        'blockchain_tx_id': row.blockchain_tx_id
                    })

                return audit_trail

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error retrieving audit trail: {str(e)}")
            return []

    async def get_blockchain_status(self) -> Dict[str, Any]:
        """Get blockchain system status"""
        try:
            return {
                'is_connected': self.is_connected,
                'total_transactions': self.metrics['total_transactions'],
                'confirmed_transactions': self.metrics['confirmed_transactions'],
                'failed_transactions': self.metrics['failed_transactions'],
                'average_confirmation_time': self.metrics['average_confirmation_time'],
                'pending_transactions': len(self.pending_transactions),
                'confirmed_transaction_ids': list(self.confirmed_transactions.keys()),
                'connection_config': {
                    'peer_url': self.connection_config['peer_url'],
                    'channel_name': self.connection_config['channel_name'],
                    'chaincode_name': self.connection_config['chaincode_name']
                },
                'crypto_suite': self.crypto_suite,
                'last_updated': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error getting blockchain status: {str(e)}")
            return {'error': str(e)}

    async def verify_transaction_integrity(self, event_id: str) -> Dict[str, Any]:
        """Verify transaction integrity by comparing hashes"""
        try:
            with SessionLocal() as db:
                # Get audit event
                result = db.execute(text("""
                    SELECT * FROM audit_events WHERE event_id = :event_id
                """), {'event_id': event_id}).fetchone()

                if not result:
                    return {'verified': False, 'error': 'Event not found'}

                # Get blockchain transaction if exists
                blockchain_result = db.execute(text("""
                    SELECT * FROM blockchain_transactions WHERE tx_id = :blockchain_tx_id
                """), {'blockchain_tx_id': result.blockchain_tx_id}).fetchone()

                # Recalculate hash
                original_hash = result.hash_value
                event_data = {
                    'event_id': result.event_id,
                    'event_type': result.event_type,
                    'severity': result.severity,
                    'timestamp': result.timestamp.isoformat(),
                    'user_id': result.user_id,
                    'action': result.action,
                    'resource_type': result.resource_type,
                    'resource_id': result.resource_id,
                    'old_values': json.loads(result.old_values) if result.old_values else {},
                    'new_values': json.loads(result.new_values) if result.new_values else {},
                    'metadata': json.loads(result.metadata) if result.metadata else {}
                }

                recalc_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

                # Compare hashes
                is_valid = original_hash == recalc_hash

                verification_result = {
                    'event_id': event_id,
                    'verified': is_valid,
                    'original_hash': original_hash,
                    'recalculated_hash': recalc_hash,
                    'hash_match': is_valid,
                    'blockchain_tx_id': result.blockchain_tx_id,
                    'blockchain_status': result.blockchain_status
                }

                if blockchain_result:
                    verification_result['blockchain_verification'] = {
                        'tx_id': blockchain_result.tx_id,
                        'block_hash': blockchain_result.block_hash,
                        'block_number': blockchain_result.block_number,
                        'transaction_hash': blockchain_result.transaction_hash,
                        'status': blockchain_result.status.value,
                        'timestamp': blockchain_result.timestamp.isoformat()
                    }

                logger.info(f"[Blockchain Audit] Integrity verification for {event_id}: {'VALID' if is_valid else 'INVALID'}")
                return verification_result

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error verifying transaction integrity: {str(e)}")
            return {'verified': False, 'error': str(e)}

    async def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup of old data"""
        try:
            while self.is_connected:
                # Run cleanup every hour
                await asyncio.sleep(3600)

                try:
                    # Clean up old pending transactions (older than 1 hour)
                    cutoff_time = datetime.utcnow() - timedelta(hours=1)
                    expired_transactions = [
                        tx_id for tx_id, tx_data in self.pending_transactions.items()
                        if tx_data['submitted_at'] < cutoff_time
                    ]

                    for tx_id in expired_transactions:
                        del self.pending_transactions[tx_id]
                        logger.warning(f"[Blockchain Audit] Cleaned up expired pending transaction: {tx_id}")

                    # Clean up old confirmed transactions (keep last 1000)
                    if len(self.confirmed_transactions) > 1000:
                        sorted_transactions = sorted(
                            self.confirmed_transactions.items(),
                            key=lambda x: x[1].timestamp,
                            reverse=True
                        )

                        keep_transactions = dict(sorted_transactions[:1000])
                        removed_count = len(self.confirmed_transactions) - len(keep_transactions)

                        for tx_id in list(self.confirmed_transactions.keys()):
                            if tx_id not in keep_transactions:
                                del self.confirmed_transactions[tx_id]

                        logger.info(f"[Blockchain Audit] Cleaned up {removed_count} old blockchain transactions")

                except Exception as e:
                    logger.error(f"[Blockchain Audit] Error in periodic cleanup: {str(e)}")

        except Exception as e:
            logger.error(f"[Blockchain Audit] Fatal error in periodic cleanup: {str(e)}")

    async def stop(self) -> None:
        """Stop blockchain integration"""
        try:
            logger.info("[Blockchain Audit] Stopping blockchain integration...")
            self.is_connected = False

            # Close any open connections would happen here in production
            logger.info("[Blockchain Audit] Blockchain integration stopped")

        except Exception as e:
            logger.error(f"[Blockchain Audit] Error stopping blockchain integration: {str(e)}")

# Global blockchain audit logging instance
blockchain_audit_logging = HyperledgerFabricIntegration()