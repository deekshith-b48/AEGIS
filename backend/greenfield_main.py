"""
Project AEGIS Greenfield Implementation
FastAPI Backend with exact specifications
Python 3.10+ with Uvicorn ASGI server
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import text
from app.database import SessionLocal, get_db, Complaint, Hotspot, Alert, Feedback, Cordon
from greenfield_ai_engine import greenfield_prediction_engine
from greenfield_alert_service import GreenfieldAlertService
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Project AEGIS API",
    description="Anticipatory Engine for Geolocated Intervention against Scams - Greenfield Implementation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for exact specifications
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://vercel.app,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize alert service
alert_service = GreenfieldAlertService()

# Pydantic Models for exact API specification

class ComplaintRequest(BaseModel):
    fraud_type: str = Field(..., description="Type of fraud (UPI_PHISHING, FAKE_LOAN_APP, etc.)")
    amount: float = Field(..., gt=100, description="Amount lost (must be > 100)")
    victim_lat: float = Field(..., ge=-90, le=90, description="Victim latitude")
    victim_lon: float = Field(..., ge=-180, le=180, description="Victim longitude")

    @validator('fraud_type')
    def validate_fraud_type(cls, v):
        valid_types = ['UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION', 'LOTTERY_SCAM', 'INVESTMENT_FRAUD']
        if v.upper() not in valid_types:
            raise ValueError(f"fraud_type must be one of: {valid_types}")
        return v.upper()

class FeedbackRequest(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot ID")
    outcome: str = Field(..., description="LEA outcome: 'confirmed' or 'false'")

    @validator('outcome')
    def validate_outcome(cls, v):
        if v not in ['confirmed', 'false']:
            raise ValueError("outcome must be 'confirmed' or 'false'")
        return v

class CordonRequest(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot ID to create cordon around")

class ComplaintResponse(BaseModel):
    success: bool
    complaint_id: str
    message: str
    prediction_triggered: bool

class RiskHeatmapResponse(BaseModel):
    success: bool
    complaints: list
    hotspots: list
    cordons: list
    system_metrics: dict

# API Endpoints - Exact Specification

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Project AEGIS API", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "aegis-api-greenfield"}

@app.post("/submit-complaint", response_model=ComplaintResponse)
async def submit_complaint(
    request: ComplaintRequest,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """
    POST /submit-complaint
    Validates and stores citizen report, triggers prediction
    Task Flow: insert into DB → invoke AI predictor → if confidence ≥ 0.8 → persist hotspot → dispatch alerts → return 202
    """
    try:
        logger.info(f"[/submit-complaint] Received complaint: {request.fraud_type}, amount: {request.amount}")

        # Step 1: Insert complaint into database
        complaint = Complaint(
            fraud_type=request.fraud_type,
            amount=request.amount,
            victim_location=text(f"ST_GeomFromText('POINT({request.victim_lon} {request.victim_lat})', 4326)")
        )

        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        complaint_id = str(complaint.id)
        logger.info(f"[/submit-complaint] Complaint stored: {complaint_id}")

        # Step 2: Invoke AI predictor
        prediction = greenfield_prediction_engine.predict_hotspot({
            'fraud_type': request.fraud_type,
            'amount': request.amount,
            'victim_lat': request.victim_lat,
            'victim_lon': request.victim_lon
        })

        prediction_triggered = False

        # Step 3: If confidence ≥ 0.8, persist hotspot and dispatch alerts
        if prediction:
            prediction_triggered = True

            # Create hotspot record
            hotspot = Hotspot(
                complaint_id=complaint.id,
                hotspot_location=text(f"ST_GeomFromText('POINT({prediction['hotspot_location'][0]} {prediction['hotspot_location'][1]})', 4326)"),
                location_name=prediction['location_name'],
                confidence=prediction['confidence'],
                time_window_mins=prediction['time_window_mins']
            )

            db.add(hotspot)
            db.commit()
            db.refresh(hotspot)

            hotspot_id = str(hotspot.id)
            logger.info(f"[/submit-complaint] Hotspot created: {hotspot_id}")

            # Step 4: Dispatch alerts in background
            background_tasks.add_task(
                dispatch_alerts_for_hotspot,
                hotspot_id,
                prediction,
                request.fraud_type,
                request.amount
            )

        return ComplaintResponse(
            success=True,
            complaint_id=complaint_id,
            message=f"Complaint submitted successfully{' with prediction' if prediction_triggered else ' (no high-confidence prediction)'}",
            prediction_triggered=prediction_triggered
        )

    except Exception as e:
        logger.error(f"[/submit-complaint] Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit complaint: {str(e)}")

async def dispatch_alerts_for_hotspot(
    hotspot_id: str,
    prediction: Dict,
    fraud_type: str,
    amount: float
):
    """
    Background task to dispatch alerts for high-confidence predictions
    """
    try:
        logger.info(f"[ALERTS] Dispatching alerts for hotspot: {hotspot_id}")

        # Send SMS alert
        sms_result = await alert_service.send_sms_alert(
            hotspot_id=hotspot_id,
            location_name=prediction['location_name'],
            fraud_type=fraud_type,
            amount=amount,
            confidence=prediction['confidence']
        )

        # Send email alert
        email_result = await alert_service.send_email_alert(
            hotspot_id=hotspot_id,
            location_name=prediction['location_name'],
            fraud_type=fraud_type,
            amount=amount,
            confidence=prediction['confidence']
        )

        # Log alert results in database
        with SessionLocal() as db:
            if sms_result:
                alert = Alert(
                    hotspot_id=hotspot_id,
                    channel='sms',
                    status='sent' if sms_result['success'] else 'failed'
                )
                db.add(alert)

            if email_result:
                alert = Alert(
                    hotspot_id=hotspot_id,
                    channel='email',
                    status='sent' if email_result['success'] else 'failed'
                )
                db.add(alert)

            db.commit()

        logger.info(f"[ALERTS] Alerts dispatched for hotspot: {hotspot_id}")

    except Exception as e:
        logger.error(f"[ALERTS] Failed to dispatch alerts for {hotspot_id}: {str(e)}")

@app.get("/risk-heatmap", response_model=RiskHeatmapResponse)
async def get_risk_heatmap(db: SessionLocal = Depends(get_db)):
    """
    GET /risk-heatmap
    Returns GeoJSON of active complaints + hotspots (last 90 mins)
    """
    try:
        logger.info("[/risk-heatmap] Generating risk heatmap")

        # Get complaints from last 90 minutes
        complaints_query = text("""
            SELECT id, fraud_type, amount, created_at,
                   ST_AsGeoJSON(victim_location) as victim_location_geojson
            FROM complaints
            WHERE created_at >= NOW() - INTERVAL '90 minutes'
            ORDER BY created_at DESC
        """)

        complaints_result = db.execute(complaints_query).fetchall()
        complaints = []

        for complaint in complaints_result:
            complaints.append({
                "type": "Feature",
                "geometry": json.loads(complaint.victim_location_geojson) if complaint.victim_location_geojson else None,
                "properties": {
                    "id": str(complaint.id),
                    "fraud_type": complaint.fraud_type,
                    "amount": float(complaint.amount),
                    "created_at": complaint.created_at.isoformat()
                }
            })

        # Get active hotspots from last 90 minutes
        hotspots_query = text("""
            SELECT id, complaint_id, location_name, confidence, time_window_mins, predicted_at,
                   ST_AsGeoJSON(hotspot_location) as hotspot_location_geojson
            FROM hotspots
            WHERE predicted_at >= NOW() - INTERVAL '90 minutes'
            ORDER BY predicted_at DESC
        """)

        hotspots_result = db.execute(hotspots_query).fetchall()
        hotspots = []

        for hotspot in hotspots_result:
            hotspots.append({
                "id": str(hotspot.id),
                "complaint_id": str(hotspot.complaint_id),
                "location_name": hotspot.location_name,
                "confidence": float(hotspot.confidence),
                "time_window_mins": hotspot.time_window_mins,
                "predicted_at": hotspot.predicted_at.isoformat(),
                "geometry": json.loads(hotspot.hotspot_location_geojson) if hotspot.hotspot_location_geojson else None
            })

        # Get active cordons
        cordons_query = text("""
            SELECT id, hotspot_id, radius_meters, activated_at, expires_at,
                   ST_X(center) as center_lon, ST_Y(center) as center_lat
            FROM cordons
            WHERE expires_at > NOW()
            ORDER BY activated_at DESC
        """)

        cordons_result = db.execute(cordons_query).fetchall()
        cordons = []

        for cordon in cordons_result:
            # Create simple circular polygon for visualization
            center_lon = float(cordon.center_lon)
            center_lat = float(cordon.center_lat)
            radius_deg = cordon.radius_meters / 111000  # Approximate conversion

            cordons.append({
                "id": str(cordon.id),
                "hotspot_id": str(cordon.hotspot_id),
                "radius_meters": cordon.radius_meters,
                "center": [center_lon, center_lat],
                "activated_at": cordon.activated_at.isoformat(),
                "expires_at": cordon.expires_at.isoformat(),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [center_lon - radius_deg, center_lat - radius_deg],
                        [center_lon + radius_deg, center_lat - radius_deg],
                        [center_lon + radius_deg, center_lat + radius_deg],
                        [center_lon - radius_deg, center_lat + radius_deg],
                        [center_lon - radius_deg, center_lat - radius_deg]
                    ]]
                }
            })

        # System metrics
        system_metrics = {
            "active_complaints": len(complaints),
            "active_hotspots": len(hotspots),
            "active_cordons": len(cordons),
            "system_accuracy": greenfield_prediction_engine.get_system_accuracy(),
            "rule_weights": greenfield_prediction_engine.get_rule_weights()
        }

        logger.info(f"[/risk-heatmap] Generated: {len(complaints)} complaints, {len(hotspots)} hotspots, {len(cordons)} cordons")

        return RiskHeatmapResponse(
            success=True,
            complaints=complaints,
            hotspots=hotspots,
            cordons=cordons,
            system_metrics=system_metrics
        )

    except Exception as e:
        logger.error(f"[/risk-heatmap] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate risk heatmap: {str(e)}")

@app.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: SessionLocal = Depends(get_db)
):
    """
    POST /feedback
    Logs LEA outcome ('confirmed'/'false') for learning loop
    """
    try:
        logger.info(f"[/feedback] Received feedback for hotspot: {request.hotspot_id}, outcome: {request.outcome}")

        # Store feedback in database
        feedback = Feedback(
            hotspot_id=request.hotspot_id,
            outcome=request.outcome
        )

        db.add(feedback)
        db.commit()

        # Update AI engine rule weights
        greenfield_prediction_engine.update_rule_weights(request.outcome)

        logger.info(f"[/feedback] Feedback processed and rule weights updated")

        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "system_accuracy": greenfield_prediction_engine.get_system_accuracy()
        }

    except Exception as e:
        logger.error(f"[/feedback] Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@app.post("/activate-cordon")
async def activate_cordon(
    request: CordonRequest,
    db: SessionLocal = Depends(get_db)
):
    """
    POST /activate-cordon
    Creates simulated digital cordon (2km radius, 45-min expiry)
    """
    try:
        logger.info(f"[/activate-cordon] Activating cordon for hotspot: {request.hotspot_id}")

        # Get hotspot location
        hotspot_query = text("""
            SELECT hotspot_location FROM hotspots WHERE id = :hotspot_id
        """)
        hotspot_result = db.execute(hotspot_query, {"hotspot_id": request.hotspot_id}).fetchone()

        if not hotspot_result:
            raise HTTPException(status_code=404, detail="Hotspot not found")

        # Create cordon record
        cordon = Cordon(
            hotspot_id=request.hotspot_id,
            center=hotspot_result.hotspot_location,
            radius_meters=2000,  # 2km radius as per specification
            expires_at=datetime.utcnow() + timedelta(minutes=45)  # 45-min expiry
        )

        db.add(cordon)
        db.commit()
        db.refresh(cordon)

        # Simulate NPCI integration (for demo purposes)
        logger.info(f"[NPCI SIMULATION] Digital cordon activated: {cordon.id}")
        logger.info(f"[NPCI SIMULATION] 2km radius around hotspot {request.hotspot_id}")
        logger.info(f"[NPCI SIMULATION] Transaction monitoring active for 45 minutes")
        logger.info(f"[NPCI SIMULATION] NPCI Reference: NPCI-{uuid.uuid4().hex[:8].upper()}")

        return {
            "success": True,
            "cordon_id": str(cordon.id),
            "message": "Digital cordon activated successfully",
            "radius_meters": 2000,
            "expires_at": cordon.expires_at.isoformat(),
            "npci_reference": f"NPCI-{uuid.uuid4().hex[:8].upper()}"
        }

    except Exception as e:
        logger.error(f"[/activate-cordon] Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate cordon: {str(e)}")

@app.post("/re-weight-rules")
async def reweight_rules(
    feedback_type: str = Field(..., description="Feedback type: 'confirmed' or 'false'")
):
    """
    Manual endpoint to simulate nightly rule re-weighting for demo
    """
    try:
        if feedback_type not in ['confirmed', 'false']:
            raise HTTPException(status_code=400, detail="feedback_type must be 'confirmed' or 'false'")

        logger.info(f"[/re-weight-rules] Manual re-weighting with feedback: {feedback_type}")

        # Update rule weights
        greenfield_prediction_engine.update_rule_weights(feedback_type)

        return {
            "success": True,
            "message": f"Rule weights re-weighted based on {feedback_type} feedback",
            "new_weights": greenfield_prediction_engine.get_rule_weights(),
            "system_accuracy": greenfield_prediction_engine.get_system_accuracy()
        }

    except Exception as e:
        logger.error(f"[/re-weight-rules] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to re-weight rules: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "greenfield_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )