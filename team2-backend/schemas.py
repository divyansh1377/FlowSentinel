"""
FlowSentinel - Team 2 (Backend & Architecture)
Pydantic Data Validation Schemas conforming strictly to API_CONTRACT.md.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class SensorReadings(BaseModel):
    distance_cm: float = Field(..., ge=0.0, le=200.0, description="Ultrasonic sensor distance in cm")
    weight_kg: float = Field(..., ge=0.0, le=2000.0, description="HX711 Load Cell mass in kg")
    vibration_g: float = Field(..., ge=0.0, le=15.0, description="MPU6050 3-Axis vibration RMS in Gs")
    vibration_x: Optional[float] = Field(0.0, ge=-10.0, le=10.0, description="Tri-axial X-acceleration")
    vibration_y: Optional[float] = Field(0.0, ge=-10.0, le=10.0, description="Tri-axial Y-acceleration")
    vibration_z: Optional[float] = Field(0.0, ge=-10.0, le=10.0, description="Tri-axial Z-acceleration")

class OperationalMetrics(BaseModel):
    material_flow_rate_tph: Optional[float] = Field(200.0, ge=0.0, le=600.0, description="Tons per hour")
    feed_conveyor_speed_mps: Optional[float] = Field(2.5, ge=0.0, le=5.0, description="Belt velocity m/s")

class SimulationFlags(BaseModel):
    is_simulated: bool = True
    noise_injected: bool = False
    preset_scenario: Optional[str] = "CUSTOM"

class TelemetryPayload(BaseModel):
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    chute_id: Optional[str] = "CHUTE_BLAST_FURNACE_01"
    sensors: SensorReadings
    operational: Optional[OperationalMetrics] = Field(default_factory=OperationalMetrics)
    simulation_flags: Optional[SimulationFlags] = Field(default_factory=SimulationFlags)

class ClassProbabilities(BaseModel):
    normal: float
    warning: float
    blockage: float

class AnomalyResult(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    isolation_forest_raw: float

class PredictionResponse(BaseModel):
    timestamp: str
    chute_id: str
    status_code: int = Field(..., description="0=NORMAL, 1=WARNING, 2=BLOCKAGE")
    status_label: str
    status_color: str
    confidence_score: float
    probabilities: ClassProbabilities
    anomaly_detection: AnomalyResult
    root_cause_analysis: str
    recommended_action: str
    telemetry_echo: Dict[str, Any]
    latency_ms: float

class AlertEvent(BaseModel):
    alert_id: str
    timestamp: str
    severity: str  # "INFO", "WARNING", "CRITICAL"
    title: str
    message: str
    chute_id: str
    status_code: int
    acknowledged: bool = False

class SystemStatusResponse(BaseModel):
    status: str
    version: str
    ml_model_loaded: bool
    models: Dict[str, str]
    active_websocket_clients: int
    uptime_seconds: float
    active_mode: str
