"""
FastAPI Telemetry Service - Settings
=====================================
Configured to connect to RiskFusion Alpha real data.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os


class Settings(BaseSettings):
    # Data paths - point to real RiskFusion outputs
    DATA_OUTPUT_DIR: Path = Path(os.path.expanduser(
        "~/OneDrive/Documents/finance ai/riskfusion_alpha/data/outputs"
    ))
    TELEMETRY_DIR: Path = Path("./data/telemetry_frames")
    
    # Telemetry config
    TELEMETRY_PUSH_INTERVAL_MS: int = 500
    TELEMETRY_MAX_RATE_HZ: float = 2.0
    
    # Normalization constants (match RiskFusion config)
    TURNOVER_CAP: float = 0.30
    TARGET_VOL: float = 0.12
    VAR_LIMIT: float = 0.05
    DRIFT_PSI_THRESHOLD: float = 0.20
    
    # Alpaca (optional, read-only) - will be loaded from RiskFusion .env
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True  # Enable for development
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Validate data directory exists
if not settings.DATA_OUTPUT_DIR.exists():
    print(f"[WARNING] Data directory not found: {settings.DATA_OUTPUT_DIR}")
    print("   The API will return degraded telemetry until RiskFusion generates data.")
else:
    print(f"[OK] Data directory found: {settings.DATA_OUTPUT_DIR}")
