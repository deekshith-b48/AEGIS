from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CordonRequest, CordonResponse
from app.services.cordon_service import CordonService

router = APIRouter()

@router.post("/activate-cordon")
async def activate_digital_cordon(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Activate digital cordon around specified location
    """
    try:
        cordon_service = CordonService(db)
        hotspot_id = request.get("hotspot_id")
        radius_meters = request.get("radius_meters")
        duration_minutes = request.get("duration_minutes")

        if not hotspot_id:
            raise HTTPException(status_code=400, detail="hotspot_id is required")

        result = cordon_service.activate_cordon(
            hotspot_id=hotspot_id,
            radius_meters=radius_meters,
            duration_minutes=duration_minutes
        )

        return {
            "success": True,
            "cordon_id": result["cordon_id"],
            "message": "Digital cordon activated successfully",
            "details": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-cordons")
async def get_active_cordons(db: Session = Depends(get_db)):
    """
    Get all currently active digital cordons
    """
    try:
        cordon_service = CordonService(db)
        active_cordons = cordon_service.get_active_cordons()

        cordon_geojson_list = []
        for cordon in active_cordons:
            geojson = cordon_service.get_cordon_geojson(cordon)
            if geojson:
                cordon_geojson_list.append(geojson)

        return {
            "success": True,
            "cordons": cordon_geojson_list,
            "count": len(cordon_geojson_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deactivate-cordon/{cordon_id}")
async def deactivate_cordon(
    cordon_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually deactivate a digital cordon
    """
    try:
        cordon_service = CordonService(db)
        success = cordon_service.deactivate_cordon(cordon_id)

        if success:
            return {
                "success": True,
                "message": f"Digital cordon {cordon_id} deactivated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Cordon not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))