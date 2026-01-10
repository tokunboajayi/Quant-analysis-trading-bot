"""
Replay Store - JSONL persistence for telemetry frames
======================================================
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.settings import settings


class ReplayStore:
    """
    Stores and retrieves telemetry frames for replay.
    Uses append-only JSONL files.
    """
    
    def __init__(self):
        self.base_dir = settings.TELEMETRY_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def append_frame(self, run_id: str, frame: Dict[str, Any]):
        """Append a frame to the run's JSONL file."""
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        frames_file = run_dir / "frames.jsonl"
        
        with open(frames_file, "a") as f:
            f.write(json.dumps(frame) + "\n")
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List all available replay runs."""
        runs = []
        
        if not self.base_dir.exists():
            return runs
        
        for run_dir in self.base_dir.iterdir():
            if run_dir.is_dir():
                frames_file = run_dir / "frames.jsonl"
                if frames_file.exists():
                    # Count frames
                    with open(frames_file) as f:
                        frame_count = sum(1 for _ in f)
                    
                    # Get first/last timestamps
                    first_ts = None
                    last_ts = None
                    trading_date = run_dir.name[:8] if len(run_dir.name) >= 8 else None
                    
                    runs.append({
                        "run_id": run_dir.name,
                        "trading_date": trading_date,
                        "frame_count": frame_count
                    })
        
        return sorted(runs, key=lambda x: x.get("trading_date", ""), reverse=True)
    
    def get_frames(
        self,
        run_id: str,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get frames for a run, optionally filtered by timestamp."""
        frames_file = self.base_dir / run_id / "frames.jsonl"
        
        if not frames_file.exists():
            return []
        
        frames = []
        
        with open(frames_file) as f:
            for line in f:
                if len(frames) >= limit:
                    break
                
                try:
                    frame = json.loads(line.strip())
                    
                    # Filter by timestamp if specified
                    ts = frame.get("ts_utc", "")
                    if start_ts and ts < start_ts:
                        continue
                    if end_ts and ts > end_ts:
                        continue
                    
                    frames.append(frame)
                except:
                    pass
        
        return frames
