# 📡 FlowSentinel: Official API Contract & Telemetry Specifications

Version: `v1.0.0`  
Protocol: `REST (HTTP/1.1 or HTTP/2)` + `WebSocket (RFC 6455)`  
Default Backend Port: `8000` (e.g. `http://localhost:8000` and `ws://localhost:8000/ws/telemetry`)

---

## 1. Data Schema Definitions

### 1.1 Ingestion / Simulation Telemetry Payload (`TelemetryPayload`)
Sent by **Team 1 (Frontend)** or physical IoT gateways to **Team 2 (Backend)**.

```json
{
  "timestamp": "2026-09-12T12:00:00.000Z",
  "chute_id": "CHUTE_BLAST_FURNACE_01",
  "sensors": {
    "distance_cm": 45.2,
    "weight_kg": 340.5,
    "vibration_g": 2.85,
    "vibration_x": 1.2,
    "vibration_y": 1.8,
    "vibration_z": 2.1
  },
  "operational": {
    "material_flow_rate_tph": 180.0,
    "feed_conveyor_speed_mps": 2.5
  },
  "simulation_flags": {
    "is_simulated": true,
    "noise_injected": false,
    "preset_scenario": "NORMAL_FLOW"
  }
}
```

#### Field Constraints & Units:
| Field | Type | Range / Format | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | string (ISO-8601) | e.g. `YYYY-MM-DDTHH:MM:SS.sssZ` | Timestamp of measurement |
| `chute_id` | string | Alphanumeric (e.g. `CHUTE_01`) | Unique identifier of monitored chute |
| `distance_cm` | float | `0.0` to `200.0` cm | Ultrasonic sensor reading to material bed |
| `weight_kg` | float | `0.0` to `2000.0` kg | HX711 Load Cell sensor weight |
| `vibration_g` | float | `0.0` to `15.0` G (RMS) | MPU6050 3-Axis total acceleration RMS |
| `vibration_x/y/z` | float | `-10.0` to `10.0` G | Optional individual tri-axial accelerations |
| `material_flow_rate_tph` | float | `0.0` to `600.0` Tons/hr | Estimated instantaneous throughput |
| `feed_conveyor_speed_mps` | float | `0.0` to `5.0` m/s | Upstream feeder belt speed |

---

### 1.2 Model Inference & Prediction Response (`PredictionResponse`)
Returned by **Team 2 (Backend)** to **Team 1 (Frontend)** via WebSocket or REST.

```json
{
  "timestamp": "2026-09-12T12:00:00.045Z",
  "chute_id": "CHUTE_BLAST_FURNACE_01",
  "status_code": 0,
  "status_label": "NORMAL",
  "status_color": "GREEN",
  "confidence_score": 0.965,
  "probabilities": {
    "normal": 0.965,
    "warning": 0.030,
    "blockage": 0.005
  },
  "anomaly_detection": {
    "is_anomaly": false,
    "anomaly_score": 0.18,
    "isolation_forest_raw": 0.62
  },
  "root_cause_analysis": "Normal material velocity and vibration signature.",
  "recommended_action": "No action required. Maintain current feed rate.",
  "telemetry_echo": {
    "distance_cm": 45.2,
    "weight_kg": 340.5,
    "vibration_g": 2.85
  },
  "latency_ms": 12.4
}
```

#### Status Codes & Class Meanings:
- **`0` (`NORMAL` / 🟢 GREEN)**: Steady-state dynamic flow, regular impact vibrations (1.5–4.5 G), clearance intact (>35 cm), normal load (<500 kg).
- **`1` (`WARNING` / 🟡 YELLOW)**: Partial buildup or sluggish flow, dampening vibrations, rising bed height (15–35 cm clearance), elevated weight (500–800 kg).
- **`2` (`BLOCKAGE` / 🔴 RED)**: Choke/Plug event, stagnant ore bed (<15 cm clearance), overloaded chute (>800 kg), dead vibration signature (<0.5 G) or erratic surge.
- **Anomaly Flag (`is_anomaly: true`)**: Sensor malfunction, mechanical resonance spike, or out-of-distribution physical behavior identified by Isolation Forest.

---

## 2. REST Endpoints

### 2.1 System Health & Metadata
- **`GET /api/status`**
  - **Response `200 OK`**:
    ```json
    {
      "status": "healthy",
      "version": "1.0.0",
      "ml_model_loaded": true,
      "models": {
        "random_forest": "Trained (v1.0)",
        "isolation_forest": "Trained (v1.0)"
      },
      "active_websocket_clients": 2,
      "uptime_seconds": 1845.2
    }
    ```

### 2.2 Telemetry Ingestion (One-off / REST Prediction)
- **`POST /api/telemetry`**
  - **Request Body**: `TelemetryPayload`
  - **Response `200 OK`**: `PredictionResponse`

### 2.3 Preset Scenarios
- **`GET /api/presets`**
  - **Response `200 OK`**:
    ```json
    {
      "NORMAL_FLOW": { "distance_cm": 50.0, "weight_kg": 300.0, "vibration_g": 3.0 },
      "RISING_BUILDUP": { "distance_cm": 25.0, "weight_kg": 650.0, "vibration_g": 1.2 },
      "COMPLETE_BLOCKAGE": { "distance_cm": 5.0, "weight_kg": 1200.0, "vibration_g": 0.15 },
      "EMPTY_CHUTE": { "distance_cm": 110.0, "weight_kg": 0.0, "vibration_g": 0.1 },
      "ERRATIC_SENSOR_SPIKE": { "distance_cm": 5.0, "weight_kg": 20.0, "vibration_g": 12.5 }
    }
    ```

### 2.4 Alert History
- **`GET /api/alerts?limit=50`**
  - **Response `200 OK`**: Array of historical triggered alerts with timestamps and severities.

---

## 3. WebSocket Real-Time Channel

### 3.1 Endpoint
`ws://localhost:8000/ws/telemetry`

### 3.2 Client -> Server Messages
The frontend simulation UI can send two message types:

1. **Manual Slider Telemetry Update**:
   ```json
   {
     "type": "SIMULATION_UPDATE",
     "payload": {
       "distance_cm": 42.0,
       "weight_kg": 350.0,
       "vibration_g": 3.1,
       "material_flow_rate_tph": 200.0
     }
   }
   ```

2. **Auto-Simulation Mode Switch**:
   ```json
   {
     "type": "SET_SIMULATION_MODE",
     "payload": {
       "mode": "auto",       // "auto" or "manual"
       "preset": "NORMAL_FLOW",
       "interval_ms": 500
     }
   }
   ```

### 3.3 Server -> Client Messages
1. **Live Inference Broadcast**:
   ```json
   {
     "type": "TELEMETRY_PREDICTION",
     "data": { ...PredictionResponse... }
   }
   ```

2. **Immediate Alert Notification**:
   ```json
   {
     "type": "CRITICAL_ALERT",
     "data": {
       "alert_id": "ALT-98231",
       "level": "CRITICAL",
       "title": "CHUTE CHOKE IMMINENT",
       "details": "Weight exceeds 1100kg with severe vibration dampening."
     }
   }
   ```

