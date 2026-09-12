# �️ FlowSentinel: Frontend Architecture (Team 1 & Team 2 Guide)

Official Product Name: **FlowSentinel**  
Tagline: *Predictive Chute Blockage Management*

---

## 👥 Frontend Team Allocation

### Frontend Team Member 1 (Owner of Shared Core & Pages 1-4)
- **`index.html`** (`/`): Home / Dashboard (Hero, 4 KPI Cards, Live Sensors, Risk vs Time Chart, Chute Twin, Quick Actions, Recent Events).
- **`monitoring.html`** (`/monitoring`): Live Monitoring (ESP32 Gateway Link, Dominant Risk Metric, Multi-Sensor Time-Series, Acknowledged Alert Feed).
- **`simulation.html`** (`/simulation`): Simulation Engine (5 Simulation Modes, Fault Injections, Sliders, 4 Scenarios, Real-Time Physics Output).
- **`manual.html`** (`/manual`): Manual Prediction Studio (Hypothetical Sliders, Presets, Instant Prediction Button, Feature Contribution Weights).
- **Design System & Shell**:
  - `css/styles.css`: Complete centralized design tokens, buttons, cards, status badges, and animations.
  - `js/navigation.js`: Global responsive sidebar and header injector.
  - `js/state.js`: Centralized reactive state store and risk calculation engine.
  - `js/api.js`: REST API client for `/api/*` endpoints.
  - `js/charts.js`: Reusable Chart.js multi-sensor and risk time-series engine.
  - `js/websocket_client.js`: WebSocket client with automatic reconnection and JSON streaming.

### Frontend Team Member 2 (Owner of Pages 5-8)
- **`training.html`** (`/training`): Model Training & Dataset Management.
- **`analytics.html`** (`/analytics`): Analytics & Confusion Matrix / Sensor Ablation.
- **`system.html`** (`/system`): Hardware Diagnostics & Bus Health.
- **`about.html`** (`/about`): System Architecture & Engineering Documentation.

---

## 🎨 Global Design System Reference

### Risk & Status Classes
- Normal (0–30%): `.badge.normal`, `.kpi-card.normal`, `.status-banner.normal`, `var(--fs-status-normal)` (`#10b981`)
- Warning (30–60%): `.badge.warning`, `.kpi-card.warning`, `.status-banner.warning`, `var(--fs-status-warning)` (`#f59e0b`)
- High (60–80%): `.badge.high`, `.kpi-card.high`, `.status-banner.high`, `var(--fs-status-high)` (`#f97316`)
- Critical (80–100%): `.badge.critical`, `.kpi-card.critical`, `.status-banner.critical`, `var(--fs-status-critical)` (`#ef4444`)
- Anomaly: `.badge.anomaly`, `var(--fs-status-anomaly)` (`#a855f7`)

### Button Variants
- `.btn.btn-primary`
- `.btn.btn-secondary`
- `.btn.btn-danger`
- `.btn.btn-success`
- `.btn.btn-ghost`
- Add `.is-loading` class to any button for a CSS spinner overlay.
