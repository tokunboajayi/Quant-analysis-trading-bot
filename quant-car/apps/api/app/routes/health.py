"""
Health check endpoint
=====================
"""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "ok",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
