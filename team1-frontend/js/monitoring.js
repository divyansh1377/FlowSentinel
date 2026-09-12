/**
 * FlowSentinel - Live Monitoring Controller
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

document.addEventListener("DOMContentLoaded", async () => {
  console.log("📡 [FlowSentinel] Launching Live Monitoring View...");

  // 1. Initialize Navigation
  const nav = new FlowSentinelNavigation("/monitoring");

  // 2. Initialize Telemetry Multi-Sensor Chart
  fsCharts.initTelemetryChart("telemetryChart");

  // Chart control bindings
  const btnPause = document.getElementById("btn-mon-pause");
  if (btnPause) {
    btnPause.addEventListener("click", () => {
      const paused = fsCharts.togglePause();
      btnPause.textContent = paused ? "▶️" : "⏸️";
      btnPause.title = paused ? "Resume Stream" : "Pause Stream";
    });
  }

  const btnClear = document.getElementById("btn-mon-clear");
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      fsCharts.clearHistory();
    });
  }

  // 3. Connect / Disconnect button mock
  const btnToggleConnect = document.getElementById("btn-toggle-connect");
  let isHardwareConnected = true;
  if (btnToggleConnect) {
    btnToggleConnect.addEventListener("click", () => {
      isHardwareConnected = !isHardwareConnected;
      const statusBadge = document.getElementById("esp-status-badge");
      const statusText = document.getElementById("esp-status-text");

      if (isHardwareConnected) {
        btnToggleConnect.textContent = "Disconnect";
        btnToggleConnect.className = "btn btn-danger";
        if (statusBadge) statusBadge.className = "badge online";
        if (statusText) statusText.textContent = "ESP32 CONNECTED";
      } else {
        btnToggleConnect.textContent = "Connect ESP32";
        btnToggleConnect.className = "btn btn-success";
        if (statusBadge) statusBadge.className = "badge offline";
        if (statusText) statusText.textContent = "DISCONNECTED";
      }
    });
  }

  const btnRefreshPorts = document.getElementById("btn-refresh-ports");
  if (btnRefreshPorts) {
    btnRefreshPorts.addEventListener("click", () => {
      btnRefreshPorts.classList.add("is-loading");
      setTimeout(() => {
        btnRefreshPorts.classList.remove("is-loading");
      }, 600);
    });
  }

  // 4. State Subscriber
  fsState.subscribe((state) => {
    updateMonitoringUI(state);
  });

  // 5. Connect WebSocket client
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

  function updateMonitoringUI(state) {
    const pred = state.prediction;
    const telem = state.telemetry;

    // Dominant Risk Metric
    const monRiskVal = document.getElementById("mon-risk-value");
    const monRiskLevelBadge = document.getElementById("mon-risk-level-badge");
    const predStateBadge = document.getElementById("pred-state-badge");
    const monConfidence = document.getElementById("mon-confidence");
    const monAnomaly = document.getElementById("mon-anomaly");
    const monLatency = document.getElementById("mon-latency");
    const monProbBar = document.getElementById("mon-prob-bar");
    const probBreakdownText = document.getElementById("prob-breakdown-text");

    if (monRiskVal) {
      monRiskVal.textContent = `${pred.risk_percentage.toFixed(1)}%`;
      monRiskVal.style.color = `var(--fs-status-${pred.risk_level.toLowerCase()})`;
    }

    if (monRiskLevelBadge) {
      monRiskLevelBadge.className = `badge ${pred.risk_level.toLowerCase()}`;
      monRiskLevelBadge.textContent = `RISK: ${pred.risk_level}`;
    }

    if (predStateBadge) {
      predStateBadge.className = `badge ${pred.risk_level.toLowerCase()}`;
      predStateBadge.textContent = `STATE ${pred.status_code}: ${pred.status_label}`;
    }

    if (monConfidence) monConfidence.textContent = `${(pred.confidence_score * 100).toFixed(1)}%`;
    if (monLatency) monLatency.textContent = `${pred.latency_ms?.toFixed(1) || "<1"} ms`;

    if (monAnomaly) {
      const isAnom = pred.anomaly_detection?.is_anomaly;
      monAnomaly.textContent = isAnom ? `0.88 (ANOMALY)` : `0.12 (NORMAL)`;
      monAnomaly.style.color = isAnom ? `var(--fs-status-anomaly)` : `var(--fs-status-normal)`;
    }

    const probs = pred.probabilities || { normal: 0.965, warning: 0.03, blockage: 0.005 };
    if (probBreakdownText) {
      probBreakdownText.textContent = `Normal: ${(probs.normal * 100).toFixed(1)}% | Warning: ${(probs.warning * 100).toFixed(1)}% | Blockage: ${(probs.blockage * 100).toFixed(1)}%`;
    }
    if (monProbBar) {
      monProbBar.className = `progress-fill ${pred.risk_level.toLowerCase()}`;
      monProbBar.style.width = `${Math.max(10, pred.risk_percentage)}%`;
    }

    // Sensor Readings
    const monDist = document.getElementById("mon-dist-val");
    const monWeight = document.getElementById("mon-weight-val");
    const monVib = document.getElementById("mon-vib-val");
    const monCurrent = document.getElementById("mon-current-val");

    if (monDist) monDist.textContent = telem.distance_cm?.toFixed(1) || "50.0";
    if (monWeight) monWeight.textContent = telem.weight_kg?.toFixed(0) || "300";
    if (monVib) monVib.textContent = telem.vibration_g?.toFixed(2) || "3.20";
    if (monCurrent) monCurrent.textContent = telem.motor_current_a?.toFixed(1) || "42.0";

    const nowStr = new Date().toLocaleTimeString();
    ["mon-dist-time", "mon-weight-time", "mon-vib-time", "mon-current-time"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = nowStr;
    });

    // Update Telemetry Chart
    fsCharts.updateTelemetryData(
      telem.distance_cm || 50,
      telem.weight_kg || 300,
      telem.vibration_g || 3,
      telem.motor_current_a || 40
    );

    // Update Alerts Feed with Acknowledge functionality
    const alertCont = document.getElementById("mon-alert-container");
    if (alertCont && state.alerts.length > 0) {
      alertCont.innerHTML = state.alerts.slice(0, 10).map((a, idx) => `
        <div class="alert-item ${a.severity?.toLowerCase() || 'warning'}" id="alert-item-${idx}">
          <div class="alert-item-header">
            <span>${new Date(a.timestamp).toLocaleTimeString()}</span>
            <span>${a.alert_id || 'ALT-01'}</span>
          </div>
          <div class="alert-item-title">${a.title || 'System Alert'}</div>
          <div style="font-size: 0.75rem; color: var(--fs-text-secondary); display: flex; justify-content: space-between; align-items: center; margin-top: 0.35rem;">
            <span>${a.message || ''}</span>
            <button class="btn btn-ghost" onclick="this.closest('.alert-item').style.opacity='0.4'; this.textContent='ACKNOWLEDGED'; this.disabled=true;" style="padding: 2px 8px; font-size: 0.7rem;">
              Acknowledge
            </button>
          </div>
        </div>
      `).join('');
    }
  }
});

