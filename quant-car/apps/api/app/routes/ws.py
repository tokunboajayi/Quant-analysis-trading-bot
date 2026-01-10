"""
WebSocket telemetry stream
==========================
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Literal

from app.telemetry.builder import TelemetryBuilder
from app.settings import settings

router = APIRouter()
builder = TelemetryBuilder()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@router.websocket("/stream")
async def telemetry_stream(
    websocket: WebSocket,
    mode: Literal["latest", "follow"] = Query(default="follow"),
    interval_ms: int = Query(default=500, ge=100, le=5000)
):
    """
    WebSocket telemetry stream.
    
    - mode=latest: Send one frame and close
    - mode=follow: Push frames continuously at interval
    """
    await manager.connect(websocket)
    
    try:
        if mode == "latest":
            # Send single frame and close
            frame = builder.build_frame()
            await websocket.send_json(frame.model_dump(by_alias=True))
            return
        
        # Follow mode: push frames continuously
        interval_sec = interval_ms / 1000.0
        max_rate = settings.TELEMETRY_MAX_RATE_HZ
        min_interval = 1.0 / max_rate
        actual_interval = max(interval_sec, min_interval)
        
        while True:
            try:
                frame = builder.build_frame()
                await websocket.send_json(frame.model_dump(by_alias=True))
                await asyncio.sleep(actual_interval)
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Send error but continue
                await websocket.send_json({
                    "error": str(e),
                    "type": "frame_build_error"
                })
                await asyncio.sleep(actual_interval)
    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
