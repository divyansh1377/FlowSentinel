/**
 * FlowSentinel - Simulation Controller & Physics Engine Integration
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

document.addEventListener("DOMContentLoaded", async () => {
  console.log("🎛️ [FlowSentinel] Launching Simulation Engine...");

  // 1. Initialize Navigation
  const nav = new FlowSentinelNavigation("/simulation");

  // 2. Initialize Telemetry Chart
  fsCharts.initTelemetryChart("telemetryChart");

  // 3. Connect WebSocket client
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  let host = window.location.host;
  if (!host || window.location.protocol === "file:") {
    host = "localhost:8000";
  }
  const wsUrl = `${protocol}//${host}/ws/telemetry`;

  const wsClient = new TelemetryWebSocketClient(
    wsUrl,
    (msg) => {
      const msgType = msg.type;
      const data = msg.data || msg.payload;

      if (msgType === "TELEMETRY_PREDICTION" && data) {
        fsState.updateFromPrediction(data);
      } else if (msgType === "CRITICAL_ALERT" && data) {
        fsState.addAlert(data);
        nav.playAlertBeep(920, 0.4);
      }
    },
    (status) => {
      nav.updateWsStatus(status);
      fsState.setConnectionState(status);
    }
  );

  wsClient.connect();

  // 4. Simulation Panel Controller
  class SimulationEngine {
    constructor() {
      this.mode = "manual";
      this.activePreset = "NORMAL_FLOW";
      this.isRunning = true;
      this.debounceTimer = null;
      this.progressionInterval = null;

      // DOM Sliders
      this.distSlider = document.getElementById("slider-distance");
      this.weightSlider = document.getElementById("slider-weight");
      this.vibSlider = document.getElementById("slider-vibration");
      this.flowSlider = document.getElementById("slider-flow");

      this.distVal = document.getElementById("val-distance");
      this.weightVal = document.getElementById("val-weight");
      this.vibVal = document.getElementById("val-vibration");
      this.flowVal = document.getElementById("val-flow");

      this.presets = {
        NORMAL_FLOW: { distance: 52.0, weight: 320.0, vibration: 3.4, flow: 240.0 },
        RISING_BUILDUP: { distance: 28.0, weight: 620.0, vibration: 1.4, flow: 140.0 },
        DEVELOPING_BLOCKAGE: { distance: 16.0, weight: 820.0, vibration: 0.65, flow: 60.0 },
        COMPLETE_BLOCKAGE: { distance: 6.0, weight: 1180.0, vibration: 0.15, flow: 0.0 }
      };

      this.initEvents();
    }

    initEvents() {
      // Slider Input Handling
      const sliders = [
        { el: this.distSlider, valEl: this.distVal, unit: " cm" },
        { el: this.weightSlider, valEl: this.weightVal, unit: " kg" },
        { el: this.vibSlider, valEl: this.vibVal, unit: " G" },
        { el: this.flowSlider, valEl: this.flowVal, unit: " TPH" }
      ];

      sliders.forEach(s => {
        if (s.el) {
          s.el.addEventListener("input", () => {
            s.valEl.textContent = s.el.value + s.unit;
            document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
            this.triggerDebouncedSend();
          });
        }
      });

      // Preset Buttons
      document.querySelectorAll(".btn-preset").forEach(btn => {
        btn.addEventListener("click", () => {
          const presetKey = btn.getAttribute("data-preset");
          this.applyPreset(presetKey);
        });
      });

      // Simulation Modes
      document.querySelectorAll(".sim-mode-card").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".sim-mode-card").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          const modeKey = btn.getAttribute("data-mode");
          this.setSimulationMode(modeKey);
        });
      });

      // Fault Injection Buttons
      document.querySelectorAll(".fault-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const faultType = btn.getAttribute("data-fault");
          this.injectFault(faultType);
        });
      });

      // Simulation Master Controls
      const btnStart = document.getElementById("btn-sim-start");
      const btnPause = document.getElementById("btn-sim-pause");
      const btnReset = document.getElementById("btn-sim-reset");

      if (btnStart) {
        btnStart.addEventListener("click", () => {
          this.isRunning = true;
          document.getElementById("sim-status-pill").className = "badge online";
          document.getElementById("sim-status-pill").textContent = "STATUS: RUNNING (25 FPS)";
          this.sendCurrentState();
        });
      }

      if (btnPause) {
        btnPause.addEventListener("click", () => {
          this.isRunning = false;
          clearInterval(this.progressionInterval);
          document.getElementById("sim-status-pill").className = "badge warning";
          document.getElementById("sim-status-pill").textContent = "STATUS: PAUSED";
        });
      }

      if (btnReset) {
        btnReset.addEventListener("click", () => {
          this.applyPreset("NORMAL_FLOW");
          fsCharts.clearHistory();
        });
      }
    }

    applyPreset(presetKey) {
      if (!this.presets[presetKey]) return;
      this.activePreset = presetKey;
      const p = this.presets[presetKey];

      this.distSlider.value = p.distance;
      this.distVal.textContent = p.distance + " cm";

      this.weightSlider.value = p.weight;
      this.weightVal.textContent = p.weight + " kg";

      this.vibSlider.value = p.vibration;
      this.vibVal.textContent = p.vibration + " G";

      this.flowSlider.value = p.flow;
      this.flowVal.textContent = p.flow + " TPH";

      document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
      const activeBtn = document.querySelector(`.btn-preset[data-preset="${presetKey}"]`);
      if (activeBtn) activeBtn.classList.add("active");

      if (this.mode === "auto") {
        wsClient.setMode("auto", presetKey, 400);
      } else {
        this.sendCurrentState();
      }
    }

    setSimulationMode(modeKey) {
      this.mode = modeKey;
      clearInterval(this.progressionInterval);
      const label = document.getElementById("active-mode-label");
      if (label) label.textContent = `MODE: ${modeKey.toUpperCase()}`;

      if (modeKey === "auto") {
        wsClient.setMode("auto", this.activePreset, 400);
      } else if (modeKey === "progressive") {
        wsClient.setMode("manual");
        this.startProgressiveSimulation();
      } else if (modeKey === "sudden") {
        wsClient.setMode("manual");
        this.applyPreset("COMPLETE_BLOCKAGE");
      } else if (modeKey === "random") {
        wsClient.setMode("manual");
        this.startRandomNoiseSimulation();
      } else {
        wsClient.setMode("manual");
      }
    }

    startProgressiveSimulation() {
      let step = 0;
      this.applyPreset("NORMAL_FLOW");

      this.progressionInterval = setInterval(() => {
        if (!this.isRunning) return;
        step++;
        let curDist = parseFloat(this.distSlider.value);
        let curWeight = parseFloat(this.weightSlider.value);
        let curVib = parseFloat(this.vibSlider.value);

        if (curDist > 8) curDist -= 1.5;
        if (curWeight < 1150) curWeight += 28;
        if (curVib > 0.2) curVib -= 0.08;

        this.distSlider.value = curDist.toFixed(1);
        this.distVal.textContent = curDist.toFixed(1) + " cm";
        this.weightSlider.value = curWeight.toFixed(0);
        this.weightVal.textContent = curWeight.toFixed(0) + " kg";
        this.vibSlider.value = curVib.toFixed(2);
        this.vibVal.textContent = curVib.toFixed(2) + " G";

        this.sendCurrentState();

        if (curDist <= 8 && curWeight >= 1150) {
          clearInterval(this.progressionInterval);
        }
      }, 500);
    }

    startRandomNoiseSimulation() {
      this.progressionInterval = setInterval(() => {
        if (!this.isRunning) return;
        const jitter = (Math.random() - 0.5) * 4;
        const curDist = Math.max(5, Math.min(100, parseFloat(this.distSlider.value) + jitter));
        this.distSlider.value = curDist.toFixed(1);
        this.distVal.textContent = curDist.toFixed(1) + " cm";
        this.sendCurrentState();
      }, 400);
    }

    injectFault(faultType) {
      if (faultType === "dropout") {
        this.distSlider.value = 0;
        this.distVal.textContent = "0.0 cm";
      } else if (faultType === "spike") {
        this.vibSlider.value = 14.5;
        this.vibVal.textContent = "14.50 G";
      } else if (faultType === "stuck") {
        this.vibSlider.value = 0.0;
        this.vibVal.textContent = "0.00 G";
      } else if (faultType === "noise") {
        this.startRandomNoiseSimulation();
      }
      this.sendCurrentState();
    }

    triggerDebouncedSend() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.sendCurrentState();
      }, 40);
    }

    sendCurrentState() {
      if (!this.isRunning) return;
      const payload = {
        distance_cm: parseFloat(this.distSlider.value),
        weight_kg: parseFloat(this.weightSlider.value),
        vibration_g: parseFloat(this.vibSlider.value),
        material_flow_rate_tph: parseFloat(this.flowSlider.value)
      };
      wsClient.sendSimulationUpdate(payload);
    }
  }

  const engine = new SimulationEngine();

  // 5. State subscriber to update UI
  fsState.subscribe((state) => {
    const pred = state.prediction;
    const telem = state.telemetry;

    const riskEl = document.getElementById("sim-metric-risk");
    const stateEl = document.getElementById("sim-metric-state");
    const anomEl = document.getElementById("sim-metric-anomaly");
    const currentEl = document.getElementById("sim-metric-current");
    const respBadge = document.getElementById("sim-response-badge");

    if (riskEl) {
      riskEl.textContent = `${pred.risk_percentage.toFixed(1)}%`;
      riskEl.style.color = `var(--fs-status-${pred.risk_level.toLowerCase()})`;
    }
    if (stateEl) stateEl.textContent = `STATE ${pred.status_code}`;
    if (anomEl) {
      const isAnom = pred.anomaly_detection?.is_anomaly;
      anomEl.textContent = isAnom ? "ANOMALY" : "NORMAL";
      anomEl.style.color = isAnom ? "var(--fs-status-anomaly)" : "var(--fs-status-normal)";
    }
    if (currentEl) currentEl.textContent = `${telem.motor_current_a?.toFixed(1) || 42.5} A`;
    if (respBadge) {
      respBadge.className = `badge ${pred.risk_level.toLowerCase()}`;
      respBadge.textContent = `${pred.status_label} (${pred.latency_ms?.toFixed(1) || "<1"} ms)`;
    }

    // Update Chart & Chute Twin
    fsCharts.updateTelemetryData(
      telem.distance_cm || 50,
      telem.weight_kg || 300,
      telem.vibration_g || 3,
      telem.motor_current_a || 40
    );

    fsCharts.updateChuteDigitalTwin(
      telem.distance_cm || 50,
      telem.weight_kg || 300,
      "sim-chute-bed-level",
      "sim-chute-bed-label"
    );
  });
});
