"""
NPCI API Integration for Digital Cordon
Real-time payment interception and account blocking capabilities
"""

import asyncio
import aiohttp
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class CordonAction(Enum):
    """
    Types of digital cordon actions
    """
    ACCOUNT_BLOCK = "account_block"
    TRANSACTION_BLOCK = "transaction_block"
    UPI_ID_BLOCK = "upi_id_block"
    DEVICE_BLOCK = "device_block"
    IP_BLOCK = "ip_block"
    BENEFICIARY_LIMIT = "beneficiary_limit"
    TRANSACTION_LIMIT = "transaction_limit"
    MONITORING_ENHANCE = "monitoring_enhance"

class CordonStatus(Enum):
    """
    Digital cordon status
    """
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CordonPriority(Enum):
    """
    Cordon priority levels
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class DigitalCordon:
    """
    Digital cordon configuration
    """
    cordon_id: str
    target_type: str  # account, upi_id, phone, email, device_id
    target_value: str
    action: CordonAction
    priority: CordonPriority
    reason: str
    evidence: Dict[str, Any]
    duration_hours: int
    created_by: str
    created_at: datetime
    expires_at: datetime
    status: CordonStatus
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CordonExecution:
    """
    Cordon execution result
    """
    cordon_id: str
    execution_id: str
    npcii_response: Dict[str, Any]
    success: bool
    execution_time: datetime
    response_time_ms: int
    error_message: str = None
    affected_accounts: List[str] = None
    affected_transactions: List[str] = None

    def __post_init__(self):
        if self.affected_accounts is None:
            self.affected_accounts = []
        if self.affected_transactions is None:
            self.affected_transactions = []

class NPCIDigitalCordon:
    """
    NPCI API integration for digital payment cordon
    """

    def __init__(self):
        # NPCI API configuration
        self.base_url = "https://api.npci.org.in"
        self.api_version = "v2"
        self.auth_token = None
        self.api_key = None
        self.webhook_secret = None

        # Request signing
        self.signing_key = None
        self.request_timeout = 30

        # Rate limiting
        self.rate_limit = {
            'requests_per_second': 10,
            'requests_per_minute': 100,
            'burst_limit': 20
        }

        # Active cordons
        self.active_cordons = {}
        self.cordon_history = []

        # Cache for responses
        self.response_cache = {}

        # Emergency contact
        self.emergency_contacts = [
            "npci.operations@npci.org.in",
            "cybercell@npci.org.in"
        ]

    async def initialize(self) -> bool:
        """
        Initialize NPCI digital cordon system
        """
        try:
            logger.info("[NPCI Cordon] Initializing digital cordon system...")

            # Load configuration
            await self._load_configuration()

            # Initialize authentication
            await self._initialize_authentication()

            # Setup webhook endpoints
            await self._setup_webhooks()

            # Test API connectivity
            connectivity_test = await self._test_api_connectivity()
            if not connectivity_test:
                logger.error("[NPCI Cordon] API connectivity test failed")
                return False

            # Load active cordons from database
            await self._load_active_cordons()

            logger.info("[NPCI Cordon] Digital cordon system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error initializing cordon system: {str(e)}")
            return False

    async def _load_configuration(self) -> None:
        """
        Load NPCI API configuration
        """
        try:
            # In production, these would come from secure configuration
            self.api_key = os.getenv("NPCI_API_KEY", "npci_api_key_2025_demo")
            self.auth_token = os.getenv("NPCI_AUTH_TOKEN", "npci_auth_token_2025_demo")
            self.webhook_secret = os.getenv("NPCI_WEBHOOK_SECRET", "npci_webhook_secret_2025_demo")

            # Generate signing key
            password = b"npci_signing_key_2025"
            salt = b"npci_salt_2025"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.signing_key = base64.urlsafe_b64encode(kdf.derive(password))

            logger.info("[NPCI Cordon] Configuration loaded")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error loading configuration: {str(e)}")

    async def _initialize_authentication(self) -> None:
        """
        Initialize NPCI API authentication
        """
        try:
            # Authenticate with NPCI API
            auth_headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }

            # Test authentication
            async with aiohttp.ClientSession(headers=auth_headers) as session:
                async with session.get(
                    f"{self.base_url}/auth/verify",
                    timeout=self.request_timeout
                ) as response:
                    if response.status == 200:
                        logger.info("[NPCI Cordon] Authentication successful")
                    else:
                        logger.warning(f"[NPCI Cordon] Authentication failed: {response.status}")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error initializing authentication: {str(e)}")

    async def _setup_webhooks(self) -> None:
        """
        Setup webhook endpoints for NPCI notifications
        """
        try:
            webhook_config = {
                "webhook_url": "https://aegis.cybercrime.gov.in/webhooks/npci",
                "events": [
                    "cordon_status_update",
                    "transaction_blocked",
                    "account_suspended",
                    "suspicious_activity"
                ],
                "secret": self.webhook_secret,
                "active": True
            }

            # Register webhook (simulated)
            logger.info("[NPCI Cordon] Webhooks configured successfully")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error setting up webhooks: {str(e)}")

    async def _test_api_connectivity(self) -> bool:
        """
        Test NPCI API connectivity
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-API-Key': self.api_key
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=self.request_timeout
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"[NPCI Cordon] API connectivity test failed: {str(e)}")
            return False

    async def _load_active_cordons(self) -> None:
        """
        Load active cordons from database
        """
        try:
            with SessionLocal() as db:
                result = db.execute(text("""
                    SELECT * FROM digital_cordons
                    WHERE status = 'active'
                    AND expires_at > NOW()
                    ORDER BY created_at DESC
                """)).fetchall()

                for row in result:
                    cordon = DigitalCordon(
                        cordon_id=row.cordon_id,
                        target_type=row.target_type,
                        target_value=row.target_value,
                        action=CordonAction(row.action),
                        priority=CordonPriority(row.priority),
                        reason=row.reason,
                        evidence=json.loads(row.evidence),
                        duration_hours=row.duration_hours,
                        created_by=row.created_by,
                        created_at=row.created_at,
                        expires_at=row.expires_at,
                        status=CordonStatus(row.status),
                        metadata=json.loads(row.metadata) if row.metadata else {}
                    )
                    self.active_cordons[cordon.cordon_id] = cordon

            logger.info(f"[NPCI Cordon] Loaded {len(self.active_cordons)} active cordons")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error loading active cordons: {str(e)}")

    async def create_digital_cordon(self, target_type: str, target_value: str,
                                 action: CordonAction, priority: CordonPriority,
                                 reason: str, evidence: Dict[str, Any],
                                 duration_hours: int = 24,
                                 created_by: str = "system") -> DigitalCordon:
        """
        Create a new digital cordon
        """
        try:
            cordon_id = f"cordon_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=duration_hours)

            cordon = DigitalCordon(
                cordon_id=cordon_id,
                target_type=target_type,
                target_value=target_value,
                action=action,
                priority=priority,
                reason=reason,
                evidence=evidence,
                duration_hours=duration_hours,
                created_by=created_by,
                created_at=created_at,
                expires_at=expires_at,
                status=CordonStatus.PENDING
            )

            # Store cordon in database
            await self._store_cordon(cordon)

            # Execute cordon if high priority
            if priority in [CordonPriority.HIGH, CordonPriority.CRITICAL, CordonPriority.EMERGENCY]:
                execution_result = await self.execute_cordon(cordon_id)
                if execution_result.success:
                    cordon.status = CordonStatus.ACTIVE
                    await self._update_cordon_status(cordon_id, CordonStatus.ACTIVE)
                else:
                    cordon.status = CordonStatus.FAILED
                    await self._update_cordon_status(cordon_id, CordonStatus.FAILED)

            self.active_cordons[cordon_id] = cordon
            self.cordon_history.append(cordon)

            logger.info(f"[NPCI Cordon] Created digital cordon: {cordon_id}")
            return cordon

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error creating digital cordon: {str(e)}")
            raise

    async def execute_cordon(self, cordon_id: str) -> CordonExecution:
        """
        Execute a digital cordon via NPCI API
        """
        try:
            if cordon_id not in self.active_cordons:
                raise ValueError(f"Cordon {cordon_id} not found")

            cordon = self.active_cordons[cordon_id]
            execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

            start_time = datetime.utcnow()

            # Prepare NPCI API request
            npcii_request = await self._prepare_npcii_request(cordon)

            # Sign request
            signed_request = await self._sign_request(npcii_request)

            # Execute request
            execution_result = await self._send_npcii_request(signed_request, cordon_id, execution_id)

            # Calculate response time
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Create execution record
            cordon_execution = CordonExecution(
                cordon_id=cordon_id,
                execution_id=execution_id,
                npcii_response=execution_result,
                success=execution_result.get('success', False),
                execution_time=start_time,
                response_time_ms=response_time_ms,
                error_message=execution_result.get('error'),
                affected_accounts=execution_result.get('affected_accounts', []),
                affected_transactions=execution_result.get('affected_transactions', [])
            )

            # Store execution result
            await self._store_execution_result(cordon_execution)

            # Update cordon status
            if cordon_execution.success:
                await self._update_cordon_status(cordon_id, CordonStatus.ACTIVE)
                # Schedule expiry
                asyncio.create_task(self._schedule_cordon_expiry(cordon_id))
            else:
                await self._update_cordon_status(cordon_id, CordonStatus.FAILED)

            logger.info(f"[NPCI Cordon] Executed cordon {cordon_id}: {'SUCCESS' if cordon_execution.success else 'FAILED'}")
            return cordon_execution

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error executing cordon {cordon_id}: {str(e)}")
            # Return failed execution
            return CordonExecution(
                cordon_id=cordon_id,
                execution_id=f"exec_failed_{secrets.token_hex(4)}",
                npcii_response={'error': str(e)},
                success=False,
                execution_time=datetime.utcnow(),
                response_time_ms=0,
                error_message=str(e)
            )

    async def _prepare_npcii_request(self, cordon: DigitalCordon) -> Dict[str, Any]:
        """
        Prepare NPCI API request
        """
        try:
            base_request = {
                "request_id": f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                "timestamp": datetime.utcnow().isoformat(),
                "request_type": cordon.action.value,
                "priority": cordon.priority.value,
                "target": {
                    "type": cordon.target_type,
                    "value": cordon.target_value
                },
                "duration_hours": cordon.duration_hours,
                "reason": cordon.reason,
                "evidence": cordon.evidence,
                "requesting_authority": "AEGIS_Cybercrime",
                "contact_information": {
                    "email": "aegis@cybercrime.gov.in",
                    "phone": "+91-11-23456789"
                },
                "legal_reference": {
                    "act": "Information Technology Act, 2000",
                    "section": "Section 66D",
                    "case_id": cordon.metadata.get('case_id', 'TBD')
                }
            }

            # Add action-specific parameters
            if cordon.action == CordonAction.ACCOUNT_BLOCK:
                base_request["block_parameters"] = {
                    "block_all_transactions": True,
                    "block_upi": True,
                    "block_imps": True,
                    "freeze_account": True,
                    "notification_to_banks": True
                }

            elif cordon.action == CordonAction.TRANSACTION_BLOCK:
                base_request["block_parameters"] = {
                    "transaction_types": ["IMPS", "UPI", "NEFT", "RTGS"],
                    "amount_threshold": cordon.metadata.get('amount_threshold', 0),
                    "duration_hours": cordon.duration_hours
                }

            elif cordon.action == CordonAction.UPI_ID_BLOCK:
                base_request["block_parameters"] = {
                    "block_all_upi_handles": True,
                    "block_qr_code": True,
                    "notification_to_psp": True
                }

            elif cordon.action == CordonAction.BENEFICIARY_LIMIT:
                base_request["limit_parameters"] = {
                    "daily_limit": cordon.metadata.get('daily_limit', 10000),
                    "transaction_limit": cordon.metadata.get('transaction_limit', 5000),
                    "beneficiary_limit_type": "per_beneficiary"
                }

            return base_request

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error preparing NPCI request: {str(e)}")
            return {}

    async def _sign_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign NPCI API request
        """
        try:
            # Create signature
            message = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
            signature = hmac.new(
                self.signing_key,
                message.encode(),
                hashes.sha256
            ).digest()

            # Add signature to request
            signed_request = request_data.copy()
            signed_request['signature'] = base64.b64encode(signature).decode()
            signed_request['signing_method'] = 'HMAC-SHA256'
            signed_request['timestamp'] = datetime.utcnow().isoformat()

            return signed_request

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error signing request: {str(e)}")
            return request_data

    async def _send_npcii_request(self, signed_request: Dict[str, Any],
                                cordon_id: str, execution_id: str) -> Dict[str, Any]:
        """
        Send signed request to NPCI API
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json',
                'X-Request-ID': execution_id,
                'X-Cordon-ID': cordon_id
            }

            # In production, this would be the actual NPCI API endpoint
            api_endpoint = f"{self.base_url}/{self.api_version}/digital-cordon/execute"

            # Simulate NPCI API response
            if self._simulate_npcii_response(signed_request):
                return {
                    'success': True,
                    'request_id': signed_request.get('request_id'),
                    'cordon_id': cordon_id,
                    'execution_id': execution_id,
                    'npci_reference': f"NPCI{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}",
                    'status': 'ACTIVE',
                    'affected_accounts': await self._get_affected_accounts(signed_request),
                    'affected_transactions': await self._get_affected_transactions(signed_request),
                    'next_steps': [
                        "All participating banks notified",
                        "Payment systems updated",
                        "Monitoring systems alerted"
                    ],
                    'expiry_time': (datetime.utcnow() + timedelta(hours=24)).isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'NPCI validation failed',
                    'error_code': 'VALIDATION_ERROR',
                    'details': 'Target account not found or insufficient evidence'
                }

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error sending NPCI request: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'API_ERROR'
            }

    def _simulate_npcii_response(self, request_data: Dict[str, Any]) -> bool:
        """
        Simulate NPCI API response for demo purposes
        """
        try:
            # Simulate validation logic
            priority = request_data.get('priority', 'medium')
            target = request_data.get('target', {})
            target_type = target.get('type', '')
            target_value = target.get('value', '')

            # High priority requests are more likely to succeed
            success_probability = {
                'emergency': 0.95,
                'critical': 0.9,
                'high': 0.8,
                'medium': 0.7,
                'low': 0.6
            }.get(priority, 0.5)

            # Simulate NPCI validation
            if target_type and target_value:
                # Simple validation simulation
                if target_type in ['account', 'upi_id', 'phone'] and len(target_value) > 5:
                    success_probability += 0.2

            return random.random() < success_probability

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error simulating NPCI response: {str(e)}")
            return False

    async def _get_affected_accounts(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Get list of affected accounts
        """
        try:
            target = request_data.get('target', {})
            target_type = target.get('type', '')
            target_value = target.get('value', '')

            affected_accounts = []

            # Simulate affected accounts based on target type
            if target_type == 'account':
                affected_accounts.append(target_value)
                # Add related accounts
                affected_accounts.extend([
                    f"{target_value}_01",
                    f"{target_value}_02"
                ])
            elif target_type == 'upi_id':
                affected_accounts.append(f"ACC_{target_value}")
            elif target_type == 'phone':
                affected_accounts.extend([
                    f"ACC_PHONE_{target_value}",
                    f"ACC_PHONE2_{target_value}"
                ])

            return affected_accounts

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error getting affected accounts: {str(e)}")
            return []

    async def _get_affected_transactions(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Get list of affected transactions
        """
        try:
            # Simulate recent transactions that would be blocked
            transactions = []
            for i in range(random.randint(1, 5)):
                tx_id = f"TXN{datetime.utcnow().strftime('%Y%m%d')}{i:06d}"
                transactions.append(tx_id)

            return transactions

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error getting affected transactions: {str(e)}")
            return []

    async def _store_cordon(self, cordon: DigitalCordon) -> None:
        """
        Store cordon in database
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO digital_cordons (
                        cordon_id, target_type, target_value, action, priority,
                        reason, evidence, duration_hours, created_by,
                        created_at, expires_at, status, metadata
                    ) VALUES (
                        :cordon_id, :target_type, :target_value, :action, :priority,
                        :reason, :evidence, :duration_hours, :created_by,
                        :created_at, :expires_at, :status, :metadata
                    )
                    ON CONFLICT (cordon_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        expires_at = EXCLUDED.expires_at
                """)

                db.execute(query, {
                    'cordon_id': cordon.cordon_id,
                    'target_type': cordon.target_type,
                    'target_value': cordon.target_value,
                    'action': cordon.action.value,
                    'priority': cordon.priority.value,
                    'reason': cordon.reason,
                    'evidence': json.dumps(cordon.evidence),
                    'duration_hours': cordon.duration_hours,
                    'created_by': cordon.created_by,
                    'created_at': cordon.created_at,
                    'expires_at': cordon.expires_at,
                    'status': cordon.status.value,
                    'metadata': json.dumps(cordon.metadata)
                })

                db.commit()

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error storing cordon: {str(e)}")

    async def _store_execution_result(self, execution: CordonExecution) -> None:
        """
        Store execution result
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO cordon_executions (
                        cordon_id, execution_id, npcii_response, success,
                        execution_time, response_time_ms, error_message,
                        affected_accounts, affected_transactions
                    ) VALUES (
                        :cordon_id, :execution_id, :npcii_response, :success,
                        :execution_time, :response_time_ms, :error_message,
                        :affected_accounts, :affected_transactions
                    )
                """)

                db.execute(query, {
                    'cordon_id': execution.cordon_id,
                    'execution_id': execution.execution_id,
                    'npcii_response': json.dumps(execution.npcii_response),
                    'success': execution.success,
                    'execution_time': execution.execution_time,
                    'response_time_ms': execution.response_time_ms,
                    'error_message': execution.error_message,
                    'affected_accounts': json.dumps(execution.affected_accounts),
                    'affected_transactions': json.dumps(execution.affected_transactions)
                })

                db.commit()

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error storing execution result: {str(e)}")

    async def _update_cordon_status(self, cordon_id: str, status: CordonStatus) -> None:
        """
        Update cordon status
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    UPDATE digital_cordons
                    SET status = :status,
                        updated_at = NOW()
                    WHERE cordon_id = :cordon_id
                """)

                db.execute(query, {
                    'cordon_id': cordon_id,
                    'status': status.value
                })

                db.commit()

            # Update in-memory cordon
            if cordon_id in self.active_cordons:
                self.active_cordons[cordon_id].status = status

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error updating cordon status: {str(e)}")

    async def _schedule_cordon_expiry(self, cordon_id: str) -> None:
        """
        Schedule cordon expiry
        """
        try:
            if cordon_id not in self.active_cordons:
                return

            cordon = self.active_cordons[cordon_id]
            delay = (cordon.expires_at - datetime.utcnow()).total_seconds()

            if delay > 0:
                await asyncio.sleep(delay)
                await self.release_cordon(cordon_id, "Auto-expired")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error scheduling cordon expiry: {str(e)}")

    async def release_cordon(self, cordon_id: str, reason: str = "Manual release") -> bool:
        """
        Release an active digital cordon
        """
        try:
            if cordon_id not in self.active_cordons:
                logger.warning(f"[NPCI Cordon] Cordon {cordon_id} not found in active cordons")
                return False

            cordon = self.active_cordons[cordon_id]

            # Send release request to NPCI
            release_result = await self._send_release_request(cordon)

            if release_result.get('success', False):
                # Update status
                await self._update_cordon_status(cordon_id, CordonStatus.RELEASED)

                # Remove from active cordons
                del self.active_cordons[cordon_id]

                logger.info(f"[NPCI Cordon] Released cordon {cordon_id}: {reason}")
                return True
            else:
                logger.error(f"[NPCI Cordon] Failed to release cordon {cordon_id}: {release_result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error releasing cordon {cordon_id}: {str(e)}")
            return False

    async def _send_release_request(self, cordon: DigitalCordon) -> Dict[str, Any]:
        """
        Send release request to NPCI
        """
        try:
            release_request = {
                "request_id": f"rel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                "timestamp": datetime.utcnow().isoformat(),
                "request_type": "release_cordon",
                "cordon_id": cordon.cordon_id,
                "target": {
                    "type": cordon.target_type,
                    "value": cordon.target_value
                },
                "reason": "Cordon expired/released",
                "requesting_authority": "AEGIS_Cybercrime"
            }

            # Sign request
            signed_request = await self._sign_request(release_request)

            # Simulate NPCI response
            return {
                'success': True,
                'request_id': release_request['request_id'],
                'cordon_id': cordon.cordon_id,
                'status': 'RELEASED',
                'release_time': datetime.utcnow().isoformat(),
                'affected_accounts': cordon.metadata.get('affected_accounts', []),
                'confirmation': "All restrictions have been lifted"
            }

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error sending release request: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_cordon_status(self, cordon_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a digital cordon
        """
        try:
            if cordon_id not in self.active_cordons:
                # Check in database
                with SessionLocal() as db:
                    result = db.execute(text("""
                        SELECT * FROM digital_cordons
                        WHERE cordon_id = :cordon_id
                    """), {'cordon_id': cordon_id}).fetchone()

                    if result:
                        return {
                            'cordon_id': result.cordon_id,
                            'status': result.status,
                            'target_type': result.target_type,
                            'target_value': result.target_value,
                            'action': result.action,
                            'created_at': result.created_at.isoformat(),
                            'expires_at': result.expires_at.isoformat(),
                            'created_by': result.created_by,
                            'reason': result.reason
                        }
                return None

            cordon = self.active_cordons[cordon_id]

            # Get latest execution result
            with SessionLocal() as db:
                execution_result = db.execute(text("""
                    SELECT * FROM cordon_executions
                    WHERE cordon_id = :cordon_id
                    ORDER BY execution_time DESC
                    LIMIT 1
                """), {'cordon_id': cordon_id}).fetchone()

            return {
                'cordon_id': cordon.cordon_id,
                'status': cordon.status.value,
                'target_type': cordon.target_type,
                'target_value': cordon.target_value,
                'action': cordon.action.value,
                'priority': cordon.priority.value,
                'created_at': cordon.created_at.isoformat(),
                'expires_at': cordon.expires_at.isoformat(),
                'created_by': cordon.created_by,
                'reason': cordon.reason,
                'evidence': cordon.evidence,
                'last_execution': {
                    'execution_id': execution_result.execution_id if execution_result else None,
                    'success': execution_result.success if execution_result else None,
                    'execution_time': execution_result.execution_time.isoformat() if execution_result else None,
                    'response_time_ms': execution_result.response_time_ms if execution_result else None,
                    'affected_accounts': json.loads(execution_result.affected_accounts) if execution_result and execution_result.affected_accounts else [],
                    'affected_transactions': json.loads(execution_result.affected_transactions) if execution_result and execution_result.affected_transactions else []
                }
            }

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error getting cordon status: {str(e)}")
            return None

    async def list_active_cordons(self, target_type: str = None) -> List[Dict[str, Any]]:
        """
        List all active digital cordons
        """
        try:
            cordons = []

            for cordon_id, cordon in self.active_cordons.items():
                if target_type is None or cordon.target_type == target_type:
                    cordons.append({
                        'cordon_id': cordon.cordon_id,
                        'target_type': cordon.target_type,
                        'target_value': cordon.target_value[:8] + "***" if len(cordon.target_value) > 8 else cordon.target_value,
                        'action': cordon.action.value,
                        'priority': cordon.priority.value,
                        'status': cordon.status.value,
                        'created_at': cordon.created_at.isoformat(),
                        'expires_at': cordon.expires_at.isoformat(),
                        'created_by': cordon.created_by,
                        'reason': cordon.reason
                    })

            # Sort by priority and creation time
            priority_order = {'emergency': 5, 'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            cordons.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['created_at']), reverse=True)

            return cordons

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error listing active cordons: {str(e)}")
            return []

    async def emergency_cordon(self, target_type: str, target_value: str,
                            evidence: Dict[str, Any], case_id: str = None) -> DigitalCordon:
        """
        Create emergency digital cordon with highest priority
        """
        try:
            logger.warning(f"[NPCI Cordon] EMERGENCY CORDON requested for {target_type}: {target_value}")

            emergency_cordon = await self.create_digital_cordon(
                target_type=target_type,
                target_value=target_value,
                action=CordonAction.ACCOUNT_BLOCK,
                priority=CordonPriority.EMERGENCY,
                reason=f"EMERGENCY: Immediate threat detected - Case {case_id or 'TBD'}",
                evidence=evidence,
                duration_hours=72,  # 3 days for emergency
                created_by="emergency_system"
            )

            # Notify emergency contacts
            await self._notify_emergency_contacts(emergency_cordon)

            return emergency_cordon

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error creating emergency cordon: {str(e)}")
            raise

    async def _notify_emergency_contacts(self, cordon: DigitalCordon) -> None:
        """
        Notify emergency contacts about cordon activation
        """
        try:
            notification_data = {
                'cordon_id': cordon.cordon_id,
                'priority': cordon.priority.value,
                'target_type': cordon.target_type,
                'target_value': cordon.target_value,
                'action': cordon.action.value,
                'reason': cordon.reason,
                'created_at': cordon.created_at.isoformat(),
                'evidence': cordon.evidence
            }

            # In production, would send actual notifications
            logger.warning(f"[NPCI Cordon] EMERGENCY NOTIFICATION sent to {self.emergency_contacts}")
            logger.warning(f"[NPCI Cordon] Notification data: {json.dumps(notification_data, default=str)}")

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error notifying emergency contacts: {str(e)}")

    async def extend_cordon(self, cordon_id: str, additional_hours: int,
                          reason: str = "Extension requested") -> bool:
        """
        Extend an existing digital cordon
        """
        try:
            if cordon_id not in self.active_cordons:
                return False

            cordon = self.active_cordons[cordon_id]
            old_expiry = cordon.expires_at
            cordon.expires_at = cordon.expires_at + timedelta(hours=additional_hours)
            cordon.duration_hours += additional_hours

            # Update in database
            with SessionLocal() as db:
                query = text("""
                    UPDATE digital_cordons
                    SET expires_at = :expires_at,
                        duration_hours = :duration_hours,
                        updated_at = NOW()
                    WHERE cordon_id = :cordon_id
                """)

                db.execute(query, {
                    'cordon_id': cordon_id,
                    'expires_at': cordon.expires_at,
                    'duration_hours': cordon.duration_hours
                })

                db.commit()

            # Schedule new expiry
            asyncio.create_task(self._schedule_cordon_expiry(cordon_id))

            logger.info(f"[NPCI Cordon] Extended cordon {cordon_id} by {additional_hours} hours. New expiry: {cordon.expires_at}")
            return True

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error extending cordon {cordon_id}: {str(e)}")
            return False

    async def get_cordon_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get digital cordon statistics
        """
        try:
            with SessionLocal() as db:
                # Get overall statistics
                result = db.execute(text("""
                    SELECT
                        COUNT(*) as total_cordons,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_cordons,
                        COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_cordons,
                        COUNT(CASE WHEN status = 'released' THEN 1 END) as released_cordons,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_cordons,
                        AVG(duration_hours) as avg_duration_hours
                    FROM digital_cordons
                    WHERE created_at >= NOW() - INTERVAL ':days_back days'
                """), {'days_back': days_back}).fetchone()

                # Get statistics by action type
                action_stats = db.execute(text("""
                    SELECT action, COUNT(*) as count
                    FROM digital_cordons
                    WHERE created_at >= NOW() - INTERVAL ':days_back days'
                    GROUP BY action
                    ORDER BY count DESC
                """), {'days_back': days_back}).fetchall()

                # Get statistics by priority
                priority_stats = db.execute(text("""
                    SELECT priority, COUNT(*) as count
                    FROM digital_cordons
                    WHERE created_at >= NOW() - INTERVAL ':days_back days'
                    GROUP BY priority
                    ORDER BY count DESC
                """), {'days_back': days_back}).fetchone()

                return {
                    'total_cordons': result.total_cordons or 0,
                    'active_cordons': result.active_cordons or 0,
                    'expired_cordons': result.expired_cordons or 0,
                    'released_cordons': result.released_cordons or 0,
                    'failed_cordons': result.failed_cordons or 0,
                    'avg_duration_hours': float(result.avg_duration_hours) if result.avg_duration_hours else 0,
                    'action_distribution': {row.action: row.count for row in action_stats},
                    'priority_distribution': {row.priority: row.count for row in priority_stats},
                    'currently_active': len(self.active_cordons),
                    'period_days': days_back
                }

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error getting cordon statistics: {str(e)}")
            return {}

    async def cleanup_expired_cordons(self) -> int:
        """
        Clean up expired cordons
        """
        try:
            expired_count = 0
            now = datetime.utcnow()

            expired_cordons = [
                cordon_id for cordon_id, cordon in self.active_cordons.items()
                if cordon.expires_at <= now
            ]

            for cordon_id in expired_cordons:
                await self.release_cordon(cordon_id, "Auto-cleanup - expired")
                expired_count += 1

            logger.info(f"[NPCI Cordon] Cleaned up {expired_count} expired cordons")
            return expired_count

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error cleaning up expired cordons: {str(e)}")
            return 0

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get digital cordon system status
        """
        try:
            return {
                'api_connected': True,  # Would check actual API connectivity
                'active_cordons': len(self.active_cordons),
                'cordons_by_priority': {
                    priority.value: len([c for c in self.active_cordons.values() if c.priority == priority])
                    for priority in CordonPriority
                },
                'cordons_by_action': {
                    action.value: len([c for c in self.active_cordons.values() if c.action == action])
                    for action in CordonAction
                },
                'upcoming_expiries': len([
                    c for c in self.active_cordons.values()
                    if (c.expires_at - datetime.utcnow()).total_seconds() < 3600  # Next hour
                ]),
                'emergency_contacts': len(self.emergency_contacts),
                'last_cleanup': datetime.utcnow().isoformat(),
                'system_uptime': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[NPCI Cordon] Error getting system status: {str(e)}")
            return {'error': str(e)}

# Global NPCI digital cordon instance
npci_digital_cordon = NPCIDigitalCordon()