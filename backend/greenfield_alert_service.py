"""
Project AEGIS Greenfield Alert Service
Handles SMS and email alerts with Twilio and SendGrid integration
Mock implementation for MVP with console logging fallback
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)

class GreenfieldAlertService:
    """
    Alert service for Project AEGIS greenfield implementation.
    Integrates with Twilio (SMS) and SendGrid (Email).
    Mock implementation logs to console when credentials missing.
    """

    def __init__(self):
        # Twilio configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.lea_phone_numbers = os.getenv("LEA_PHONE_NUMBERS", "+919876543210,+919812345678").split(",")

        # SendGrid configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@aegis.gov.in")
        self.lea_emails = os.getenv("LEA_EMAILS", "lea@example.com,officer@example.com").split(",")

        # Alert configuration
        self.confidence_threshold = 0.8

        logger.info("[ALERT SERVICE] Initialized")
        logger.info(f"[ALERT SERVICE] Twilio configured: {'Yes' if self.twilio_account_sid else 'No (Mock mode)'}")
        logger.info(f"[ALERT SERVICE] SendGrid configured: {'Yes' if self.sendgrid_api_key else 'No (Mock mode)'}")

    async def send_sms_alert(
        self,
        hotspot_id: str,
        location_name: str,
        fraud_type: str,
        amount: float,
        confidence: float
    ) -> Optional[Dict]:
        """
        Send SMS alert via Twilio. Falls back to console logging for MVP.

        Message format: 🚨 AEGIS Alert #<hotspot_id>: High-risk withdrawal predicted at <location_name> in <time_left> mins. Amount: ₹<amount> | Confidence: <confidence>%
        """
        try:
            # Calculate time left (45 minutes from now)
            time_left_minutes = 45

            # Format message as per specification
            message = (
                f"🚨 AEGIS Alert #{hotspot_id[:8]}: "
                f"High-risk withdrawal predicted at {location_name} in {time_left_minutes} mins. "
                f"Amount: ₹{amount:,.0f} | Confidence: {confidence:.0%} | Type: {fraud_type}"
            )

            if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number:
                # Real Twilio integration
                result = await self._send_twilio_sms(message)
                logger.info(f"[ALERT SERVICE] Real SMS sent to {len(self.lea_phone_numbers)} numbers")
            else:
                # Mock implementation - log to console
                result = {
                    "success": True,
                    "mode": "mock",
                    "message": message,
                    "sent_to": self.lea_phone_numbers,
                    "logged_at": datetime.utcnow().isoformat()
                }

                # Console logging for MVP
                print("\n" + "="*80)
                print("🚨 AEGIS ALERT - SMS (MOCK MODE)")
                print("="*80)
                print(f"To: {', '.join(self.lea_phone_numbers)}")
                print(f"Message: {message}")
                print(f"Hotspot ID: {hotspot_id}")
                print(f"Logged at: {datetime.utcnow().isoformat()}")
                print("="*80 + "\n")

                logger.info(f"[ALERT SERVICE] Mock SMS logged: {message}")

            return result

        except Exception as e:
            logger.error(f"[ALERT SERVICE] SMS alert failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def send_email_alert(
        self,
        hotspot_id: str,
        location_name: str,
        fraud_type: str,
        amount: float,
        confidence: float
    ) -> Optional[Dict]:
        """
        Send email alert via SendGrid. Falls back to console logging for MVP.
        """
        try:
            # Calculate time left
            time_left_minutes = 45

            # Prepare HTML email content
            subject = f"🚨 AEGIS Alert: High-Risk Withdrawal Predicted at {location_name}"

            html_content = self._generate_email_html(
                hotspot_id, location_name, fraud_type, amount, confidence, time_left_minutes
            )

            if self.sendgrid_api_key:
                # Real SendGrid integration
                result = await self._send_sendgrid_email(subject, html_content)
                logger.info(f"[ALERT SERVICE] Real email sent to {len(self.lea_emails)} addresses")
            else:
                # Mock implementation - log to console
                result = {
                    "success": True,
                    "mode": "mock",
                    "subject": subject,
                    "sent_to": self.lea_emails,
                    "logged_at": datetime.utcnow().isoformat()
                }

                # Console logging for MVP
                print("\n" + "="*80)
                print("🚨 AEGIS ALERT - EMAIL (MOCK MODE)")
                print("="*80)
                print(f"To: {', '.join(self.lea_emails)}")
                print(f"Subject: {subject}")
                print(f"Hotspot ID: {hotspot_id}")
                print(f"Logged at: {datetime.utcnow().isoformat()}")
                print("\nEmail Content Preview:")
                print("-"*40)
                print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
                print("="*80 + "\n")

                logger.info(f"[ALERT SERVICE] Mock email logged: {subject}")

            return result

        except Exception as e:
            logger.error(f"[ALERT SERVICE] Email alert failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _send_twilio_sms(self, message: str) -> Dict:
        """
        Send SMS via Twilio REST API.
        """
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"

            auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)

            results = []
            for phone_number in self.lea_phone_numbers:
                data = {
                    "From": self.twilio_phone_number,
                    "To": phone_number,
                    "Body": message
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data, auth=auth) as response:
                        if response.status == 201:
                            result = await response.json()
                            results.append({"phone": phone_number, "success": True, "sid": result.get("sid")})
                        else:
                            error_text = await response.text()
                            results.append({"phone": phone_number, "success": False, "error": error_text})

            return {
                "success": all(r.get("success", False) for r in results),
                "results": results,
                "mode": "twilio"
            }

        except Exception as e:
            logger.error(f"[ALERT SERVICE] Twilio SMS error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _send_sendgrid_email(self, subject: str, html_content: str) -> Dict:
        """
        Send email via SendGrid API.
        """
        try:
            url = "https://api.sendgrid.com/v3/mail/send"

            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }

            # Prepare email data
            personalizations = []
            for email in self.lea_emails:
                personalizations.append({
                    "to": [{"email": email}],
                    "subject": subject
                })

            email_data = {
                "personalizations": personalizations,
                "from": {"email": self.from_email, "name": "Project AEGIS"},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=email_data) as response:
                    if response.status == 202:
                        return {"success": True, "mode": "sendgrid", "message_id": response.headers.get("X-Message-Id")}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": error_text, "status": response.status}

        except Exception as e:
            logger.error(f"[ALERT SERVICE] SendGrid email error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _generate_email_html(
        self,
        hotspot_id: str,
        location_name: str,
        fraud_type: str,
        amount: float,
        confidence: float,
        time_left_minutes: int
    ) -> str:
        """
        Generate HTML email content for alert.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AEGIS Alert</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #dc2626;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9fafb;
                    padding: 30px;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                    border-radius: 0 0 8px 8px;
                }}
                .alert-details {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                    border-left: 4px solid #dc2626;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 8px 0;
                    border-bottom: 1px solid #f3f4f6;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #6b7280;
                }}
                .detail-value {{
                    font-weight: bold;
                    color: #111827;
                }}
                .confidence {{
                    color: #dc2626;
                    font-size: 1.2em;
                }}
                .action-required {{
                    background-color: #fef2f2;
                    border: 1px solid #fecaca;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 PROJECT AEGIS ALERT</h1>
                <p>High-Risk Cash Withdrawal Prediction</p>
            </div>

            <div class="content">
                <div class="alert-details">
                    <div class="detail-row">
                        <span class="detail-label">Alert ID:</span>
                        <span class="detail-value">#{hotspot_id[:8].upper()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Predicted Location:</span>
                        <span class="detail-value">{location_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Scam Type:</span>
                        <span class="detail-value">{fraud_type.replace('_', ' ')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Amount:</span>
                        <span class="detail-value">₹{amount:,.0f}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time Remaining:</span>
                        <span class="detail-value">{time_left_minutes} minutes</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value confidence">{confidence:.0%}</span>
                    </div>
                </div>

                <div class="action-required">
                    <h3>⚡ IMMEDIATE ACTION REQUIRED</h3>
                    <p>High-confidence prediction indicates elevated risk of cash withdrawal at the specified location. Time-sensitive intervention recommended.</p>
                </div>

                <div class="alert-details">
                    <h4>Recommended Actions:</h4>
                    <ul>
                        <li>Deploy personnel to monitor the location</li>
                        <li>Coordinate with local banking authorities</li>
                        <li>Consider activating digital cordon if available</li>
                        <li>Document observations for system learning</li>
                    </ul>
                </div>
            </div>

            <div class="footer">
                <p><strong>Project AEGIS</strong> - Anticipatory Engine for Geolocated Intervention against Scams</p>
                <p>This alert was generated automatically at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                <p><em>This is a high-priority law enforcement alert. Immediate attention required.</em></p>
            </div>
        </body>
        </html>
        """

# Singleton instance for the application
greenfield_alert_service = GreenfieldAlertService()