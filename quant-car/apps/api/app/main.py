"""
FastAPI Main Application
=========================
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.settings import settings
from app.routes import health, telemetry, ws, replay, research, incidents, bot, portfolio
from app.telemetry.builder import TelemetryBuilder


# Global builder instance
builder = TelemetryBuilder()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: build initial frame
    try:
        builder.build_frame()
        print("[OK] Initial telemetry frame built")
    except Exception as e:
        print(f"[WARN] Could not build initial frame: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down telemetry service...")


app = FastAPI(
    title="RiskFusion Quant Car Telemetry",
    version="1.0.0",
    description="Real-time telemetry streaming for the Quant Car cockpit",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router, tags=["Health"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
app.include_router(ws.router, prefix="/telemetry", tags=["WebSocket"])
app.include_router(replay.router, prefix="/replay", tags=["Replay"])
app.include_router(research.router)
app.include_router(incidents.router)
app.include_router(bot.router)
app.include_router(portfolio.router)


@app.get("/")
async def root():
    return {
        "service": "RiskFusion Quant Car Telemetry",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "latest": "/telemetry/latest",
            "stream": "/telemetry/stream",
            "replay": "/replay/index"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
