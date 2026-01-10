"""
Replay endpoints
================
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pathlib import Path
import json

from app.settings import settings
from app.telemetry.replay_store import ReplayStore

router = APIRouter()
replay_store = ReplayStore()


@router.get("/index")
async def get_replay_index():
    """
    Get list of available replay runs.
    """
    runs = replay_store.list_runs()
    return {"runs": runs}


@router.get("/{run_id}")
async def get_replay_frames(
    run_id: str,
    start_ts: Optional[str] = Query(default=None),
    end_ts: Optional[str] = Query(default=None),
    limit: int = Query(default=1000, le=10000)
):
    """
    Get frames for a specific replay run.
    """
    frames = replay_store.get_frames(run_id, start_ts, end_ts, limit)
    
    if not frames:
        raise HTTPException(status_code=404, detail=f"No frames for run {run_id}")
    
    return {
        "run_id": run_id,
        "frame_count": len(frames),
        "frames": frames
    }
