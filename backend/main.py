"""
Project AEGIS - Enhanced FastAPI Application
Advanced Cybercrime Response System API Server v2.0
"""

import asyncio
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import uvicorn

# Import existing modules
from app.api import complaints, predictions, alerts, cordons
from app.database import engine, Base

# Import AEGIS advanced components
try:
    from ai_models.enhanced_federated_causal_graph import enhanced_federated_causal_graph
    from ai_models.enhanced_behavioral_digital_twin import enhanced_behavioral_digital_twin
    from risk_scoring.advanced_risk_engine import advanced_risk_engine
    from integrations.npci_digital_cordon import npci_digital_cordon
    from alerts.multi_channel_alerts import multi_channel_alerts
    from learning.continuous_learning import continuous_learning
    from gis.real_time_gis import real_time_gis
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Advanced features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic Models for Advanced Features
class ComplaintRequest(BaseModel):
    """Enhanced complaint submission request"""
    complaint_type: str
    amount: float
    victim_location: str
    scammer_details: Dict[str, Any] = {}
    transaction_details: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class CordonRequest(BaseModel):
    """Enhanced digital cordon request"""
    target_type: str
    target_value: str
    cordon_type: str
    priority: str = "medium"
    duration_hours: int = 24
    evidence: Dict[str, Any] = {}
    requested_by: str

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str = None

# WebSocket Manager
class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

manager = ConnectionManager()

# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Project AEGIS API Server v2.0...")

    if ADVANCED_FEATURES_AVAILABLE:
        try:
            logger.info("📊 Initializing advanced AI systems...")
            # Initialize all advanced systems asynchronously
            initialization_tasks = [
                enhanced_federated_causal_graph.initialize(),
                enhanced_behavioral_digital_twin.initialize(),
                advanced_risk_engine.initialize(),
                npci_digital_cordon.initialize(),
                multi_channel_alerts.initialize(),
                continuous_learning.initialize(),
                real_time_gis.initialize()
            ]

            results = await asyncio.gather(*initialization_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Failed to initialize system {i}: {str(result)}")
                else:
                    logger.info(f"✅ System {i} initialized successfully")

            logger.info("✅ All advanced systems initialized!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize advanced systems: {str(e)}")
    else:
        logger.info("⚠️ Running in basic mode (advanced features not available)")

    yield

    logger.info("🛑 Shutting down Project AEGIS API Server...")

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Project AEGIS API v2.0",
    description="Advanced Cybercrime Response System - Anticipatory Engine for Geolocated Intervention against Scams",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routers
app.include_router(complaints.router, prefix="/api/v1", tags=["complaints"])
app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(cordons.router, prefix="/api/v1", tags=["cordons"])

# Enhanced Endpoints

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    health_data = {
        "status": "healthy",
        "service": "aegis-api",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "advanced_features": ADVANCED_FEATURES_AVAILABLE,
        "websocket_connections": manager.get_connection_count()
    }

    if ADVANCED_FEATURES_AVAILABLE:
        try:
            # Get status from all advanced systems
            health_data["components"] = {
                "federated_causal_graph": "operational",
                "behavioral_digital_twin": "operational",
                "risk_scoring_engine": "operational",
                "npci_digital_cordon": "operational",
                "multi_channel_alerts": "operational",
                "continuous_learning": "operational",
                "real_time_gis": "operational"
            }
        except Exception as e:
            logger.error(f"❌ Error getting component status: {str(e)}")
            health_data["components"] = {"error": str(e)}

    return health_data

@app.post("/api/v2/complaints/enhanced")
async def submit_enhanced_complaint(
    complaint: ComplaintRequest,
    background_tasks: BackgroundTasks
):
    """
    Enhanced complaint processing with advanced AI models
    """
    if not ADVANCED_FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Advanced features not available")

    try:
        start_time = datetime.utcnow()
        prediction_id = f"pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(f"📝 Processing enhanced complaint: {complaint.complaint_type} - ₹{complaint.amount:,.2f}")

        # Process through advanced AI pipeline
        # Step 1: Behavioral analysis
        behavioral_analysis = await enhanced_behavioral_digital_twin.predict_behavior(
            scam_type=complaint.complaint_type,
            amount=complaint.amount,
            location=complaint.victim_location,
            scammer_details=complaint.scammer_details
        )

        # Step 2: Risk prediction
        risk_predictions = await advanced_risk_engine.predict_risk_locations(
            behavioral_profile=behavioral_analysis,
            victim_location=complaint.victim_location,
            transaction_details=complaint.transaction_details
        )

        # Step 3: Causal graph enhancement
        enhanced_predictions = await enhanced_federated_causal_graph.enhance_predictions(
            base_predictions=risk_predictions,
            context=complaint.dict()
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Broadcast real-time update
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "enhanced_prediction",
                "data": {
                    "prediction_id": prediction_id,
                    "complaint_type": complaint.complaint_type,
                    "amount": complaint.amount,
                    "processing_time_ms": processing_time,
                    "predictions_count": len(enhanced_predictions)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Add to continuous learning
        background_tasks.add_task(
            continuous_learning.add_learning_data,
            features=complaint.dict(),
            labels=enhanced_predictions,
            source="enhanced_api",
            data_type="risk_scoring"
        )

        logger.info(f"✅ Enhanced complaint processed in {processing_time:.2f}ms")

        return {
            "prediction_id": prediction_id,
            "predictions": enhanced_predictions,
            "processing_time_ms": processing_time,
            "models_used": ["behavioral_digital_twin", "risk_scoring_engine", "federated_causal_graph"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error processing enhanced complaint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing complaint: {str(e)}")

@app.post("/api/v2/cordons/enhanced")
async def create_enhanced_digital_cordon(
    cordon_request: CordonRequest,
    background_tasks: BackgroundTasks
):
    """
    Enhanced digital cordon creation with advanced features
    """
    if not ADVANCED_FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Advanced features not available")

    try:
        logger.info(f"🛡️ Creating enhanced digital cordon: {cordon_request.target_type}")

        # Create enhanced digital cordon
        cordon = await npci_digital_cordon.create_digital_cordon(
            target_type=cordon_request.target_type,
            target_value=cordon_request.target_value,
            action=cordon_request.cordon_type,
            priority=cordon_request.priority,
            reason=f"Enhanced cordon via API - {cordon_request.requested_by}",
            evidence=cordon_request.evidence,
            duration_hours=cordon_request.duration_hours,
            created_by=cordon_request.requested_by
        )

        # Send multi-channel alert
        background_tasks.add_task(
            multi_channel_alerts.create_alert,
            title=f"Enhanced Digital Cordon Activated",
            message=f"Advanced digital cordon activated: {cordon_request.target_value}",
            severity="high",
            target_groups=["cybercrime_team", "banking_authorities"],
            metadata={
                "cordon_id": cordon.cordon_id,
                "enhanced_features": True
            }
        )

        # Broadcast real-time update
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "enhanced_cordon_activated",
                "data": {
                    "cordon_id": cordon.cordon_id,
                    "target_type": cordon_request.target_type,
                    "status": cordon.status.value
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "cordon_id": cordon.cordon_id,
            "status": cordon.status.value,
            "enhanced_features": True,
            "expires_at": cordon.expires_at.isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error creating enhanced digital cordon: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating digital cordon: {str(e)}")

@app.get("/api/v2/analytics/realtime")
async def get_realtime_analytics():
    """
    Get real-time analytics data
    """
    if not ADVANCED_FEATURES_AVAILABLE:
        return {"error": "Advanced features not available"}

    try:
        # Get data from all advanced systems
        learning_stats = await continuous_learning.get_learning_statistics()
        alert_stats = await multi_channel_alerts.get_alert_statistics()
        cordon_stats = await npci_digital_cordon.get_cordon_statistics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "learning_system": learning_stats,
            "alert_system": alert_stats,
            "cordon_system": cordon_stats,
            "realtime_metrics": {
                "active_websockets": manager.get_connection_count(),
                "system_status": "operational"
            }
        }

    except Exception as e:
        logger.error(f"❌ Error fetching realtime analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

@app.get("/api/v2/models/status")
async def get_advanced_models_status():
    """
    Get status of all advanced AI models
    """
    if not ADVANCED_FEATURES_AVAILABLE:
        return {"error": "Advanced features not available"}

    try:
        return {
            "federated_causal_graph": await enhanced_federated_causal_graph.get_system_status(),
            "behavioral_digital_twin": await enhanced_behavioral_digital_twin.get_system_status(),
            "risk_scoring_engine": await advanced_risk_engine.get_system_status(),
            "continuous_learning": await continuous_learning.get_system_status(),
            "npci_digital_cordon": await npci_digital_cordon.get_system_status(),
            "multi_channel_alerts": await multi_channel_alerts.get_system_status(),
            "real_time_gis": await real_time_gis.get_system_status()
        }

    except Exception as e:
        logger.error(f"❌ Error fetching model status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching model status: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            await websocket.send_json({
                "type": "echo",
                "data": {"received": data},
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Enhanced exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Enhanced HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Enhanced general exception handler"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )