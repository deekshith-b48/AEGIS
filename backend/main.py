from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import complaints, predictions, alerts, cordons
from app.database import engine, Base
import uvicorn
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project AEGIS API",
    description="Anticipatory Engine for Geolocated Intervention against Scams",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(complaints.router, prefix="/api", tags=["complaints"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(cordons.router, prefix="/api", tags=["cordons"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "aegis-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)