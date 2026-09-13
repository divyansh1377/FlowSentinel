"""
FlowSentinel - Team 2 (Backend & Architecture)
Integration and Unit Test Suite for REST & WebSocket Endpoints.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Path setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ML_DIR = os.path.join(PROJECT_ROOT, "team3-ml-simulation")
sys.path.append(CURRENT_DIR)
sys.path.append(ML_DIR)

from main import app
from simulator_service import simulator_service

client = TestClient(app)

def test_system_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "ml_model_loaded" in data

def test_get_presets():
    response = client.get("/api/presets")
    assert response.status_code == 200
    presets = response.json()
    assert "NORMAL_FLOW" in presets
    assert "COMPLETE_BLOCKAGE" in presets
    assert presets["COMPLETE_BLOCKAGE"]["weight_kg"] > 800

def test_telemetry_inference_normal():
    payload = {
        "sensors": {
            "distance_cm": 55.0,
            "weight_kg": 320.0,
            "vibration_g": 3.2
        },
        "operational": {
            "material_flow_rate_tph": 240.0
        }
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] in [0, 1, 2]
    assert "probabilities" in data
    assert "anomaly_detection" in data
    assert data["latency_ms"] < 20.0


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("sensors", "weight_kg"), 2000.1),
        (("sensors", "vibration_g"), 15.1),
        (("sensors", "vibration_x"), -10.1),
        (("sensors", "vibration_y"), 10.1),
        (("sensors", "vibration_z"), -10.1),
        (("operational", "material_flow_rate_tph"), 600.1),
        (("operational", "feed_conveyor_speed_mps"), 5.1),
    ],
)
def test_telemetry_rejects_out_of_contract_values(field_path, value):
    payload = {
        "sensors": {
            "distance_cm": 55.0,
            "weight_kg": 320.0,
            "vibration_g": 3.2,
        },
        "operational": {
            "material_flow_rate_tph": 240.0,
            "feed_conveyor_speed_mps": 2.5,
        },
    }
    payload[field_path[0]][field_path[1]] = value

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == field_path[1] for error in errors)

def test_telemetry_inference_blockage():
    payload = {
        "sensors": {
            "distance_cm": 5.0,
            "weight_kg": 1200.0,
            "vibration_g": 0.15
        },
        "operational": {
            "material_flow_rate_tph": 0.0
        }
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 2  # BLOCKAGE
    assert data["status_label"] == "BLOCKAGE"
    assert data["status_color"] == "RED"

def test_get_alerts():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_websocket_endpoint():
    with client.websocket_connect("/ws/telemetry") as websocket:
        # Handshake frame
        initial = websocket.receive_json()
        assert initial["type"] == "HANDSHAKE"

        # Send simulation slider movement
        websocket.send_json({
            "type": "SIMULATION_UPDATE",
            "payload": {
                "distance_cm": 10.0,
                "weight_kg": 1000.0,
                "vibration_g": 0.2
            }
        })

        # Receive responses (may include an alert frame followed by prediction frame)
        msg1 = websocket.receive_json()
        if msg1["type"] == "CRITICAL_ALERT":
            assert "alert_id" in msg1["data"]
            msg2 = websocket.receive_json()
            assert msg2["type"] == "TELEMETRY_PREDICTION"
            assert msg2["data"]["status_code"] in [1, 2]
        else:
            assert msg1["type"] == "TELEMETRY_PREDICTION"
            assert msg1["data"]["status_code"] in [1, 2]


def test_auto_simulation_broadcast_lifecycle():
    """Auto mode starts with the app and broadcasts physics-generated inference frames."""
    with TestClient(app) as lifecycle_client:
        try:
            with lifecycle_client.websocket_connect("/ws/telemetry") as websocket:
                assert websocket.receive_json()["type"] == "HANDSHAKE"
                websocket.send_json({
                    "type": "SET_SIMULATION_MODE",
                    "payload": {
                        "mode": "auto",
                        "preset": "NORMAL_FLOW",
                        "interval_ms": 100,
                    },
                })

                mode_changed = websocket.receive_json()
                assert mode_changed["type"] == "SIMULATION_MODE_CHANGED"
                assert mode_changed["data"]["mode"] == "auto"

                prediction = websocket.receive_json()
                assert prediction["type"] == "TELEMETRY_PREDICTION"
                assert prediction["data"]["status_code"] in [0, 1, 2]
                assert prediction["data"]["chute_id"] == "CHUTE_BLAST_FURNACE_01"
        finally:
            simulator_service.set_mode("manual")
