import os
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.twilio_config = {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER')
        }
        self.sendgrid_config = {
            'api_key': os.getenv('SENDGRID_API_KEY'),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@aegis.gov.in')
        }

    def send_high_priority_alert(self, hotspot) -> bool:
        """
        Send high-priority alert for hotspot prediction
        """
        try:
            # Extract coordinates for alert message
            alert_data = {
                'hotspot_id': str(hotspot.id),
                'location_name': hotspot.location_name,
                'confidence': hotspot.confidence,
                'time_window': hotspot.time_window_mins,
                'predicted_at': hotspot.predicted_at
            }

            # Send SMS alert (mock implementation)
            sms_sent = self._send_sms_alert(alert_data)

            # Send email alert (mock implementation)
            email_sent = self._send_email_alert(alert_data)

            # Log the alert for audit
            self._log_alert(alert_data, sms_sent, email_sent)

            return sms_sent or email_sent

        except Exception as e:
            logger.error(f"Alert service error: {str(e)}")
            return False

    def _send_sms_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send SMS alert via Twilio (mock implementation for MVP)
        """
        try:
            # Mock Twilio implementation - log instead of sending
            message = (
                f"🚨 AEGIS ALERT: High-risk scam cash-out predicted at {alert_data['location_name']}. "
                f"Confidence: {alert_data['confidence']:.0%}. "
                f"Time window: {alert_data['time_window']} minutes. "
                f"Hotspot ID: {alert_data['hotspot_id'][:8]}"
            )

            # Log message (in production, use actual Twilio client)
            logger.info(f"MOCK SMS ALERT: {message}")
            print(f"[SMS MOCK] {message}")

            return True

        except Exception as e:
            logger.error(f"SMS alert failed: {str(e)}")
            return False

    def _send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send email alert via SendGrid (mock implementation for MVP)
        """
        try:
            # Mock SendGrid implementation - log instead of sending
            subject = f"AEGIS High-Priority Alert: {alert_data['location_name']}"

            html_content = f"""
            <html>
            <body>
                <h2>🚨 Project AEGIS - High-Priority Alert</h2>
                <p><strong>Location:</strong> {alert_data['location_name']}</p>
                <p><strong>Confidence:</strong> {alert_data['confidence']:.0%}</p>
                <p><strong>Time Window:</strong> {alert_data['time_window']} minutes</p>
                <p><strong>Predicted:</strong> {alert_data['predicted_at'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Hotspot ID:</strong> {alert_data['hotspot_id']}</p>
                <hr>
                <p><em>This is an automated alert from Project AEGIS. Please check the LEA dashboard for details.</em></p>
            </body>
            </html>
            """

            # Log email content (in production, use actual SendGrid client)
            logger.info(f"MOCK EMAIL ALERT: {subject}")
            print(f"[EMAIL MOCK] Subject: {subject}")
            print(f"[EMAIL MOCK] Content: {html_content[:200]}...")

            return True

        except Exception as e:
            logger.error(f"Email alert failed: {str(e)}")
            return False

    def _log_alert(self, alert_data: Dict[str, Any], sms_sent: bool, email_sent: bool):
        """
        Log alert for audit trail
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'hotspot_id': alert_data['hotspot_id'],
            'location_name': alert_data['location_name'],
            'confidence': alert_data['confidence'],
            'sms_sent': sms_sent,
            'email_sent': email_sent,
            'alert_type': 'high_priority'
        }

        logger.info(f"ALERT LOGGED: {log_entry}")
        print(f"[ALERT LOG] {log_entry}")