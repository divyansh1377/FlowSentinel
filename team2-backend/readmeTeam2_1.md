# ⚡ Team 2 (Backend & Architecture) - Progress Report

**Engineer:** Engineer 4
**Phase Status:** Phase 1, 2, and 3 Completed

This document outlines the backend architecture, real-time alerting, and WebSocket pipeline implementations completed for the FlowSentinel project.

---

## 🎯 Completed Deliverables

### 1. Data Validation & API Contract (`schemas.py`)
- Strictly implemented Pydantic models mapping to `API_CONTRACT.md`.
- Built robust validation rules preventing invalid telemetry (e.g., negative distances, out-of-bounds weight).
- Integrated UTC timezone-aware ISO-8601 timestamps for all incoming and outgoing payloads.
- Added schemas for alert acknowledgement (`AlertAcknowledgeRequest`, `AlertAcknowledgeResponse`).

### 2. Stateful Alert Dispatcher (`alert_dispatcher.py`)
- **Hysteresis & Debouncing:** Implemented a stateful engine with a configurable debounce window (1.5 seconds) to prevent rapid alarm flickering between `WARNING` and `BLOCKAGE` states.
- **Immediate Critical Triggers:** Hard-coded bypasses to immediately trigger an alert if a `CRITICAL` blockage (state 2) or an unsupervised sensor anomaly occurs.
- **Event Audit Log:** Built a bounded in-memory queue to track historical alerts.
- **Acknowledgement Flow:** Added mechanisms for operators to acknowledge alerts and clear the history log.

### 3. Async WebSocket Hub (`websocket_manager.py`)
- Engineered a thread-safe, non-blocking WebSocket connection manager.
- Features automatic tracking of active clients and graceful pruning of dead/dropped connections.
- Implemented `broadcast_json` to push live ML inferences and critical alerts to all connected frontend UI dashboards simultaneously.
- Added `PING/PONG` heartbeat support to maintain connection stability.

### 4. Background Auto-Simulator (`simulator_service.py`)
- Integrated with Team 3's physics data generator to provide a continuous telemetry stream.
- Supports runtime switching between predefined scenarios (`NORMAL_FLOW`, `RISING_BUILDUP`, `COMPLETE_BLOCKAGE`, `ERRATIC_SENSOR_SPIKE`).

### 5. Integration Test Suite (`test_backend.py`)
- Wrote an exhaustive `pytest` suite ensuring 100% endpoint reliability.
- **Benchmarks:** Confirmed ML inference + REST overhead operates well under the 50ms requirement (averaging ~1-5ms per request).
- Covers WebSocket lifecycle, concurrent multi-client broadcasting, and alert acknowledgement edge cases.

### 6. Containerization & Deployment
- Built a lightweight `Dockerfile` for the Team 2 backend based on `python:3.11-slim`.
- Configured a root `docker-compose.yml` to orchestrate the backend with health checks and environment variables.

---

## 🚀 How to Run & Verify

### Run the Backend Tests
```bash
# Activate the virtual environment
source ../.venv/bin/activate

# Execute the test suite
pytest test_backend.py -v
```

### Start the FlowSentinel System
From the repository root, you can launch the entire system using the master script:
```bash
cd ..
./start_all.sh
```
The FastAPI documentation (Swagger UI) will be available at: http://localhost:8000/docs

