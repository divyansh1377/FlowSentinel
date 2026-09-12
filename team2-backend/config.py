"""
FlowSentinel - Team 2 (Backend & Architecture)
Configuration & Environment Settings
"""

import os
from pydantic import BaseModel

class SystemConfig(BaseModel):
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    
    # WebSocket Streaming Interval for Auto Mode (ms)
    STREAM_INTERVAL_MS: int = int(os.getenv("STREAM_INTERVAL_MS", "400"))
    
    # Alert Debounce Window (seconds) to prevent hysteresis flapping
    ALERT_DEBOUNCE_SECONDS: float = float(os.getenv("ALERT_DEBOUNCE_SECONDS", "1.5"))
    
    # Path to Team 3 ML models directory
    MODELS_DIR: str = os.getenv(
        "MODELS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team3-ml-simulation", "models")
    )
    
    # Path to Team 1 Frontend static directory
    FRONTEND_DIR: str = os.getenv(
        "FRONTEND_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team1-frontend")
    )

settings = SystemConfig()

