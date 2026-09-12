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
    assert data["latency_ms"] < 50.0

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

        reply = websocket.receive_json()
        assert reply["type"] == "TELEMETRY_PREDICTION"
        assert reply["data"]["status_code"] == 2

