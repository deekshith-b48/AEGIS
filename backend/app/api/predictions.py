from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/predictions/health")
async def predictions_health():
    """
    Health check for predictions service
    """
    return {"status": "healthy", "service": "predictions-api"}