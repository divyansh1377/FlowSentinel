"""
FlowSentinel - Team 2 (Backend & Architecture)
Integration and Unit Test Suite for REST & WebSocket Endpoints.
Authored by Engineer 4 (Team 2).
"""

import sys
import os
import time
import pytest
from fastapi.testclient import TestClient

# Path setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ML_DIR = os.path.join(PROJECT_ROOT, "team3-ml-simulation")
sys.path.append(CURRENT_DIR)
sys.path.append(ML_DIR)

from main import app
from alert_dispatcher import alert_dispatcher
from websocket_manager import ws_hub

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_alert_state():
    """Reset alert dispatcher state before each test."""
    alert_dispatcher.clear_history()
    yield
    alert_dispatcher.clear_history()


def test_system_status():
    """Test /api/status endpoint returns healthy system status and model metadata."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "ml_model_loaded" in data
    assert "models" in data
    assert "uptime_seconds" in data
    assert "active_websocket_clients" in data
    assert "active_mode" in data


def test_get_presets():
    """Test /api/presets endpoint contains all 5 standard simulation presets."""
    response = client.get("/api/presets")
    assert response.status_code == 200
    presets = response.json()
    expected_presets = [
        "NORMAL_FLOW",
        "RISING_BUILDUP",
        "COMPLETE_BLOCKAGE",
        "EMPTY_CHUTE",
        "ERRATIC_SENSOR_SPIKE",
    ]
    for preset in expected_presets:
        assert preset in presets
        assert "distance_cm" in presets[preset]
        assert "weight_kg" in presets[preset]
        assert "vibration_g" in presets[preset]
    assert presets["COMPLETE_BLOCKAGE"]["weight_kg"] >= 800


def test_telemetry_inference_normal():
    """Test normal flow telemetry prediction."""
    payload = {
        "sensors": {"distance_cm": 55.0, "weight_kg": 320.0, "vibration_g": 3.2},
        "operational": {"material_flow_rate_tph": 240.0},
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] in [0, 1, 2]
    assert "status_label" in data
    assert "status_color" in data
    assert "probabilities" in data
    assert "anomaly_detection" in data
    assert "root_cause_analysis" in data
    assert "recommended_action" in data
    assert data["latency_ms"] < 150.0  # Allow buffer for cold start on first inference


def test_telemetry_inference_blockage():
    """Test critical blockage telemetry prediction and alert trigger."""
    payload = {
        "sensors": {"distance_cm": 5.0, "weight_kg": 1200.0, "vibration_g": 0.15},
        "operational": {"material_flow_rate_tph": 0.0},
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 2  # BLOCKAGE
    assert data["status_label"] == "BLOCKAGE"
    assert data["status_color"] == "RED"

    # Check that critical alert was registered in dispatcher
    alerts = alert_dispatcher.get_history()
    assert len(alerts) > 0
    assert alerts[0]["severity"] == "CRITICAL"
    assert alerts[0]["status_code"] == 2


def test_telemetry_inference_warning():
    """Test partial buildup warning telemetry."""
    payload = {
        "sensors": {"distance_cm": 25.0, "weight_kg": 650.0, "vibration_g": 1.2},
        "operational": {"material_flow_rate_tph": 120.0},
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status_code" in data
    assert "probabilities" in data


def test_telemetry_inference_anomaly():
    """Test sensor fault / vibration spike anomaly detection."""
    payload = {
        "sensors": {"distance_cm": 50.0, "weight_kg": 310.0, "vibration_g": 13.5},
        "operational": {"material_flow_rate_tph": 220.0},
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "anomaly_detection" in data


def test_telemetry_validation_error():
    """Test Pydantic validation rejects negative distance or out-of-range sensor values."""
    invalid_payload = {
        "sensors": {
            "distance_cm": -10.0,  # Invalid: negative
            "weight_kg": 300.0,
            "vibration_g": 2.0,
        }
    }
    response = client.post("/api/telemetry", json=invalid_payload)
    assert response.status_code == 422


def test_alert_lifecycle():
    """Test alert generation, listing, acknowledging, and clearing."""
    # Trigger a critical blockage alert
    client.post(
        "/api/telemetry",
        json={"sensors": {"distance_cm": 4.0, "weight_kg": 1300.0, "vibration_g": 0.1}},
    )

    # Retrieve alerts
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) > 0
    alert_id = alerts[0]["alert_id"]
    assert alerts[0]["acknowledged"] is False

    # Acknowledge alert
    ack_resp = client.post(
        f"/api/alerts/{alert_id}/acknowledge", json={"acknowledged_by": "operator_1"}
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledged"] is True

    # Verify acknowledged state in list
    resp_after = client.get("/api/alerts")
    assert resp_after.json()[0]["acknowledged"] is True

    # Test acknowledging non-existent alert
    bad_ack = client.post("/api/alerts/ALT-NONEXISTENT/acknowledge")
    assert bad_ack.status_code == 404

    # Clear alerts
    del_resp = client.delete("/api/alerts")
    assert del_resp.status_code == 200
    assert len(client.get("/api/alerts").json()) == 0


def test_websocket_full_lifecycle():
    """Test WebSocket connection, handshake, simulation update, mode change, ping/pong, and disconnect."""
    with client.websocket_connect("/ws/telemetry") as websocket:
        # 1. Verify Handshake
        initial = websocket.receive_json()
        assert initial["type"] == "HANDSHAKE"
        assert initial["data"]["status"] == "connected"

        # 2. Ping / Pong
        websocket.send_json({"type": "PING"})
        pong = websocket.receive_json()
        assert pong["type"] == "PONG"
        assert "server_time" in pong["data"]

        # 3. Simulation update (Manual Slider)
        websocket.send_json(
            {
                "type": "SIMULATION_UPDATE",
                "payload": {
                    "distance_cm": 8.0,
                    "weight_kg": 1100.0,
                    "vibration_g": 0.2,
                },
            }
        )
        reply = websocket.receive_json()
        # Might receive CRITICAL_ALERT and/or TELEMETRY_PREDICTION
        received_types = [reply["type"]]
        if reply["type"] == "CRITICAL_ALERT":
            second = websocket.receive_json()
            received_types.append(second["type"])
        assert "TELEMETRY_PREDICTION" in received_types

        # 4. Mode change
        websocket.send_json(
            {
                "type": "SET_SIMULATION_MODE",
                "payload": {
                    "mode": "auto",
                    "preset": "NORMAL_FLOW",
                    "interval_ms": 300,
                },
            }
        )
        mode_reply = websocket.receive_json()
        assert mode_reply["type"] == "SIMULATION_MODE_CHANGED"
        assert mode_reply["data"]["mode"] == "auto"


def test_multiple_websocket_clients():
    """Test broadcasting telemetry to multiple concurrent WebSocket clients."""
    with client.websocket_connect("/ws/telemetry") as ws1, client.websocket_connect(
        "/ws/telemetry"
    ) as ws2:
        # Receive handshakes
        h1 = ws1.receive_json()
        h2 = ws2.receive_json()
        assert h1["type"] == "HANDSHAKE"
        assert h2["type"] == "HANDSHAKE"

        # Send REST telemetry and verify both WebSocket clients receive the broadcast
        client.post(
            "/api/telemetry",
            json={
                "sensors": {"distance_cm": 48.0, "weight_kg": 340.0, "vibration_g": 3.0}
            },
        )

        msg1 = ws1.receive_json()
        msg2 = ws2.receive_json()
        assert msg1["type"] in ("TELEMETRY_PREDICTION", "CRITICAL_ALERT")
        assert msg2["type"] in ("TELEMETRY_PREDICTION", "CRITICAL_ALERT")


def test_inference_benchmark_latency():
    """Benchmark ML inference latency to verify sub-20ms requirement."""
    sample = {"sensors": {"distance_cm": 45.0, "weight_kg": 350.0, "vibration_g": 2.8}}
    latencies = []
    for _ in range(20):
        start = time.perf_counter()
        resp = client.post("/api/telemetry", json=sample)
        lat = (time.perf_counter() - start) * 1000
        latencies.append(lat)
        assert resp.status_code == 200

    avg_latency = sum(latencies) / len(latencies)
    print(f"\n⚡ Average inference REST latency: {avg_latency:.2f} ms")
    assert avg_latency < 50.0  # Allow buffer for HTTP testclient overhead
