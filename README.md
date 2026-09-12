# FlowSentinel: AI-Powered Intelligent Chute Blockage Detection System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![WebSockets](https://img.shields.io/badge/RealTime-WebSockets-010101.svg?logo=socketdotio&logoColor=white)](https://websockets.readthedocs.io)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

> **FlowSentinel** is a mission-critical AI-driven monitoring and early-warning detection system for industrial transfer chutes and conveyor drop points in high-stress environments such as steel manufacturing plants.

---

## 🎯 System Architecture Overview

FlowSentinel continuously synthesizes and processes 3 primary sensor signals to detect blockage formations and mechanical anomalies before catastrophic equipment failure occurs:

1. **Ultrasonic Sensor (Distance $d$ cm)**: Measures the air gap above the material stream down to the bed.
2. **HX711 Load Cell (Weight $W$ kg)**: Measures the instantaneous material mass loading the chute structure.
3. **MPU6050 3-Axis Accelerometer (Vibration $G$ RMS)**: Measures kinetic impact oscillations and flow energy.

```
                      +------------------------------------+
                      |     Team 1: Frontend SCADA UI      |
                      |  • Manual Sliders & Presets        |
                      |  • Real-Time Charts & Chute Twin   |
                      |  • Audio-Visual Alarm Dispatcher   |
                      +-----------------+------------------+
                                        |  WebSocket (Bidirectional)
                                        v
                      +------------------------------------+
                      |      Team 2: FastAPI Backend       |
                      |  • /ws/telemetry Real-Time Hub     |
                      |  • Alert Dispatcher with Debounce  |
                      |  • Auto-Streamer Background Daemon |
                      +-----------------+------------------+
                                        |  In-Memory Inference (<15ms)
                                        v
                      +------------------------------------+
                      |   Team 3: ML & Physics Engine      |
                      |  • Physics Synthetic Generator     |
                      |  • Isolation Forest (Anomaly)      |
                      |  • Random Forest (0/1/2 Classify)  |
                      +------------------------------------+
```

---

## 👥 6-Person Team Organization & Directory Layout

The repository is modularly structured to enable parallel development with **zero merge conflicts**:

```
FlowSentinel/
├── PROJECT_PLAN.md             # 6-Person, 3-Phase Project Roadmap & RACI Matrix
├── API_CONTRACT.md             # Standardized REST & WebSocket JSON Schemas
├── start_all.sh                # 1-Click Startup Script for Full System
├── requirements.txt            # Unified Python Dependencies
│
├── team3-ml-simulation/        # [Team 3: Engineers 5 & 6] Data Science & Physics
│   ├── data_generator.py       # Physics-based synthetic chute sensor telemetry generator
│   ├── train_models.py         # Trains Isolation Forest & Random Forest models
│   ├── model_pipeline.py       # ChutePredictor inference interface
│   ├── benchmark_ml.py         # Precision/Recall & Latency evaluation
│   ├── export_dataset.py       # CSV dataset exporter
│   └── models/                 # Serialized model weights (.joblib)
│
├── team2-backend/              # [Team 2: Engineers 3 & 4] Server & WebSockets
│   ├── main.py                 # FastAPI application, CORS & static file mounting
│   ├── schemas.py              # Pydantic data validation schemas
│   ├── websocket_manager.py    # Multi-client WebSocket connection hub
│   ├── alert_dispatcher.py     # Stateful alert engine with debounce & hysteresis
│   ├── simulator_service.py    # Background auto-telemetry generator daemon
│   └── test_backend.py         # Integration & unit test suite
│
└── team1-frontend/             # [Team 1: Engineers 1 & 2] UI/UX & Simulation GUI
    ├── index.html              # Modern Dark Industrial SCADA Dashboard
    ├── css/styles.css          # Glassmorphism cyber-industrial styling
    └── js/
        ├── app.js              # Application entrypoint & state orchestrator
        ├── websocket_client.js # WebSocket client with auto-reconnect
        ├── simulation_panel.js # Interactive sliders (Distance, Weight, Vibration)
        └── charts.js           # Live dynamic SCADA charts & Chute visualizer
```

---

## 🚀 Quick Start Instructions

### Prerequisites
- Python 3.9+ installed
- Modern Web Browser (Chrome, Firefox, Safari, Edge)

### 1-Click Automated Launch (Recommended)
Run the automated bootstrap script from the repository root:
```bash
chmod +x start_all.sh
./start_all.sh
```

This script will:
1. Validate or create a Python virtual environment.
2. Install all required dependencies.
3. Automatically train the **Isolation Forest** and **Random Forest** models using the physics engine.
4. Launch the FastAPI server on `http://localhost:8000`.
5. Serve the live interactive SCADA Frontend on `http://localhost:8000` (or open `team1-frontend/index.html`).

---

## 🧪 Testing and Validation

### Run Backend Integration Tests
```bash
pytest team2-backend/test_backend.py -v
```

### Benchmark ML Models
```bash
python3 team3-ml-simulation/benchmark_ml.py
```

---

## 📊 Sensor & Classification Mapping Reference

| Chute State | Ultrasonic ($d$) | Load Cell ($W$) | MPU6050 ($G$ RMS) | ML Classification | Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Flow** | $40 - 70\text{ cm}$ | $200 - 450\text{ kg}$ | $2.0 - 5.0\text{ G}$ | `0` (NORMAL) | Standard continuous operation |
| **Buildup Warning**| $15 - 35\text{ cm}$ | $500 - 800\text{ kg}$ | $0.8 - 1.8\text{ G}$ | `1` (WARNING) | Reduce upstream feeder speed |
| **Critical Blockage**| $< 15\text{ cm}$ | $> 800\text{ kg}$ | $< 0.4\text{ G}$ | `2` (BLOCKAGE) | Immediate conveyor shutdown & alarm |
| **Sensor Anomaly**| Out of bounds | Inconsistent | Unnatural spikes | `ANOMALY DETECTED`| Trigger maintenance diagnostic |
