from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/alerts/health")
async def alerts_health():
    """
    Health check for alerts service
    """
    return {"status": "healthy", "service": "alerts-api"}