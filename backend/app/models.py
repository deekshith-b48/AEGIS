from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ScamType(str, Enum):
    UPI_PHISHING = "UPI_PHISHING"
    FAKE_LOAN_APP = "FAKE_LOAN_APP"
    IMPERSONATION = "IMPERSONATION"
    LOTTERY_SCAM = "LOTTERY_SCAM"
    INVESTMENT_FRAUD = "INVESTMENT_FRAUD"

class ComplaintRequest(BaseModel):
    scam_type: ScamType
    amount: float = Field(..., gt=100, le=10000000)
    victim_location: dict = Field(..., example={"lat": 28.6139, "lon": 77.2090})

    @validator('victim_location')
    def validate_location(cls, v):
        if not isinstance(v, dict) or 'lat' not in v or 'lon' not in v:
            raise ValueError('Location must contain lat and lon')
        if not (-90 <= v['lat'] <= 90) or not (-180 <= v['lon'] <= 180):
            raise ValueError('Invalid latitude/longitude range')
        return v

class ComplaintResponse(BaseModel):
    success: bool
    complaint_id: str
    message: str
    prediction_triggered: bool

class HotspotResponse(BaseModel):
    id: str
    complaint_id: str
    hotspot_location: dict
    location_name: str
    confidence: float
    time_window_mins: int
    predicted_at: datetime
    status: str

class RiskHeatmapResponse(BaseModel):
    complaints: List[dict]  # GeoJSON FeatureCollection
    hotspots: List[HotspotResponse]
    cordons: List[dict]  # GeoJSON FeatureCollection
    system_metrics: dict

class FeedbackRequest(BaseModel):
    hotspot_id: str
    lea_action: str  # confirmed, false, interdicted
    notes: Optional[str] = None

class CordonRequest(BaseModel):
    center_location: dict
    radius_meters: int = 2000
    duration_minutes: int = 45

class CordonResponse(BaseModel):
    success: bool
    cordon_id: str
    message: str
    details: dict