"""Health check and root endpoints."""

from fastapi import APIRouter
from datetime import datetime
from services.database import db_service


router = APIRouter()


@router.get(
    "/",
    summary="API Information",
    description="Returns basic API information including service name, version, and status",
    tags=["Health"]
)
def root():
    """API info endpoint."""
    return {
        "service": "PartSelect Chat Agent",
        "version": "1.0.0",
        "status": "online"
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Check API health status and database connectivity",
    tags=["Health"]
)
def health():
    """Health check with database status."""
    db_status = "connected" if db_service.test_connection() else "disconnected"
    
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }
