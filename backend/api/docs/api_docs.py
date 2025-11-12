"""
Comprehensive API Documentation for Project AEGIS
OpenAPI/Swagger definitions and documentation utilities
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Pydantic models for API documentation
class ContactInfo(BaseModel):
    name: str = Field(..., description="Name of the contact")
    email: str = Field(..., description="Email of the contact")
    phone: str = Field(None, description="Phone number of the contact")
    department: str = Field(None, description="Department of the contact")

class ScammerDetails(BaseModel):
    name: Optional[str] = Field(None, description="Scammer's name (if known)")
    phone: Optional[str] = Field(None, description="Scammer's phone number")
    email: Optional[str] = Field(None, description="Scammer's email")
    bank_account: Optional[str] = Field(None, description="Scammer's bank account")
    upi_id: Optional[str] = Field(None, description="Scammer's UPI ID")
    platform: Optional[str] = Field(None, description="Platform used by scammer")
    social_media: Optional[str] = Field(None, description="Social media handle")
    ip_address: Optional[str] = Field(None, description="IP address")

class TransactionDetails(BaseModel):
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_number: Optional[str] = Field(None, description="Account number (masked)")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    transaction_amount: Optional[float] = Field(None, description="Transaction amount")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference number")
    payment_method: Optional[str] = Field(None, description="Payment method (UPI, NEFT, RTGS, etc.)")

class ComplaintRequest(BaseModel):
    """Complaint submission request model"""
    complaint_type: str = Field(..., description="Type of cybercrime", example="online_scam")
    amount: float = Field(..., gt=0, description="Amount involved in the scam (in rupees)", example=50000.0)
    victim_location: str = Field(..., description="Victim's location", example="Mumbai, Maharashtra")
    victim_contact: Optional[ContactInfo] = Field(None, description="Victim's contact information (encrypted)")
    scammer_details: Optional[ScammerDetails] = Field(None, description="Information about the scammer")
    transaction_details: Optional[TransactionDetails] = Field(None, description="Transaction details")
    scam_date: Optional[datetime] = Field(None, description="Date of scam")
    platform_details: Optional[Dict[str, Any]] = Field(None, description="Platform where scam occurred")
    victim_statement: Optional[str] = Field(None, description="Detailed statement from victim")
    evidence_attachments: Optional[List[str]] = Field(None, description="List of evidence file URLs")
    priority: Optional[str] = Field("medium", description="Complaint priority", enum=["low", "medium", "high", "critical"])

class PredictionResult(BaseModel):
    """AI prediction result model"""
    location_id: int = Field(..., description="Location ID")
    location_name: str = Field(..., description="Location name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    confidence_score: float = Field(..., description="Confidence score (0-1)", ge=0, le=1)
    risk_level: str = Field(..., description="Risk level", enum=["low", "medium", "high", "critical"])
    time_window_start: datetime = Field(..., description="Start time window for prediction")
    time_window_end: datetime = Field(..., description="End time window for prediction")
    ai_insights: Optional[Dict[str, Any]] = Field(None, description="AI model insights")
    probability_score: Optional[float] = Field(None, description="Probability of cash-out", ge=0, le=1)
    distance_km: Optional[float] = Field(None, description="Distance from victim location in km")

class CordonRequest(BaseModel):
    """Digital cordon activation request"""
    target_type: str = Field(..., description="Type of target", example="account")
    target_value: str = Field(..., description="Target value", example="123456789012")
    cordon_type: str = Field(..., description="Type of cordon", example="account_block")
    priority: str = Field("medium", description="Priority level", enum=["low", "medium", "high", "critical", "emergency"])
    duration_hours: int = Field(24, description="Duration in hours", ge=1, le=168)
    evidence: Optional[Dict[str, Any]] = Field(None, description="Supporting evidence")
    geographic_area: Optional[Dict[str, Any]] = Field(None, description="Geographic area for cordon")
    transaction_limits: Optional[Dict[str, float]] = Field(None, description="Transaction limits")

class AlertRequest(BaseModel):
    """Alert creation request"""
    title: str = Field(..., description="Alert title", example="High-Risk Prediction Confirmed")
    message: str = Field(..., description="Alert message", description="AI model predicts high probability of cash-out at location within 30 minutes")
    severity: str = Field(..., description="Alert severity", enum=["info", "low", "medium", "high", "critical", "emergency"])
    target_groups: Optional[List[str]] = Field(None, description="Target groups to notify")
    recipients: Optional[List[Dict[str, str]]] = Field(None, description="Specific recipients")
    channels: Optional[List[str]] = Field(None, description="Alert channels")
    auto_resolve_after: Optional[int] = Field(None, description="Auto-resolve after X hours")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SystemStatus(BaseModel):
    """System health status"""
    status: str = Field(..., description="Overall system status", enum=["healthy", "degraded", "unhealthy"])
    timestamp: datetime = Field(..., description="Status timestamp")
    version: str = Field(..., description="System version")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component statuses")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")
    active_connections: int = Field(..., description="Active WebSocket connections")

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID")

# OpenAPI Documentation Configuration
API_TITLE = "Project AEGIS API"
API_DESCRIPTION = """
## Project AEGIS - Advanced Cybercrime Response System

**Anticipatory Engine for Geolocated Intervention against Scams**

Project AEGIS transforms India's cybercrime response from reactive reporting to anticipatory disruption.
Our AI-powered system predicts high-risk cash withdrawal locations within 90 minutes of scam complaints.

### Key Features

- **AI-Powered Predictions**: Advanced machine learning models predict likely cash-out locations
- **Real-Time Processing**: Sub-second complaint processing and prediction generation
- **Digital Cordon System**: Integration with NPCI for payment interception
- **Multi-Channel Alerts**: Email, SMS, WhatsApp, Push notifications
- **Geospatial Analysis**: Real-time hotspot detection and mapping
- **Privacy-First Design**: Zero PII storage with DPDP Act 2023 compliance

### API Overview

This API provides programmatic access to all Project AEGIS capabilities:

1. **Complaint Management**: File and track cybercrime complaints
2. **AI Predictions**: Get AI-powered location predictions
3. **Digital Cordons**: Create and manage payment interception cordons
4. **Real-Time Alerts**: Send and manage multi-channel alerts
5. **Analytics**: Access comprehensive system analytics
6. **User Management**: Manage users and permissions

### Authentication

The API uses JWT (JSON Web Token) authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Rate Limiting

API endpoints are rate-limited to ensure fair usage:
- **Citizen endpoints**: 100 requests per hour
- **LEA endpoints**: 500 requests per hour
- **Analytics endpoints**: 1000 requests per hour
- **Admin endpoints**: 2000 requests per hour

### Data Privacy

- All personal data is encrypted at rest
- No PII (Personally Identifiable Information) is stored permanently
- Compliance with DPDP Act 2023
- Data retention policies enforced automatically

### Getting Started

1. **Register for API access**: Contact the AEGIS team
2. **Obtain API credentials**: Receive your API key and secret
3. **Test authentication**: Verify your credentials work
4. **Integrate**: Use the API in your application

For more detailed information, see our [API Reference Guide](/docs/guide) or contact the development team.
"""

API_VERSION = "2.0.0"
API_TERMS_OF_SERVICE = """
## Terms of Service

By using this API, you agree to:

1. Use the API only for lawful purposes
2. Protect your API credentials
3. Comply with applicable laws and regulations
4. Respect rate limits and fair usage policies
5. Report any security vulnerabilities
6. Not attempt to reverse engineer the system

### Data Usage

All data provided through this API must be:
- Accurate and up-to-date
- Obtained legally and ethically
- Used only for stated purposes
- Handled in compliance with applicable laws

### Liability

Project AEGIS and its partners are not liable for:
- Inaccurate information provided by users
- Consequences of decisions based on API predictions
- System downtime or maintenance issues
- Third-party service disruptions

### Changes

We reserve the right to:
- Update API versions and features
- Modify rate limits and policies
- Discontinue access for violations
- Update these terms of service

For the full terms, please visit our website.
"""

API_CONTACT = {
    "name": "Project AEGIS Development Team",
    "email": "api-support@aegis.gov.in",
    "url": "https://aegis.gov.in/api-support",
    "license": {
        "name": "Government of India",
        "url": "https://gov.in/"
    }
}

def create_custom_openapi(app: FastAPI):
    """Create custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
        servers=[
            {
                "url": "https://api.aegis.gov.in",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.aegis.gov.in",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        contact={
            "name": API_CONTACT["name"],
            "email": API_CONTACT["email"],
            "url": API_CONTACT["url"]
        },
        license_info={
            "name": API_CONTACT["license"]["name"],
            "url": API_CONTACT["license"]["url"]
        },
        info={
            "termsOfService": API_TERMS_OF_SERVICE,
            "x-logo": {
                "url": "https://aegis.gov.in/logo.png",
                "backgroundColor": "#ffffff",
                "altText": "Project AEGIS Logo"
            },
            "x-version": "2.0.0",
            "x-release-date": "2024-11-12",
            "x-apidocs": "https://aegis.gov.in/docs",
            "x-github": "https://github.com/aegis-project/api",
            "x-twitter": "https://twitter.com/project_aegis",
            "x-status": "production"
        },
        tags=[
            {
                "name": "Complaints",
                "description": "Cybercrime complaint management"
            },
            {
                "name": "Predictions",
                "description": "AI-powered location predictions"
            },
            {
                "name": "Digital Cordons",
                "description": "Payment interception and account blocking"
            },
            {
                "name": "Alerts",
                "description": "Multi-channel alert system"
            },
            {
                "name": "Analytics",
                "description": "System analytics and reporting"
            },
            {
                "name": "Users",
                "description": "User management and authentication"
            },
            {
                "name": "WebSocket",
                "description": "Real-time communication"
            },
            {
                "name": "System",
                "description": "System health and monitoring"
            }
        ],
        components={
            "schemas": {
                "ComplaintRequest": ComplaintRequest.__name__,
                "PredictionResult": PredictionResult.__name__,
                "CordonRequest": CordonRequest.__name__,
                "AlertRequest": AlertRequest.__name__,
                "SystemStatus": SystemStatus.__name__,
                "APIResponse": APIResponse.__name__,
                "ErrorResponse": ErrorResponse.__name__
            },
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/APIResponse"}
                        }
                    }
                },
                "201": {
                    "description": "Resource created successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/APIResponse"}
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                },
                "403": {
                    "description": "Forbidden",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                },
                "404": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                },
                "429": {
                    "description": "Rate limit exceeded",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/schemas/ErrorResponse"}
                        }
                    }
                }
            }
        }
    )

    # Add custom documentation examples
    openapi_schema["paths"]["/api/v1/complaints"]["post"]["responses"]["201"]["content"]["application/json"]["example"] = {
        "success": True,
        "message": "Complaint submitted successfully",
        "data": {
            "complaint_id": "comp_20241112_123456_7890",
            "status": "pending",
            "submitted_at": "2024-11-12T10:30:00Z"
        }
    }

    openapi_schema["paths"]["/api/v2/complaints/enhanced"]["post"]["responses"]["200"]["content"]["application/json"]["example"] = {
        "success": True,
        "message": "Enhanced complaint processed successfully",
        "data": {
            "prediction_id": "pred_20241112_123456_7890",
            "predictions": [
                {
                    "location_id": 123,
                    "location_name": "Mumbai Central ATM",
                    "latitude": 19.0760,
                    "longitude": 72.8777,
                    "confidence_score": 0.92,
                    "risk_level": "high",
                    "time_window_start": "2024-11-12T10:45:00Z",
                    "time_window_end": "2024-11-12T12:15:00Z",
                    "ai_insights": {
                        "behavioral_patterns": ["high_frequency_transactions", "cross-platform"],
                        "risk_factors": ["large_amount", "recent_complaints"]
                    }
                }
            ],
            "processing_time_ms": 1250.5,
            "models_used": ["behavioral_digital_twin", "risk_scoring_engine", "federated_causal_graph"]
        }
    }

    return openapi_schema

def setup_docs_app() -> FastAPI:
    """Create a standalone FastAPI app for documentation"""
    app = FastAPI(
        title="Project AEGIS API Documentation",
        description="API Documentation and Testing Interface",
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom OpenAPI schema
    app.openapi_schema = create_custom_openapi(app)

    @app.get("/", tags=["Documentation"])
    async def root():
        return {
            "message": "Project AEGIS API Documentation",
            "version": API_VERSION,
            "status": "operational",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }

    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "aegis-api-docs",
            "timestamp": datetime.utcnow().isoformat(),
            "version": API_VERSION
        }

    @app.get("/info", tags=["System"])
    async def api_info():
        return {
            "title": API_TITLE,
            "version": API_VERSION,
            "description": API_DESCRIPTION,
            "contact": API_CONTACT,
            "terms_of_service": API_TERMS_OF_SERVICE,
            "features": [
                "Complaint Management",
                "AI Predictions",
                "Digital Cordons",
                "Real-Time Alerts",
                "Analytics Dashboard",
                "WebSocket Communication",
                "Role-Based Access Control",
                "Audit Logging",
                "Rate Limiting",
                "Data Encryption",
                "DPDP Compliance"
            ],
            "statistics": {
                "api_endpoints": 45,
                "models_supported": 12,
                "ai_algorithms": [
                    "CST-Transformer",
                    "Federated Causal Graph",
                    "Behavioral Digital Twin",
                    "Risk Scoring Engine"
                ],
                "integration_partners": [
                    "NCRP",
                    "CFCFRMS",
                    "I4C",
                    "NPCI"
                ]
            }
        }

    return app

def generate_postman_collection() -> Dict[str, Any]:
    """Generate Postman collection for API testing"""
    return {
        "info": {
            "_postman_id": "aegis-api-collection",
            "name": "Project AEGIS API v2.0",
            "description": "Comprehensive API collection for Project AEGIS cybercrime response system",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "System Health",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        }
                    ],
                    "url": "{{baseUrl}}/health"
                }
            },
            {
                "name": "Submit Complaint",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        },
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{\n  "complaint_type": "online_sam",\n  "amount": 50000,\n  "victim_location": "Mumbai, Maharashtra",\n  "victim_contact": {\n    "name": "John Doe",\n    "email": "john@example.com",\n    "phone": "+919876543210"\n  },\n  "scammer_details": {\n    "phone": "+918765432109",\n    "upi_id": "scammer@paytm"\n  },\n  "transaction_details": {\n    "bank_name": "State Bank of India",\n    "amount": 50000,\n    "date": "2024-11-12T10:30:00Z"\n  }\n}'
                    },
                    "url": "{{baseUrl}}/api/v1/complaints"
                }
            },
            {
                "name": "Submit Enhanced Complaint",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        },
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{\n  "complaint_type": "online_sam",\n  "amount": 50000,\n  "victim_location": "Mumbai, Maharashtra",\n  "scammer_details": {\n    "name": "Unknown",\n    "phone": "+918765432109",\n    "upi_id": "scammer@paytm"\n  },\n  "metadata": {\n    "source": "mobile_app",\n    "device_id": "device_12345"\n  }\n}'
                    },
                    "url": "{{baseUrl}}/api/v2/complaints/enhanced"
                }
            },
            {
                "name": "Create Digital Cordon",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        },
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{\n  "target_type": "account",\n  "target_value": "123456789012",\n  "cordon_type": "account_block",\n  "priority": "high",\n  "duration_hours": 24,\n  "evidence": {\n    "complaint_id": "comp_123",\n    "risk_score": 0.95\n  }\n}'
                    },
                    "url": "{{baseUrl}}/api/v2/cordons/enhanced"
                }
            },
            {
                "name": "Create Alert",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        },
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{\n  "title": "High-Risk Prediction Confirmed",\n  "message": "AI model predicts high probability of cash-out at Mumbai Central within 30 minutes",\n  "severity": "critical",\n  "target_groups": ["cybercrime_team", "banking_authorities"]\n}'
                    },
                    "url": "{{baseUrl}}/api/v1/alerts"
                }
            },
            {
                "name": "Get Analytics Data",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer <JWT_TOKEN>"
                        }
                    ],
                    "url": "{{baseUrl}}/api/v2/analytics/realtime"
                }
            },
            {
                "name": "WebSocket Connection",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Connection",
                            "value": "Upgrade"
                        },
                        {
                            "key": "Upgrade",
                            "value": "websocket"
                        },
                        {
                            "key": "Sec-WebSocket-Key",
                            "value": "websocket_key"
                        },
                        {
                            "key": "Sec-WebSocket-Version",
                            "value": "13"
                        }
                    ],
                    "url": "{{baseUrl}}/ws"
                }
            }
        ],
        "variable": [
            {
                "key": "baseUrl",
                "value": "https://api.aegis.gov.in",
                "description": "API base URL",
                "disabled": False
            }
        ]
    }

# Export documentation utilities
__all__ = [
    "create_custom_openapi",
    "setup_docs_app",
    "generate_postman_collection",
    "API_TITLE",
    "API_VERSION",
    "API_DESCRIPTION",
    "API_CONTACT"
]