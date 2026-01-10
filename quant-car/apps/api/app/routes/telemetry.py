"""
Telemetry REST endpoints
========================
"""
from fastapi import APIRouter, HTTPException

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from telemetry.models import TelemetryFrame

from app.telemetry.builder import TelemetryBuilder

router = APIRouter()
builder = TelemetryBuilder()


@router.get("/latest", response_model=TelemetryFrame)
async def get_latest_telemetry():
    """
    Get the latest telemetry frame.
    """
    try:
        frame = builder.build_frame()
        return frame
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build frame: {e}")


@router.get("/frame/{trading_date}", response_model=TelemetryFrame)
async def get_frame_by_date(trading_date: str):
    """
    Get telemetry frame for a specific trading date.
    Date format: YYYYMMDD
    """
    try:
        frame = builder.build_frame(trading_date)
        return frame
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"No data for {trading_date}: {e}")
