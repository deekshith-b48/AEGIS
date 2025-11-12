"""
Multi-Channel Alert System
Comprehensive alerting system with email, SMS, WhatsApp, push notifications, and dashboard alerts
"""

import asyncio
import aiohttp
import json
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """
    Alert severity levels
    """
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """
    Alert delivery channels
    """
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH_NOTIFICATION = "push_notification"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TELEGRAM = "telegram"

class AlertStatus(Enum):
    """
    Alert status
    """
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

@dataclass
class AlertMessage:
    """
    Alert message structure
    """
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    channels: List[AlertChannel]
    recipients: List[Dict[str, str]]  # List of recipient dicts with contact info
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    priority: int = 1  # 1-10, where 10 is highest
    category: str = "general"
    source: str = "aegis"
    requires_acknowledgment: bool = False
    escalation_rules: List[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.escalation_rules is None:
            self.escalation_rules = []

@dataclass
class AlertDelivery:
    """
    Alert delivery result
    """
    alert_id: str
    channel: AlertChannel
    recipient: str
    status: AlertStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: str = None
    delivery_details: Dict[str, Any] = None

    def __post_init__(self):
        if self.delivery_details is None:
            self.delivery_details = {}

@dataclass
class EscalationRule:
    """
    Alert escalation rule
    """
    rule_id: str
    condition: str  # "no_acknowledgment", "high_severity", "time_elapsed"
    threshold: Any  # Severity level, time in minutes, etc.
    action: str  # "escalate_channel", "add_recipients", "increase_priority"
    parameters: Dict[str, Any]
    is_active: bool = True

class MultiChannelAlertSystem:
    """
    Multi-channel alert system for real-time notifications
    """

    def __init__(self):
        # Alert storage
        self.active_alerts = {}
        self.alert_history = []
        self.delivery_queue = asyncio.Queue()

        # Channel configurations
        self.channel_configs = {}
        self.rate_limits = {}

        # Escalation rules
        self.escalation_rules = []

        # Delivery tracking
        self.delivery_stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'by_channel': {},
            'by_severity': {}
        }

        # Contact management
        self.contact_groups = {}
        self.recipient_preferences = {}

        # External service configurations
        self.smtp_config = {}
        self.sms_config = {}
        self.whatsapp_config = {}
        self.push_config = {}

        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [30, 120, 300]  # seconds

    async def initialize(self) -> bool:
        """
        Initialize alert system
        """
        try:
            logger.info("[Alert System] Initializing multi-channel alert system...")

            # Load channel configurations
            await self._load_channel_configurations()

            # Load contact groups
            await self._load_contact_groups()

            # Load escalation rules
            await self._load_escalation_rules()

            # Initialize external services
            await self._initialize_external_services()

            # Start delivery workers
            await self._start_delivery_workers()

            # Start escalation monitor
            asyncio.create_task(self._monitor_escalations())

            # Start cleanup task
            asyncio.create_task(self._cleanup_expired_alerts())

            logger.info("[Alert System] Multi-channel alert system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Alert System] Error initializing alert system: {str(e)}")
            return False

    async def _load_channel_configurations(self) -> None:
        """
        Load configurations for each alert channel
        """
        try:
            # Email configuration
            self.channel_configs[AlertChannel.EMAIL] = {
                'enabled': True,
                'max_recipients_per_message': 50,
                'rate_limit_per_minute': 100,
                'template_engine': 'jinja2',
                'default_sender': 'alerts@aegis.cybercrime.gov.in',
                'reply_to': 'support@aegis.cybercrime.gov.in'
            }

            # SMS configuration
            self.channel_configs[AlertChannel.SMS] = {
                'enabled': True,
                'max_length': 160,
                'rate_limit_per_minute': 50,
                'provider': 'twilio',  # Could be 'twilio', 'msg91', etc.
                'sender_id': 'AEGISA'
            }

            # WhatsApp configuration
            self.channel_configs[AlertChannel.WHATSAPP] = {
                'enabled': True,
                'max_length': 1000,
                'rate_limit_per_minute': 30,
                'provider': 'twilio',
                'template_namespace': 'aegis_alerts'
            }

            # Push notification configuration
            self.channel_configs[AlertChannel.PUSH_NOTIFICATION] = {
                'enabled': True,
                'max_length': 200,
                'rate_limit_per_minute': 200,
                'provider': 'firebase',
                'ttl_seconds': 3600
            }

            # Dashboard configuration
            self.channel_configs[AlertChannel.DASHBOARD] = {
                'enabled': True,
                'max_active_alerts': 1000,
                'auto_expire_hours': 24,
                'refresh_interval_seconds': 30
            }

            # Webhook configuration
            self.channel_configs[AlertChannel.WEBHOOK] = {
                'enabled': True,
                'timeout_seconds': 30,
                'max_retries': 3,
                'authentication_required': True
            }

            # Slack configuration
            self.channel_configs[AlertChannel.SLACK] = {
                'enabled': True,
                'max_message_length': 4000,
                'rate_limit_per_minute': 60,
                'webhook_urls': []
            }

            # Telegram configuration
            self.channel_configs[AlertChannel.TELEGRAM] = {
                'enabled': True,
                'max_message_length': 4096,
                'rate_limit_per_minute': 30,
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'chat_ids': []
            }

            logger.info("[Alert System] Channel configurations loaded")

        except Exception as e:
            logger.error(f"[Alert System] Error loading channel configurations: {str(e)}")

    async def _load_contact_groups(self) -> None:
        """
        Load contact groups and preferences
        """
        try:
            # Define contact groups
            self.contact_groups = {
                'cybercrime_team': [
                    {
                        'name': 'Cybercrime Response Team',
                        'email': 'cybercrime@ncrp.gov.in',
                        'phone': '+919876543210',
                        'whatsapp': '+919876543210',
                        'telegram_id': '@cybercrime_team',
                        'role': 'responder',
                        'priority': 1
                    }
                ],
                'banking_authorities': [
                    {
                        'name': 'Banking Fraud Team',
                        'email': 'fraud@rbi.org.in',
                        'phone': '+919876543211',
                        'whatsapp': '+919876543211',
                        'role': 'authority',
                        'priority': 2
                    }
                ],
                'law_enforcement': [
                    {
                        'name': 'Law Enforcement Coordination',
                        'email': 'cybercell@police.gov.in',
                        'phone': '+919876543212',
                        'whatsapp': '+919876543212',
                        'role': 'law_enforcement',
                        'priority': 3
                    }
                ],
                'field_officers': [
                    {
                        'name': 'Field Response Team',
                        'email': 'field@ncrp.gov.in',
                        'phone': '+919876543213',
                        'whatsapp': '+919876543213',
                        'role': 'field_responder',
                        'priority': 4
                    }
                ],
                'analytics_team': [
                    {
                        'name': 'Analytics Team',
                        'email': 'analytics@cybercrime.gov.in',
                        'phone': '+919876543214',
                        'role': 'analyst',
                        'priority': 5
                    }
                ],
                'management': [
                    {
                        'name': 'Senior Management',
                        'email': 'director@cybercrime.gov.in',
                        'phone': '+919876543215',
                        'role': 'management',
                        'priority': 6
                    }
                ]
            }

            # Set channel preferences for different times
            self.recipient_preferences = {
                'business_hours': {  # 9 AM - 6 PM
                    'default_channels': [AlertChannel.EMAIL, AlertChannel.DASHBOARD],
                    'high_severity_channels': [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.DASHBOARD],
                    'critical_channels': [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.DASHBOARD]
                },
                'after_hours': {  # 6 PM - 9 AM
                    'default_channels': [AlertChannel.EMAIL, AlertChannel.SMS],
                    'high_severity_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.DASHBOARD],
                    'critical_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD]
                },
                'emergency': {  # All hours for critical alerts
                    'default_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD],
                    'high_severity_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD],
                    'critical_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD]
                }
            }

            logger.info("[Alert System] Contact groups loaded")

        except Exception as e:
            logger.error(f"[Alert System] Error loading contact groups: {str(e)}")

    async def _load_escalation_rules(self) -> None:
        """
        Load escalation rules
        """
        try:
            self.escalation_rules = [
                EscalationRule(
                    rule_id="no_ack_critical",
                    condition="no_acknowledgment",
                    threshold=AlertSeverity.CRITICAL,
                    action="escalate_channel",
                    parameters={
                        'add_channels': [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM],
                        'add_recipients': ['management'],
                        'delay_minutes': 5
                    }
                ),
                EscalationRule(
                    rule_id="time_elapsed_high",
                    condition="time_elapsed",
                    threshold=30,  # minutes
                    action="add_recipients",
                    parameters={
                        'add_groups': ['law_enforcement'],
                        'increase_priority': True
                    }
                ),
                EscalationRule(
                    rule_id="multiple_failures",
                    condition="delivery_failures",
                    threshold=2,
                    action="escalate_channel",
                    parameters={
                        'switch_to': [AlertChannel.SMS, AlertChannel.TELEGRAM],
                        'exclude_channel': [AlertChannel.EMAIL]
                    }
                )
            ]

            logger.info("[Alert System] Escalation rules loaded")

        except Exception as e:
            logger.error(f"[Alert System] Error loading escalation rules: {str(e)}")

    async def _initialize_external_services(self) -> None:
        """
        Initialize external service configurations
        """
        try:
            # SMTP configuration
            self.smtp_config = {
                'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                'port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('SMTP_USERNAME', 'alerts@aegis.cybercrime.gov.in'),
                'password': os.getenv('SMTP_PASSWORD', 'demo_password'),
                'use_tls': True
            }

            # SMS configuration
            self.sms_config = {
                'provider': os.getenv('SMS_PROVIDER', 'twilio'),
                'account_sid': os.getenv('TWILIO_ACCOUNT_SID', 'demo_sid'),
                'auth_token': os.getenv('TWILIO_AUTH_TOKEN', 'demo_token'),
                'from_number': os.getenv('TWILIO_FROM_NUMBER', '+1234567890')
            }

            # WhatsApp configuration
            self.whatsapp_config = {
                'provider': 'twilio',
                'account_sid': os.getenv('TWILIO_ACCOUNT_SID', 'demo_sid'),
                'auth_token': os.getenv('TWILIO_AUTH_TOKEN', 'demo_token'),
                'from_number': os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            }

            # Push notification configuration
            self.push_config = {
                'firebase_server_key': os.getenv('FIREBASE_SERVER_KEY', 'demo_key'),
                'api_url': 'https://fcm.googleapis.com/fcm/send'
            }

            logger.info("[Alert System] External service configurations loaded")

        except Exception as e:
            logger.error(f"[Alert System] Error initializing external services: {str(e)}")

    async def _start_delivery_workers(self) -> None:
        """
        Start background workers for alert delivery
        """
        try:
            # Start multiple delivery workers
            for i in range(3):  # 3 concurrent workers
                asyncio.create_task(self._delivery_worker(f"worker-{i}"))

            logger.info("[Alert System] Delivery workers started")

        except Exception as e:
            logger.error(f"[Alert System] Error starting delivery workers: {str(e)}")

    async def _delivery_worker(self, worker_name: str) -> None:
        """
        Background worker for processing alert deliveries
        """
        try:
            while True:
                try:
                    # Get alert delivery task from queue
                    delivery_task = await asyncio.wait_for(
                        self.delivery_queue.get(),
                        timeout=1.0
                    )

                    # Process delivery
                    await self._process_delivery(delivery_task, worker_name)

                    # Mark task as done
                    self.delivery_queue.task_done()

                except asyncio.TimeoutError:
                    # No tasks in queue, continue
                    await asyncio.sleep(0.1)
                    continue
                except Exception as e:
                    logger.error(f"[Alert System] Worker {worker_name} error: {str(e)}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"[Alert System] Worker {worker_name} fatal error: {str(e)}")

    async def create_alert(self, title: str, message: str, severity: AlertSeverity,
                         target_groups: List[str] = None,
                         recipients: List[Dict[str, str]] = None,
                         channels: List[AlertChannel] = None,
                         metadata: Dict[str, Any] = None,
                         requires_acknowledgment: bool = False,
                         expires_hours: int = 24) -> AlertMessage:
        """
        Create a new alert
        """
        try:
            alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=expires_hours) if expires_hours > 0 else None

            # Determine recipients
            alert_recipients = []
            if target_groups:
                for group in target_groups:
                    if group in self.contact_groups:
                        alert_recipients.extend(self.contact_groups[group])
            if recipients:
                alert_recipients.extend(recipients)

            # Determine channels based on severity and time
            if not channels:
                channels = await self._determine_channels(severity)

            # Set priority based on severity
            priority_map = {
                AlertSeverity.INFO: 1,
                AlertSeverity.LOW: 3,
                AlertSeverity.MEDIUM: 5,
                AlertSeverity.HIGH: 7,
                AlertSeverity.CRITICAL: 9,
                AlertSeverity.EMERGENCY: 10
            }
            priority = priority_map.get(severity, 5)

            # Create alert message
            alert = AlertMessage(
                alert_id=alert_id,
                title=title,
                message=message,
                severity=severity,
                channels=channels,
                recipients=alert_recipients,
                metadata=metadata or {},
                created_at=created_at,
                expires_at=expires_at,
                priority=priority,
                category=metadata.get('category', 'general') if metadata else 'general',
                source=metadata.get('source', 'aegis') if metadata else 'aegis',
                requires_acknowledgment=requires_acknowledgment,
                escalation_rules=self.escalation_rules
            )

            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Queue for delivery
            await self._queue_alert_delivery(alert)

            logger.info(f"[Alert System] Created alert {alert_id} with severity {severity.value}")
            return alert

        except Exception as e:
            logger.error(f"[Alert System] Error creating alert: {str(e)}")
            raise

    async def _determine_channels(self, severity: AlertSeverity) -> List[AlertChannel]:
        """
        Determine appropriate channels based on severity and time
        """
        try:
            current_hour = datetime.now().hour
            is_business_hours = 9 <= current_hour <= 18

            if is_business_hours:
                if severity in [AlertSeverity.INFO, AlertSeverity.LOW]:
                    return [AlertChannel.EMAIL, AlertChannel.DASHBOARD]
                elif severity in [AlertSeverity.MEDIUM]:
                    return [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.DASHBOARD]
                elif severity in [AlertSeverity.HIGH]:
                    return [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.DASHBOARD]
                else:  # CRITICAL, EMERGENCY
                    return [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD]
            else:
                # After hours
                if severity in [AlertSeverity.INFO, AlertSeverity.LOW]:
                    return [AlertChannel.EMAIL, AlertChannel.DASHBOARD]
                elif severity in [AlertSeverity.MEDIUM]:
                    return [AlertChannel.SMS, AlertChannel.DASHBOARD]
                elif severity in [AlertSeverity.HIGH]:
                    return [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.DASHBOARD]
                else:  # CRITICAL, EMERGENCY
                    return [AlertChannel.SMS, AlertChannel.WHATSAPP, AlertChannel.TELEGRAM, AlertChannel.DASHBOARD]

        except Exception as e:
            logger.error(f"[Alert System] Error determining channels: {str(e)}")
            return [AlertChannel.EMAIL, AlertChannel.DASHBOARD]

    async def _queue_alert_delivery(self, alert: AlertMessage) -> None:
        """
        Queue alert for delivery through all configured channels
        """
        try:
            for channel in alert.channels:
                if not self.channel_configs.get(channel, {}).get('enabled', False):
                    logger.warning(f"[Alert System] Channel {channel.value} is disabled, skipping")
                    continue

                for recipient in alert.recipients:
                    # Check if recipient has contact info for this channel
                    if await self._has_recipient_contact(recipient, channel):
                        delivery_task = {
                            'alert': alert,
                            'channel': channel,
                            'recipient': recipient,
                            'attempt': 1
                        }
                        await self.delivery_queue.put(delivery_task)

        except Exception as e:
            logger.error(f"[Alert System] Error queuing alert delivery: {str(e)}")

    async def _has_recipient_contact(self, recipient: Dict[str, str], channel: AlertChannel) -> bool:
        """
        Check if recipient has contact information for the channel
        """
        try:
            contact_fields = {
                AlertChannel.EMAIL: ['email'],
                AlertChannel.SMS: ['phone'],
                AlertChannel.WHATSAPP: ['whatsapp', 'phone'],
                AlertChannel.PUSH_NOTIFICATION: ['device_token'],
                AlertChannel.TELEGRAM: ['telegram_id']
            }

            required_fields = contact_fields.get(channel, [])
            for field in required_fields:
                if field in recipient and recipient[field]:
                    return True

            return False

        except Exception as e:
            logger.error(f"[Alert System] Error checking recipient contact: {str(e)}")
            return False

    async def _process_delivery(self, delivery_task: Dict[str, Any], worker_name: str) -> None:
        """
        Process individual alert delivery
        """
        try:
            alert = delivery_task['alert']
            channel = delivery_task['channel']
            recipient = delivery_task['recipient']
            attempt = delivery_task['attempt']

            logger.debug(f"[Alert System] {worker_name}: Processing {channel.value} delivery to {recipient.get('name', 'Unknown')} (attempt {attempt})")

            # Check rate limiting
            if await self._is_rate_limited(channel, recipient):
                logger.warning(f"[Alert System] Rate limit exceeded for {channel.value} to {recipient.get('name', 'Unknown')}")
                # Retry later
                await asyncio.sleep(60)
                await self.delivery_queue.put({
                    **delivery_task,
                    'attempt': attempt + 1
                })
                return

            # Send alert through appropriate channel
            success = await self._send_alert_channel(alert, channel, recipient)

            # Create delivery record
            delivery = AlertDelivery(
                alert_id=alert.alert_id,
                channel=channel,
                recipient=recipient.get('name', 'Unknown'),
                status=AlertStatus.SENT if success else AlertStatus.FAILED,
                sent_at=datetime.utcnow(),
                error_message=None if success else "Delivery failed"
            )

            # Store delivery record
            await self._store_delivery_record(delivery)

            # Update statistics
            if success:
                self.delivery_stats['total_sent'] += 1
                self.delivery_stats['by_channel'][channel.value] = self.delivery_stats['by_channel'].get(channel.value, 0) + 1
                self.delivery_stats['by_severity'][alert.severity.value] = self.delivery_stats['by_severity'].get(alert.severity.value, 0) + 1
            else:
                self.delivery_stats['total_failed'] += 1

            # Handle failures and retries
            if not success and attempt < self.max_retries:
                retry_delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
                await asyncio.sleep(retry_delay)
                await self.delivery_queue.put({
                    **delivery_task,
                    'attempt': attempt + 1
                })

        except Exception as e:
            logger.error(f"[Alert System] {worker_name}: Error processing delivery: {str(e)}")

    async def _is_rate_limited(self, channel: AlertChannel, recipient: Dict[str, str]) -> bool:
        """
        Check if rate limiting should be applied
        """
        try:
            # Simple rate limiting check (in production, would use proper rate limiting service)
            config = self.channel_configs.get(channel, {})
            rate_limit = config.get('rate_limit_per_minute', 100)

            # For demo, return False (no rate limiting)
            return False

        except Exception as e:
            logger.error(f"[Alert System] Error checking rate limit: {str(e)}")
            return False

    async def _send_alert_channel(self, alert: AlertMessage, channel: AlertChannel,
                               recipient: Dict[str, str]) -> bool:
        """
        Send alert through specific channel
        """
        try:
            if channel == AlertChannel.EMAIL:
                return await self._send_email(alert, recipient)
            elif channel == AlertChannel.SMS:
                return await self._send_sms(alert, recipient)
            elif channel == AlertChannel.WHATSAPP:
                return await self._send_whatsapp(alert, recipient)
            elif channel == AlertChannel.PUSH_NOTIFICATION:
                return await self._send_push_notification(alert, recipient)
            elif channel == AlertChannel.DASHBOARD:
                return await self._send_dashboard_alert(alert, recipient)
            elif channel == AlertChannel.WEBHOOK:
                return await self._send_webhook(alert, recipient)
            elif channel == AlertChannel.SLACK:
                return await self._send_slack_alert(alert, recipient)
            elif channel == AlertChannel.TELEGRAM:
                return await self._send_telegram_alert(alert, recipient)
            else:
                logger.warning(f"[Alert System] Unsupported channel: {channel.value}")
                return False

        except Exception as e:
            logger.error(f"[Alert System] Error sending alert via {channel.value}: {str(e)}")
            return False

    async def _send_email(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send email alert
        """
        try:
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = self.channel_configs[AlertChannel.EMAIL]['default_sender']
            msg['To'] = recipient['email']

            # HTML content
            html_content = f"""
            <html>
            <body>
                <h2 style="color: {self._get_severity_color(alert.severity)};">
                    {alert.severity.value.upper()} ALERT
                </h2>
                <h3>{alert.title}</h3>
                <p>{alert.message}</p>

                <div style="background-color: #f5f5f5; padding: 10px; margin: 10px 0;">
                    <strong>Alert Details:</strong><br>
                    <strong>ID:</strong> {alert.alert_id}<br>
                    <strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <strong>Severity:</strong> {alert.severity.value}<br>
                    <strong>Source:</strong> {alert.source}
                </div>

                {self._format_metadata_html(alert.metadata)}

                <hr>
                <p><small>This alert was generated by Project AEGIS Cybercrime Response System.</small></p>
                <p><small>If you need immediate assistance, contact the Cybercrime Response Team.</small></p>
            </body>
            </html>
            """

            # Plain text content
            text_content = f"""
{alert.severity.value.upper()} ALERT

{alert.title}

{alert.message}

Alert Details:
ID: {alert.alert_id}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Severity: {alert.severity.value}
Source: {alert.source}

{self._format_metadata_text(alert.metadata)}

---
This alert was generated by Project AEGIS Cybercrime Response System.
If you need immediate assistance, contact the Cybercrime Response Team.
            """

            msg.attach(MimeText(text_content, 'plain'))
            msg.attach(MimeText(html_content, 'html'))

            # Send email (simulation for demo)
            # In production, would use actual SMTP server
            logger.info(f"[Alert System] Email sent to {recipient['email']}: {alert.title}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending email: {str(e)}")
            return False

    async def _send_sms(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send SMS alert
        """
        try:
            phone = recipient.get('phone', recipient.get('whatsapp', ''))

            # Format SMS message (within 160 characters)
            sms_message = f"[{alert.severity.value.upper()}] {alert.title[:50]}. {alert.message[:80]}... ID: {alert.alert_id[-8:]}"

            # Send SMS (simulation for demo)
            logger.info(f"[Alert System] SMS sent to {phone}: {sms_message}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending SMS: {str(e)}")
            return False

    async def _send_whatsapp(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send WhatsApp alert
        """
        try:
            phone = recipient.get('whatsapp', recipient.get('phone', ''))

            # Format WhatsApp message
            whatsapp_message = f"""
*{alert.severity.value.upper()} ALERT*

{alert.title}

{alert.message}

*Alert ID:* {alert.alert_id}
*Time:* {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
*Severity:* {alert.severity.value}
*Source:* {alert.source}

---
Project AEGIS Cybercrime Response System
            """.strip()

            # Send WhatsApp message (simulation for demo)
            logger.info(f"[Alert System] WhatsApp sent to {phone}: {alert.title}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending WhatsApp: {str(e)}")
            return False

    async def _send_push_notification(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send push notification
        """
        try:
            device_token = recipient.get('device_token')

            if not device_token:
                logger.warning(f"[Alert System] No device token for {recipient.get('name', 'Unknown')}")
                return False

            # Create push notification payload
            push_payload = {
                'to': device_token,
                'notification': {
                    'title': f"{alert.severity.value.upper()}: {alert.title}",
                    'body': alert.message[:200] + ("..." if len(alert.message) > 200 else ""),
                    'sound': 'default',
                    'badge': 1
                },
                'data': {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity.value,
                    'category': alert.category,
                    'source': alert.source,
                    'created_at': alert.created_at.isoformat()
                }
            }

            # Send push notification (simulation for demo)
            logger.info(f"[Alert System] Push notification sent to {recipient.get('name', 'Unknown')}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending push notification: {str(e)}")
            return False

    async def _send_dashboard_alert(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send dashboard alert
        """
        try:
            # Store in database for dashboard display
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO dashboard_alerts (
                        alert_id, title, message, severity, category,
                        recipient, created_at, expires_at, metadata,
                        acknowledged, acknowledged_by, acknowledged_at
                    ) VALUES (
                        :alert_id, :title, :message, :severity, :category,
                        :recipient, :created_at, :expires_at, :metadata,
                        false, NULL, NULL
                    )
                    ON CONFLICT (alert_id) DO UPDATE SET
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at
                """)

                db.execute(query, {
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity.value,
                    'category': alert.category,
                    'recipient': recipient.get('name', 'System'),
                    'created_at': alert.created_at,
                    'expires_at': alert.expires_at,
                    'metadata': json.dumps(alert.metadata)
                })

                db.commit()

            logger.info(f"[Alert System] Dashboard alert created: {alert.alert_id}")
            return True

        except Exception as e:
            logger.error(f"[Alert System] Error creating dashboard alert: {str(e)}")
            return False

    async def _send_webhook(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send webhook alert
        """
        try:
            webhook_url = recipient.get('webhook_url')

            if not webhook_url:
                logger.warning(f"[Alert System] No webhook URL for {recipient.get('name', 'Unknown')}")
                return False

            # Create webhook payload
            webhook_payload = {
                'alert_id': alert.alert_id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'category': alert.category,
                'source': alert.source,
                'created_at': alert.created_at.isoformat(),
                'metadata': alert.metadata
            }

            # Send webhook (simulation for demo)
            logger.info(f"[Alert System] Webhook sent to {webhook_url}: {alert.title}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending webhook: {str(e)}")
            return False

    async def _send_slack_alert(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send Slack alert
        """
        try:
            webhook_url = recipient.get('slack_webhook_url')

            if not webhook_url:
                # Use default Slack webhook
                webhook_urls = self.channel_configs[AlertChannel.SLACK].get('webhook_urls', [])
                if not webhook_urls:
                    logger.warning("[Alert System] No Slack webhook configured")
                    return False
                webhook_url = webhook_urls[0]

            # Create Slack message
            color_map = {
                AlertSeverity.INFO: '#36a64f',      # green
                AlertSeverity.LOW: '#36a64f',       # green
                AlertSeverity.MEDIUM: '#ff9500',    # orange
                AlertSeverity.HIGH: '#ff0000',      # red
                AlertSeverity.CRITICAL: '#8b0000',   # dark red
                AlertSeverity.EMERGENCY: '#8b0000'    # dark red
            }

            slack_payload = {
                'attachments': [{
                    'color': color_map.get(alert.severity, '#36a64f'),
                    'title': f"[{alert.severity.value.upper()}] {alert.title}",
                    'text': alert.message,
                    'fields': [
                        {
                            'title': 'Alert ID',
                            'value': alert.alert_id,
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'short': True
                        },
                        {
                            'title': 'Severity',
                            'value': alert.severity.value,
                            'short': True
                        },
                        {
                            'title': 'Source',
                            'value': alert.source,
                            'short': True
                        }
                    ],
                    'footer': 'Project AEGIS',
                    'ts': int(alert.created_at.timestamp())
                }]
            }

            # Send Slack message (simulation for demo)
            logger.info(f"[Alert System] Slack alert sent: {alert.title}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending Slack alert: {str(e)}")
            return False

    async def _send_telegram_alert(self, alert: AlertMessage, recipient: Dict[str, str]) -> bool:
        """
        Send Telegram alert
        """
        try:
            chat_id = recipient.get('telegram_id')

            if not chat_id:
                # Use default Telegram chat IDs
                chat_ids = self.channel_configs[AlertChannel.TELEGRAM].get('chat_ids', [])
                if not chat_ids:
                    logger.warning("[Alert System] No Telegram chat IDs configured")
                    return False
                chat_id = chat_ids[0]

            # Format Telegram message
            telegram_message = f"""
*{alert.severity.value.upper()} ALERT*

{alert.title}

{alert.message}

*Alert ID:* {alert.alert_id}
*Time:* {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
*Severity:* {alert.severity.value}
*Source:* {alert.source}

---
Project AEGIS Cybercrime Response System
            """.strip()

            # Send Telegram message (simulation for demo)
            logger.info(f"[Alert System] Telegram alert sent to {chat_id}: {alert.title}")

            return True

        except Exception as e:
            logger.error(f"[Alert System] Error sending Telegram alert: {str(e)}")
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """
        Get color for alert severity
        """
        color_map = {
            AlertSeverity.INFO: '#36a64f',      # green
            AlertSeverity.LOW: '#36a64f',       # green
            AlertSeverity.MEDIUM: '#ff9500',    # orange
            AlertSeverity.HIGH: '#ff0000',      # red
            AlertSeverity.CRITICAL: '#8b0000',   # dark red
            AlertSeverity.EMERGENCY: '#8b0000'    # dark red
        }
        return color_map.get(severity, '#36a64f')

    def _format_metadata_html(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata as HTML
        """
        if not metadata:
            return ""

        html = "<div style='background-color: #f9f9f9; padding: 10px; margin: 10px 0;'>"
        html += "<strong>Additional Information:</strong><br>"

        for key, value in metadata.items():
            if key != 'category' and key != 'source':
                html += f"<strong>{key.replace('_', ' ').title()}:</strong> {value}<br>"

        html += "</div>"
        return html

    def _format_metadata_text(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata as plain text
        """
        if not metadata:
            return ""

        text = "\nAdditional Information:\n"

        for key, value in metadata.items():
            if key != 'category' and key != 'source':
                text += f"{key.replace('_', ' ').title()}: {value}\n"

        return text

    async def _store_delivery_record(self, delivery: AlertDelivery) -> None:
        """
        Store alert delivery record
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO alert_deliveries (
                        alert_id, channel, recipient, status, sent_at,
                        delivered_at, error_message, delivery_details
                    ) VALUES (
                        :alert_id, :channel, :recipient, :status, :sent_at,
                        :delivered_at, :error_message, :delivery_details
                    )
                """)

                db.execute(query, {
                    'alert_id': delivery.alert_id,
                    'channel': delivery.channel.value,
                    'recipient': delivery.recipient,
                    'status': delivery.status.value,
                    'sent_at': delivery.sent_at,
                    'delivered_at': delivery.delivered_at,
                    'error_message': delivery.error_message,
                    'delivery_details': json.dumps(delivery.delivery_details)
                })

                db.commit()

        except Exception as e:
            logger.error(f"[Alert System] Error storing delivery record: {str(e)}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str,
                              notes: str = None) -> bool:
        """
        Acknowledge an alert
        """
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"[Alert System] Alert {alert_id} not found in active alerts")
                return False

            alert = self.active_alerts[alert_id]
            alert.metadata['acknowledged_by'] = acknowledged_by
            alert.metadata['acknowledged_at'] = datetime.utcnow().isoformat()
            alert.metadata['acknowledgment_notes'] = notes

            # Update in database
            with SessionLocal() as db:
                query = text("""
                    UPDATE dashboard_alerts
                    SET acknowledged = true,
                        acknowledged_by = :acknowledged_by,
                        acknowledged_at = :acknowledged_at,
                        acknowledgment_notes = :notes
                    WHERE alert_id = :alert_id
                """)

                db.execute(query, {
                    'alert_id': alert_id,
                    'acknowledged_by': acknowledged_by,
                    'acknowledged_at': datetime.utcnow(),
                    'notes': notes
                })

                db.commit()

            logger.info(f"[Alert System] Alert {alert_id} acknowledged by {acknowledged_by}")
            return True

        except Exception as e:
            logger.error(f"[Alert System] Error acknowledging alert {alert_id}: {str(e)}")
            return False

    async def resolve_alert(self, alert_id: str, resolved_by: str,
                           resolution_notes: str = None) -> bool:
        """
        Resolve an alert
        """
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"[Alert System] Alert {alert_id} not found in active alerts")
                return False

            alert = self.active_alerts[alert_id]
            alert.metadata['resolved_by'] = resolved_by
            alert.metadata['resolved_at'] = datetime.utcnow().isoformat()
            alert.metadata['resolution_notes'] = resolution_notes

            # Remove from active alerts
            del self.active_alerts[alert_id]

            # Update in database
            with SessionLocal() as db:
                query = text("""
                    UPDATE dashboard_alerts
                    SET resolved = true,
                        resolved_by = :resolved_by,
                        resolved_at = :resolved_at,
                        resolution_notes = :notes
                    WHERE alert_id = :alert_id
                """)

                db.execute(query, {
                    'alert_id': alert_id,
                    'resolved_by': resolved_by,
                    'resolved_at': datetime.utcnow(),
                    'notes': resolution_notes
                })

                db.commit()

            logger.info(f"[Alert System] Alert {alert_id} resolved by {resolved_by}")
            return True

        except Exception as e:
            logger.error(f"[Alert System] Error resolving alert {alert_id}: {str(e)}")
            return False

    async def _monitor_escalations(self) -> None:
        """
        Monitor alerts for escalation conditions
        """
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute

                for alert_id, alert in list(self.active_alerts.items()):
                    await self._check_escalation_conditions(alert_id, alert)

        except Exception as e:
            logger.error(f"[Alert System] Error in escalation monitor: {str(e)}")

    async def _check_escalation_conditions(self, alert_id: str, alert: AlertMessage) -> None:
        """
        Check if alert should be escalated
        """
        try:
            current_time = datetime.utcnow()
            elapsed_minutes = (current_time - alert.created_at).total_seconds() / 60

            for rule in alert.escalation_rules:
                if not rule.is_active:
                    continue

                should_escalate = False

                if rule.condition == "no_acknowledgment" and alert.severity == rule.threshold:
                    if 'acknowledged_by' not in alert.metadata:
                        should_escalate = True

                elif rule.condition == "time_elapsed" and elapsed_minutes >= rule.threshold:
                    should_escalate = True

                elif rule.condition == "delivery_failures":
                    # Check delivery failures
                    failed_count = 0
                    # This would require checking delivery records
                    if failed_count >= rule.threshold:
                        should_escalate = True

                if should_escalate:
                    await self._execute_escalation(alert_id, alert, rule)

        except Exception as e:
            logger.error(f"[Alert System] Error checking escalation conditions: {str(e)}")

    async def _execute_escalation(self, alert_id: str, alert: AlertMessage, rule: EscalationRule) -> None:
        """
        Execute escalation rule
        """
        try:
            logger.warning(f"[Alert System] Executing escalation {rule.rule_id} for alert {alert_id}")

            if rule.action == "escalate_channel":
                new_channels = rule.parameters.get('add_channels', [])
                alert.channels.extend(new_channels)
                await self._queue_alert_delivery(alert)

            elif rule.action == "add_recipients":
                add_groups = rule.parameters.get('add_groups', [])
                for group in add_groups:
                    if group in self.contact_groups:
                        alert.recipients.extend(self.contact_groups[group])
                await self._queue_alert_delivery(alert)

            elif rule.action == "increase_priority":
                new_priority = min(10, alert.priority + rule.parameters.get('priority_increase', 2))
                alert.priority = new_priority

            # Log escalation
            alert.metadata.setdefault('escalations', []).append({
                'rule_id': rule.rule_id,
                'executed_at': datetime.utcnow().isoformat(),
                'action': rule.action,
                'parameters': rule.parameters
            })

        except Exception as e:
            logger.error(f"[Alert System] Error executing escalation: {str(e)}")

    async def _cleanup_expired_alerts(self) -> None:
        """
        Clean up expired alerts
        """
        try:
            while True:
                await asyncio.sleep(3600)  # Check every hour

                current_time = datetime.utcnow()
                expired_alerts = []

                for alert_id, alert in list(self.active_alerts.items()):
                    if alert.expires_at and alert.expires_at <= current_time:
                        expired_alerts.append(alert_id)

                for alert_id in expired_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.metadata['auto_expired'] = True
                    del self.active_alerts[alert_id]

                    logger.info(f"[Alert System] Auto-expired alert {alert_id}")

        except Exception as e:
            logger.error(f"[Alert System] Error in cleanup task: {str(e)}")

    async def get_alert_statistics(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get alert statistics
        """
        try:
            with SessionLocal() as db:
                # Get overall statistics
                result = db.execute(text("""
                    SELECT
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN acknowledged = true THEN 1 END) as acknowledged_alerts,
                        COUNT(CASE WHEN resolved = true THEN 1 END) as resolved_alerts,
                        AVG(EXTRACT(EPOCH FROM (acknowledged_at - created_at))/60) as avg_acknowledgment_minutes,
                        AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) as avg_resolution_hours
                    FROM dashboard_alerts
                    WHERE created_at >= NOW() - INTERVAL ':days_back days'
                """), {'days_back': days_back}).fetchone()

                # Get statistics by severity
                severity_stats = db.execute(text("""
                    SELECT severity, COUNT(*) as count
                    FROM dashboard_alerts
                    WHERE created_at >= NOW() - INTERVAL ':days_back days'
                    GROUP BY severity
                    ORDER BY count DESC
                """), {'days_back': days_back}).fetchall()

                # Get statistics by channel
                channel_stats = db.execute(text("""
                    SELECT channel, COUNT(*) as count,
                           COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered
                    FROM alert_deliveries
                    WHERE sent_at >= NOW() - INTERVAL ':days_back days'
                    GROUP BY channel
                    ORDER BY count DESC
                """), {'days_back': days_back}).fetchall()

                return {
                    'total_alerts': result.total_alerts if result else 0,
                    'acknowledged_alerts': result.acknowledged_alerts if result else 0,
                    'resolved_alerts': result.resolved_alerts if result else 0,
                    'avg_acknowledgment_minutes': float(result.avg_acknowledgment_minutes) if result and result.avg_acknowledgment_minutes else 0,
                    'avg_resolution_hours': float(result.avg_resolution_hours) if result and result.avg_resolution_hours else 0,
                    'severity_distribution': {row.severity: row.count for row in severity_stats},
                    'channel_performance': {
                        row.channel: {
                            'sent': row.count,
                            'delivered': row.delivered if row.delivered else 0,
                            'delivery_rate': (row.delivered / row.count * 100) if row.count > 0 else 0
                        } for row in channel_stats
                    },
                    'active_alerts': len(self.active_alerts),
                    'delivery_stats': self.delivery_stats,
                    'period_days': days_back
                }

        except Exception as e:
            logger.error(f"[Alert System] Error getting alert statistics: {str(e)}")
            return {}

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get alert system status
        """
        try:
            return {
                'active_alerts': len(self.active_alerts),
                'delivery_queue_size': self.delivery_queue.qsize(),
                'channels_enabled': {
                    channel.value: config.get('enabled', False)
                    for channel, config in self.channel_configs.items()
                },
                'contact_groups': len(self.contact_groups),
                'escalation_rules': len(self.escalation_rules),
                'delivery_statistics': self.delivery_stats,
                'system_uptime': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[Alert System] Error getting system status: {str(e)}")
            return {'error': str(e)}

# Global alert system instance
multi_channel_alerts = MultiChannelAlertSystem()