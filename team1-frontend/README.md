# 🖥️ Team 1: Frontend (UI/UX & Simulation GUI)

**Sub-Team**: Frontend & SCADA Visualization Engineers (Engineers 1 & 2)  
**Core Deliverables**:
1. Industrial-grade SCADA web dashboard (`index.html`).
2. High-performance Cyber-Industrial dark theme with glassmorphism & dynamic glowing borders (`css/styles.css`).
3. Manual simulation sliders (Distance, Weight, Vibration, Flow Rate) & preset scenarios (`js/simulation_panel.js`).
4. Real-time multi-axis time-series charts & Chute Digital Twin animated cross-section (`js/charts.js`).
5. WebSocket client with auto-reconnect (`js/websocket_client.js`).
6. Web Audio API alarm synthesizer and event dispatcher (`js/app.js`).

---

## 🎨 Design & Interaction Features
- **Chute Digital Twin**: Live visual cross-section illustrating raw material bed accumulation level ($5\%-95\%$) dynamically coupled to Ultrasonic clearance and Load Cell mass.
- **Glowing Status Banner**: Dynamic color-coded alerts (🟢 Normal, 🟡 Buildup Warning, 🔴 Critical Blockage, ⚡ Anomaly).
- **Audio-Visual Alarm**: Toggleable Web Audio API sound generator for critical blockage alerts.
- **Preset Injector**: Instantaneous testing of realistic industrial failure scenarios.

---

## 🚀 Running the Frontend
When the FastAPI backend is running (`python3 team2-backend/main.py`), the frontend is served directly on:
```
http://localhost:8000
```
Alternatively, open `team1-frontend/index.html` directly in any browser.

