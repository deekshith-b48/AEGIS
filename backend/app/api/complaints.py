from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, Complaint, Hotspot
from app.models import ComplaintRequest, ComplaintResponse, RiskHeatmapResponse
from app.services.prediction_engine import PredictionEngine
from app.services.geospatial import create_location_point, complaint_to_geojson, hotspot_to_response
from datetime import datetime, timedelta
import uuid

router = APIRouter()

@router.post("/submit-complaint", response_model=ComplaintResponse)
async def submit_complaint(
    complaint: ComplaintRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a new scam complaint and trigger prediction analysis.
    """
    try:
        # Create complaint record
        location_point = create_location_point(
            complaint.victim_location['lat'],
            complaint.victim_location['lon']
        )

        # Convert string point to Geography object
        location_geography = text(f"ST_GeomFromText('POINT({complaint.victim_location['lon']} {complaint.victim_location['lat']})', 4326)")

        db_complaint = Complaint(
            scam_type=complaint.scam_type,
            amount=complaint.amount,
            victim_location=location_geography
        )

        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)

        # Trigger prediction analysis
        prediction_engine = PredictionEngine(db)
        hotspots_created = prediction_engine.predict_hotspots(str(db_complaint.id))

        return ComplaintResponse(
            success=True,
            complaint_id=str(db_complaint.id),
            message="Complaint submitted successfully. Analysis in progress.",
            prediction_triggered=len(hotspots_created) > 0
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-heatmap")
async def get_risk_heatmap(db: Session = Depends(get_db)):
    """
    Get current risk heatmap data for LEA dashboard.
    """
    try:
        # Get recent complaints (last 2 hours)
        recent_complaints = db.query(Complaint).filter(
            Complaint.created_at >= datetime.utcnow() - timedelta(hours=2)
        ).all()

        # Get active hotspots
        active_hotspots = db.query(Hotspot).filter(
            Hotspot.status == "active",
            Hotspot.predicted_at >= datetime.utcnow() - timedelta(minutes=90)
        ).all()

        # Get active cordons
        from app.database import Cordon
        active_cordons = db.query(Cordon).filter(
            Cordon.status == "active",
            Cordon.expires_at > datetime.utcnow()
        ).all()

        # Convert to GeoJSON and response formats
        complaints_geojson = []
        for complaint in recent_complaints:
            # Get coordinates as GeoJSON
            coords_result = db.execute(
                text("SELECT ST_AsGeoJSON(victim_location) as geojson FROM complaints WHERE id = :id"),
                {"id": complaint.id}
            ).fetchone()

            complaints_geojson.append({
                "type": "Feature",
                "geometry": coords_result.geojson if coords_result else None,
                "properties": {
                    "id": str(complaint.id),
                    "scam_type": complaint.scam_type,
                    "amount": float(complaint.amount),
                    "created_at": complaint.created_at.isoformat()
                }
            })

        # Convert cordons to GeoJSON
        cordons_geojson = []
        for cordon in active_cordons:
            # Get center coordinates
            center_result = db.execute(
                text("SELECT ST_AsGeoJSON(center_location) as geojson FROM cordons WHERE id = :id"),
                {"id": cordon.id}
            ).fetchone()

            # Create circular polygon (simplified)
            cordons_geojson.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[]]  # Simplified for MVP
                },
                "properties": {
                    "id": str(cordon.id),
                    "radius_meters": cordon.radius_meters,
                    "center": center_result.geojson if center_result else None,
                    "expires_at": cordon.expires_at.isoformat(),
                    "status": cordon.status
                }
            })

        return RiskHeatmapResponse(
            complaints=complaints_geojson,
            hotspots=[hotspot_to_response(h, db) for h in active_hotspots],
            cordons=cordons_geojson,
            system_metrics={
                "active_complaints": len(recent_complaints),
                "active_hotspots": len(active_hotspots),
                "active_cordons": len(active_cordons),
                "system_accuracy": 0.58  # Hardcoded for MVP
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(
    feedback_data: dict,
    db: Session = Depends(get_db)
):
    """
    Submit LEA feedback on hotspot predictions
    """
    try:
        from app.database import Feedback

        feedback = Feedback(
            hotspot_id=feedback_data.get("hotspot_id"),
            lea_action=feedback_data.get("lea_action"),
            notes=feedback_data.get("notes")
        )

        db.add(feedback)

        # Update hotspot status if needed
        if feedback_data.get("lea_action") == "interdicted":
            hotspot = db.query(Hotspot).filter(
                Hotspot.id == feedback_data.get("hotspot_id")
            ).first()
            if hotspot:
                hotspot.status = "interdicted"
        elif feedback_data.get("lea_action") == "false":
            hotspot = db.query(Hotspot).filter(
                Hotspot.id == feedback_data.get("hotspot_id")
            ).first()
            if hotspot:
                hotspot.status = "false_alert"

        db.commit()

        return {"success": True, "message": "Feedback submitted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))