# ⚡ Team 2: Backend, WebSockets & Server Architecture

**Sub-Team**: Backend & Server Architecture Engineers (Engineers 3 & 4)  
**Core Deliverables**:
1. High-throughput async FastAPI application (`main.py`).
2. Robust bidirectional WebSocket Hub (`websocket_manager.py`).
3. Stateful Alert Engine with Hysteresis & Debounce (`alert_dispatcher.py`).
4. Background Live Telemetry Streaming Daemon (`simulator_service.py`).
5. Integration Test Suite (`test_backend.py`).

---

## 🔌 API Endpoints Reference

### REST Endpoints:
- `GET /api/status` - Live backend health, uptime, active websocket counts, and ML model status.
- `POST /api/telemetry` - Direct ingestion of telemetry payload and instantaneous prediction.
- `GET /api/presets` - Pre-configured industrial simulation scenarios.
- `GET /api/alerts` - Historical audit log of triggered alerts.
- `POST /api/retrain` - Hot re-training and re-loading of ML models into memory.

### WebSocket Hub:
- `ws://localhost:8000/ws/telemetry` - Streaming bi-directional pipeline for frontend dashboard.

---

## 🏃 Running the Server & Tests

### Start the Backend Server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Backend Tests:
```bash
pytest test_backend.py -v
```

