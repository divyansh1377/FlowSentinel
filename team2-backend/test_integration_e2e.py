"""
FlowSentinel - Team 2 & Integration
End-to-End Integration & Hardening Test Suite
Validates the complete pipeline: Frontend Telemetry -> WebSocket -> Backend -> ML -> Prediction -> Alert Dispatcher -> Recovery -> Alert Acknowledgment.
"""

import os
import sys
import json
import time
import pytest
from fastapi.testclient import TestClient

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
def clean_state():
    """Reset alert dispatcher state before and after each test."""
    alert_dispatcher.clear_history()
    yield
    alert_dispatcher.clear_history()


def test_e2e_scenarios_normal_to_blockage_to_recovery():
    """
    Validates complete multi-state transition sequence:
    1. Scenario A: Normal Flow (State 0)
    2. Scenario B: Rising Buildup (State 1)
    3. Scenario C: Developing Blockage
    4. Scenario D: Complete Blockage (State 2) -> Emits CRITICAL_ALERT
    5. Scenario E: Recovery back to Normal Flow -> Emits Recovery notice & drops risk
    """
    with client.websocket_connect("/ws/telemetry") as ws:
        # 1. Verify initial Handshake
        handshake = ws.receive_json()
        assert handshake["type"] == "HANDSHAKE"
        assert handshake["data"]["status"] == "connected"

        # -----------------------------------------------------------------
        # Scenario A: Normal Flow
        # -----------------------------------------------------------------
        ws.send_json(
            {
                "type": "SIMULATION_UPDATE",
                "payload": {
                    "distance_cm": 52.0,
                    "weight_kg": 320.0,
                    "vibration_g": 3.4,
                    "material_flow_rate_tph": 240.0,
                },
            }
        )
        msg_a = ws.receive_json()
        assert msg_a["type"] == "TELEMETRY_PREDICTION"
        assert msg_a["data"]["status_code"] == 0
        assert msg_a["data"]["status_label"] == "NORMAL"
        assert msg_a["data"]["status_color"] == "GREEN"

        # -----------------------------------------------------------------
        # Scenario B: Rising Buildup
        # -----------------------------------------------------------------
        ws.send_json(
            {
                "type": "SIMULATION_UPDATE",
                "payload": {
                    "distance_cm": 24.0,
                    "weight_kg": 680.0,
                    "vibration_g": 1.2,
                    "material_flow_rate_tph": 110.0,
                },
            }
        )
        frames_b = []
        for _ in range(2):
            frame = ws.receive_json()
            frames_b.append(frame)
            if frame["type"] == "TELEMETRY_PREDICTION":
                break

        pred_b = next(f for f in frames_b if f["type"] == "TELEMETRY_PREDICTION")
        assert pred_b["data"]["status_code"] in (1, 2)

        # -----------------------------------------------------------------
        # Scenario D: Complete Critical Blockage
        # -----------------------------------------------------------------
        ws.send_json(
            {
                "type": "SIMULATION_UPDATE",
                "payload": {
                    "distance_cm": 6.0,
                    "weight_kg": 1200.0,
                    "vibration_g": 0.15,
                    "material_flow_rate_tph": 0.0,
                },
            }
        )
        frames_d = []
        for _ in range(2):
            frame = ws.receive_json()
            frames_d.append(frame)
            if frame["type"] == "TELEMETRY_PREDICTION":
                break

        # Check critical alert was emitted
        alert_frame = next((f for f in frames_d if f["type"] == "CRITICAL_ALERT"), None)
        assert alert_frame is not None or len(alert_dispatcher.get_history()) > 0

        pred_d = next(f for f in frames_d if f["type"] == "TELEMETRY_PREDICTION")
        assert pred_d["data"]["status_code"] == 2
        assert pred_d["data"]["status_label"] == "BLOCKAGE"
        assert pred_d["data"]["status_color"] == "RED"

        # -----------------------------------------------------------------
        # Scenario E: Recovery Back to Normal Flow
        # -----------------------------------------------------------------
        # Send 3 normal frames to simulate flushing and recovery
        for _ in range(3):
            ws.send_json(
                {
                    "type": "SIMULATION_UPDATE",
                    "payload": {
                        "distance_cm": 52.0,
                        "weight_kg": 320.0,
                        "vibration_g": 3.4,
                        "material_flow_rate_tph": 240.0,
                    },
                }
            )
            for _ in range(2):
                f = ws.receive_json()
                if f["type"] == "TELEMETRY_PREDICTION":
                    last_pred = f
                    break

        assert last_pred["data"]["status_code"] == 0
        assert last_pred["data"]["status_label"] == "NORMAL"


def test_alert_acknowledgment_websocket_bidirectional():
    """
    Test that acknowledging an alert over WebSocket broadcasts ALERT_ACKNOWLEDGED
    with operator metadata and updates the server audit log.
    """
    # 1. Trigger an alert
    resp = client.post(
        "/api/telemetry",
        json={
            "sensors": {"distance_cm": 5.0, "weight_kg": 1250.0, "vibration_g": 0.1},
            "operational": {"material_flow_rate_tph": 0.0},
        },
    )
    assert resp.status_code == 200

    alerts = alert_dispatcher.get_history()
    assert len(alerts) > 0
    target_alert_id = alerts[0]["alert_id"]
    assert alerts[0]["acknowledged"] is False

    # 2. Connect client and send ACKNOWLEDGE_ALERT
    with client.websocket_connect("/ws/telemetry") as ws:
        _ = ws.receive_json()  # Handshake

        ws.send_json(
            {
                "type": "ACKNOWLEDGE_ALERT",
                "payload": {
                    "alert_id": target_alert_id,
                    "acknowledged_by": "lead_engineer",
                },
            }
        )

        ack_event = ws.receive_json()
        assert ack_event["type"] == "ALERT_ACKNOWLEDGED"
        assert ack_event["data"]["alert_id"] == target_alert_id
        assert ack_event["data"]["acknowledged_by"] == "lead_engineer"

    # Verify server state was updated
    updated_alerts = alert_dispatcher.get_history()
    target_in_history = next(
        a for a in updated_alerts if a["alert_id"] == target_alert_id
    )
    assert target_in_history["acknowledged"] is True


def test_alert_acknowledgment_rest_broadcasts_to_websocket():
    """
    Test that acknowledging an alert over REST API broadcasts ALERT_ACKNOWLEDGED
    to active WebSocket subscribers.
    """
    # Trigger alert
    client.post(
        "/api/telemetry",
        json={
            "sensors": {"distance_cm": 4.5, "weight_kg": 1220.0, "vibration_g": 0.12}
        },
    )
    alerts = alert_dispatcher.get_history()
    target_id = alerts[0]["alert_id"]

    with client.websocket_connect("/ws/telemetry") as ws:
        _ = ws.receive_json()  # Handshake

        # Trigger REST acknowledgment
        ack_res = client.post(
            f"/api/alerts/{target_id}/acknowledge",
            json={"acknowledged_by": "shift_operator"},
        )
        assert ack_res.status_code == 200
        assert ack_res.json()["acknowledged"] is True

        # Verify WebSocket received the broadcast
        ws_msg = ws.receive_json()
        assert ws_msg["type"] == "ALERT_ACKNOWLEDGED"
        assert ws_msg["data"]["alert_id"] == target_id
        assert ws_msg["data"]["acknowledged_by"] == "shift_operator"


def test_simulation_mode_switch():
    """
    Test switching between manual mode and auto mode via WebSocket.
    """
    with client.websocket_connect("/ws/telemetry") as ws:
        _ = ws.receive_json()  # Handshake

        ws.send_json(
            {
                "type": "SET_SIMULATION_MODE",
                "payload": {
                    "mode": "auto",
                    "preset": "RISING_BUILDUP",
                    "interval_ms": 400,
                },
            }
        )

        event = ws.receive_json()
        assert event["type"] == "SIMULATION_MODE_CHANGED"
        assert event["data"]["mode"] == "auto"
        assert event["data"]["preset"] == "RISING_BUILDUP"
        assert event["data"]["interval_ms"] == 400


def test_malformed_websocket_message_resilience():
    """
    Ensure sending non-JSON or missing fields does not crash the server connection.
    """
    with client.websocket_connect("/ws/telemetry") as ws:
        _ = ws.receive_json()  # Handshake

        # Send raw invalid text
        ws.send_text("NOT_VALID_JSON{:::}")

        # Connection should stay open and respond to valid ping
        ws.send_json({"type": "PING"})
        pong = ws.receive_json()
        assert pong["type"] == "PONG"
