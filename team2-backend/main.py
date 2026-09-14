"""
FlowSentinel - Team 2 (Backend & Architecture)
Main FastAPI Application Entrypoint

Exposes REST APIs, WebSocket Telemetry Hub, and serves the Team 1 SCADA Frontend.
"""

import sys
import os
import time
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add paths for cross-team modularity
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ML_DIR = os.path.join(PROJECT_ROOT, "team3-ml-simulation")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "team1-frontend")

sys.path.append(CURRENT_DIR)
sys.path.append(ML_DIR)

from config import settings
from schemas import (
    TelemetryPayload,
    PredictionResponse,
    SystemStatusResponse,
    AlertEvent,
    AlertAcknowledgeRequest,
    AlertAcknowledgeResponse,
)
from websocket_manager import ws_hub
from alert_dispatcher import alert_dispatcher
from simulator_service import simulator_service
from model_pipeline import ChutePredictor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FlowSentinel.Main")

# Initialize Machine Learning Engine
predictor = ChutePredictor(models_dir=os.path.join(ML_DIR, "models"))
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize background simulator & predictor
    logger.info("🚀 [FastAPI] Initializing FlowSentinel Backend Engine...")
    simulator_service.initialize(predictor, alert_dispatcher)
    sim_task = asyncio.create_task(simulator_service.start_loop())
    yield
    # Shutdown
    logger.info("🛑 [FastAPI] Shutting down FlowSentinel Backend Engine...")
    simulator_service.stop()
    sim_task.cancel()


app = FastAPI(
    title="FlowSentinel - AI Chute Blockage Detection Backend",
    description="Real-time SCADA telemetry ingestion, WebSocket pipeline, and ML inference service.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-origin frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------


@app.get("/api/status", response_model=SystemStatusResponse, tags=["System"])
async def get_system_status():
    """
    Returns the real-time health and metadata of backend & ML models.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "ml_model_loaded": predictor.is_loaded,
        "models": {
            "random_forest": (
                "Trained (v1.0)" if predictor.is_loaded else "Heuristic Fallback"
            ),
            "isolation_forest": (
                "Trained (v1.0)" if predictor.is_loaded else "Heuristic Fallback"
            ),
        },
        "active_websocket_clients": ws_hub.client_count,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "active_mode": simulator_service.mode,
    }


@app.post("/api/telemetry", response_model=PredictionResponse, tags=["Inference"])
async def process_telemetry(payload: TelemetryPayload):
    """
    Ingests single telemetry sample, runs ML inference, and evaluates alerts.
    """
    sample_dict = {
        "distance_cm": payload.sensors.distance_cm,
        "weight_kg": payload.sensors.weight_kg,
        "vibration_g": payload.sensors.vibration_g,
        "material_flow_rate_tph": (
            payload.operational.material_flow_rate_tph if payload.operational else 200.0
        ),
    }

    prediction = predictor.predict(sample_dict)
    prediction["timestamp"] = (
        payload.timestamp or datetime.now(timezone.utc).isoformat()
    )
    prediction["chute_id"] = payload.chute_id or "CHUTE_BLAST_FURNACE_01"

    # Evaluate alerts
    await alert_dispatcher.evaluate_prediction(prediction, prediction["chute_id"])

    # Broadcast to all live WebSocket dashboards
    await ws_hub.broadcast_json("TELEMETRY_PREDICTION", prediction)

    return prediction


@app.get("/api/presets", tags=["Simulation"])
async def get_simulation_presets():
    """
    Returns standard industrial test scenarios for simulation controls.
    """
    return {
        "NORMAL_FLOW": {
            "name": "Normal Continuous Flow",
            "description": "Dynamic material transfer with healthy clearance and rock collision impact vibrations.",
            "distance_cm": 52.0,
            "weight_kg": 320.0,
            "vibration_g": 3.4,
            "material_flow_rate_tph": 240.0,
        },
        "RISING_BUILDUP": {
            "name": "Sluggish Flow & Sidewall Buildup",
            "description": "Ore sticking to chute walls, clearance narrowing, vibration dampening.",
            "distance_cm": 24.0,
            "weight_kg": 680.0,
            "vibration_g": 1.2,
            "material_flow_rate_tph": 110.0,
        },
        "COMPLETE_BLOCKAGE": {
            "name": "Critical Chute Choke / Plug",
            "description": "Complete material stagnation, excessive load cell weight, dead vibration.",
            "distance_cm": 6.5,
            "weight_kg": 1150.0,
            "vibration_g": 0.18,
            "material_flow_rate_tph": 0.0,
        },
        "EMPTY_CHUTE": {
            "name": "Empty Feeder Chute",
            "description": "No ore on belt, max clearance, 0kg weight, idling baseline vibration.",
            "distance_cm": 95.0,
            "weight_kg": 0.0,
            "vibration_g": 0.08,
            "material_flow_rate_tph": 0.0,
        },
        "ERRATIC_SENSOR_SPIKE": {
            "name": "Sensor Fault / Severe Resonance",
            "description": "Out-of-distribution high frequency vibration spike triggering Isolation Forest.",
            "distance_cm": 50.0,
            "weight_kg": 310.0,
            "vibration_g": 12.8,
            "material_flow_rate_tph": 220.0,
        },
    }


@app.get("/api/alerts", tags=["Alerts"])
async def get_alerts(limit: int = Query(50, ge=1, le=200)):
    """
    Returns chronological audit log of triggered warning & blockage events.
    """
    return alert_dispatcher.get_history(limit=limit)


@app.post(
    "/api/alerts/{alert_id}/acknowledge",
    response_model=AlertAcknowledgeResponse,
    tags=["Alerts"],
)
async def acknowledge_alert(
    alert_id: str = Path(...), body: Optional[AlertAcknowledgeRequest] = None
):
    """
    Acknowledge a specific alert by ID.
    """
    success = alert_dispatcher.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Alert with ID {alert_id} not found."
        )

    # Broadcast acknowledgement to WebSocket clients
    await ws_hub.broadcast_json(
        "ALERT_ACKNOWLEDGED",
        {
            "alert_id": alert_id,
            "acknowledged_by": body.acknowledged_by if body else "operator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "status": "success",
        "alert_id": alert_id,
        "acknowledged": True,
        "message": f"Alert {alert_id} has been acknowledged.",
    }


@app.delete("/api/alerts", tags=["Alerts"])
async def clear_alerts():
    """
    Clear alert history (useful for reset and testing).
    """
    alert_dispatcher.clear_history()
    await ws_hub.broadcast_json(
        "ALERTS_CLEARED", {"timestamp": datetime.now(timezone.utc).isoformat()}
    )
    return {"status": "success", "message": "Alert history cleared."}


@app.post("/api/retrain", tags=["Machine Learning"])
async def trigger_retrain():
    """
    Triggers re-training of the ML models using Team 3's pipeline.
    """
    try:
        from train_models import train_and_export_models

        meta = train_and_export_models(n_samples=10000)
        predictor.load_models()
        return {
            "status": "success",
            "message": "Models successfully retrained and reloaded into memory.",
            "metadata": meta,
        }
    except Exception as e:
        logger.error(f"Failed to retrain models: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrain models: {str(e)}"
        )


# ---------------------------------------------------------
# WebSocket Real-Time Telemetry Pipeline
# ---------------------------------------------------------


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    Bidirectional WebSocket pipeline for high-frequency real-time simulation and telemetry streaming.
    """
    await ws_hub.connect(websocket)
    try:
        # Send initial system handshake
        await ws_hub.send_direct_json(
            websocket,
            "HANDSHAKE",
            {
                "status": "connected",
                "ml_loaded": predictor.is_loaded,
                "server_time": datetime.now(timezone.utc).isoformat(),
            },
        )

        while True:
            raw_text = await websocket.receive_text()
            try:
                import json

                data = json.loads(raw_text)
                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "SIMULATION_UPDATE":
                    # Manual slider movement from frontend
                    prediction = predictor.predict(payload)
                    prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
                    prediction["chute_id"] = payload.get(
                        "chute_id", "CHUTE_BLAST_FURNACE_01"
                    )

                    # Check alerts
                    await alert_dispatcher.evaluate_prediction(
                        prediction, prediction["chute_id"]
                    )

                    # Broadcast result to all connected dashboards
                    await ws_hub.broadcast_json("TELEMETRY_PREDICTION", prediction)

                elif msg_type == "SET_SIMULATION_MODE":
                    # Switch between manual sliders and auto-streamer
                    mode = payload.get("mode", "manual")
                    preset = payload.get("preset", "NORMAL_FLOW")
                    interval_ms = payload.get("interval_ms", 500)
                    simulator_service.set_mode(mode, preset, interval_ms)
                    await ws_hub.broadcast_json(
                        "SIMULATION_MODE_CHANGED",
                        {"mode": mode, "preset": preset, "interval_ms": interval_ms},
                    )

                elif msg_type == "ACKNOWLEDGE_ALERT":
                    alert_id = payload.get("alert_id")
                    if alert_id:
                        alert_dispatcher.acknowledge_alert(alert_id)
                        await ws_hub.broadcast_json(
                            "ALERT_ACKNOWLEDGED",
                            {
                                "alert_id": alert_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                elif msg_type == "PING":
                    await ws_hub.send_direct_json(
                        websocket,
                        "PONG",
                        {
                            "time": time.time(),
                            "server_time": datetime.now(timezone.utc).isoformat(),
                        },
                    )

            except Exception as parse_err:
                logger.warning(f"⚠️ [WebSocket] Message processing error: {parse_err}")

    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as e:
        logger.warning(f"⚠️ [WebSocket] Unexpected connection drop: {e}")
        ws_hub.disconnect(websocket)


# ---------------------------------------------------------
# Static File Mounting (Team 1 Frontend Integration)
# ---------------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        {
            "message": "FlowSentinel Backend is online. Place Team 1 frontend in team1-frontend/index.html to view dashboard."
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
