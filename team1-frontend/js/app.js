/**
 * FlowSentinel - Main Dashboard Orchestrator
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

document.addEventListener("DOMContentLoaded", async () => {
  console.log("🚀 [FlowSentinel] Launching Dashboard Interface...");

  // 1. Initialize Global Navigation & Header
  const nav = new FlowSentinelNavigation("/");

  // 2. Initialize Charts
  fsCharts.initRiskTimeChart("riskTimeChart");

  // Chart Controls
  const btnPause = document.getElementById("btn-chart-pause");
  if (btnPause) {
    btnPause.addEventListener("click", () => {
      const paused = fsCharts.togglePause();
      btnPause.textContent = paused ? "▶️" : "⏸️";
      btnPause.title = paused ? "Resume Chart" : "Pause Chart";
    });
  }

  const btnClear = document.getElementById("btn-chart-clear");
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      fsCharts.clearHistory();
    });
  }

  // 3. Hydrate initial historical alerts from REST API
  try {
    const alerts = await fsApi.getAlerts(10);
    if (alerts && alerts.length > 0) {
      alerts.forEach(a => fsState.addAlert(a));
    }
  } catch (e) {
    console.warn("Could not pre-fetch alerts:", e);
  }

  // 4. Bind State Subscribers to UI DOM
  fsState.subscribe((state) => {
    updateDashboardUI(state);
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
      const data = msg.data !== undefined ? msg.data : msg.payload;

      if (msgType === "TELEMETRY_PREDICTION" && data) {
        fsState.updateFromPrediction(data);
      } else if (msgType === "CRITICAL_ALERT" && data) {
        fsState.addAlert(data);
        nav.playAlertBeep(920, 0.4);
      } else if (msgType === "ALERT_ACKNOWLEDGED" && data) {
        if (data.alert_id) {
          fsState.acknowledgeAlert(data.alert_id, data.acknowledged_by);
        }
      } else if (msgType === "ALERTS_CLEARED") {
        fsState.clearAlerts();
      }
    },
    (status) => {
      nav.updateWsStatus(status);
      fsState.setConnectionState(status);
    }
  );

  wsClient.connect();

  function updateDashboardUI(state) {
    const pred = state.prediction;
    const telem = state.telemetry;

    // Update Banner
    const banner = document.getElementById("status-banner");
    const statusIcon = document.getElementById("status-icon");
    const statusTitle = document.getElementById("status-title");
    const statusDiagnosis = document.getElementById("status-diagnosis");
    const statusRecommendation = document.getElementById("status-recommendation");
    const bannerRiskVal = document.getElementById("banner-risk-val");
    const bannerConfVal = document.getElementById("banner-confidence-val");

    if (banner) {
      banner.className = `status-banner ${pred.risk_level.toLowerCase()}`;
      if (pred.anomaly_detection?.is_anomaly) banner.classList.add("anomaly");

      if (pred.anomaly_detection?.is_anomaly) {
        statusIcon.textContent = "⚡";
        statusTitle.textContent = "ANOMALOUS SENSOR SIGNATURE DETECTED";
      } else if (pred.status_code === 2 || pred.risk_level === "CRITICAL") {
        statusIcon.textContent = "🚨";
        statusTitle.textContent = "CRITICAL CHUTE BLOCKAGE DETECTED";
      } else if (pred.status_code === 1 || pred.risk_level === "WARNING" || pred.risk_level === "HIGH") {
        statusIcon.textContent = "⚠️";
        statusTitle.textContent = "FLOW RESTRICTION / BUILDUP WARNING";
      } else {
        statusIcon.textContent = "✅";
        statusTitle.textContent = "NORMAL DYNAMIC MATERIAL FLOW";
      }

      if (statusDiagnosis) statusDiagnosis.textContent = pred.root_cause_analysis || "";
      if (statusRecommendation) statusRecommendation.textContent = `Action: ${pred.recommended_action || "Maintain current operating feed rate."}`;
      if (bannerRiskVal) {
        bannerRiskVal.textContent = `${pred.risk_percentage.toFixed(1)}%`;
        bannerRiskVal.style.color = `var(--fs-status-${pred.risk_level.toLowerCase()})`;
      }
      if (bannerConfVal) bannerConfVal.textContent = `${(pred.confidence_score * 100).toFixed(1)}%`;
    }

    // Update KPI Cards
    const kpiRiskCard = document.getElementById("kpi-risk-card");
    const kpiRiskVal = document.getElementById("kpi-risk-value");
    const kpiRiskBadge = document.getElementById("kpi-risk-badge");
    if (kpiRiskCard && kpiRiskVal && kpiRiskBadge) {
      kpiRiskCard.className = `kpi-card ${pred.risk_level.toLowerCase()}`;
      kpiRiskVal.textContent = `${pred.risk_percentage.toFixed(1)}%`;
      kpiRiskBadge.className = `badge ${pred.risk_level.toLowerCase()}`;
      kpiRiskBadge.textContent = pred.risk_level;
    }

    const kpiConfVal = document.getElementById("kpi-confidence-value");
    const kpiLatency = document.getElementById("kpi-latency-value");
    if (kpiConfVal) kpiConfVal.textContent = `${(pred.confidence_score * 100).toFixed(1)}%`;
    if (kpiLatency) kpiLatency.textContent = `${pred.latency_ms?.toFixed(1) || "<1"} ms`;

    const kpiChuteVal = document.getElementById("kpi-chute-value");
    const kpiStateCode = document.getElementById("kpi-state-code");
    const kpiFlow = document.getElementById("kpi-flow-rate");
    if (kpiChuteVal) kpiChuteVal.textContent = pred.status_label || "NORMAL";
    if (kpiStateCode) {
      kpiStateCode.className = `badge ${pred.risk_level.toLowerCase()}`;
      kpiStateCode.textContent = `STATE ${pred.status_code}`;
    }
    if (kpiFlow) kpiFlow.textContent = `${telem.material_flow_rate_tph?.toFixed(0) || 240} TPH`;

    const kpiAnomalyTag = document.getElementById("kpi-anomaly-tag");
    if (kpiAnomalyTag) {
      if (pred.anomaly_detection?.is_anomaly) {
        kpiAnomalyTag.textContent = "ANOMALY";
        kpiAnomalyTag.style.color = "var(--fs-status-anomaly)";
      } else {
        kpiAnomalyTag.textContent = "HEALTHY";
        kpiAnomalyTag.style.color = "var(--fs-status-normal)";
      }
    }

    // Update Live Sensor Cards
    const sensorDist = document.getElementById("sensor-val-dist");
    const sensorWeight = document.getElementById("sensor-val-weight");
    const sensorVib = document.getElementById("sensor-val-vib");
    const sensorCurrent = document.getElementById("sensor-val-current");

    if (sensorDist) sensorDist.textContent = telem.distance_cm?.toFixed(1) || "50.0";
    if (sensorWeight) sensorWeight.textContent = telem.weight_kg?.toFixed(0) || "300";
    if (sensorVib) sensorVib.textContent = telem.vibration_g?.toFixed(2) || "3.20";
    if (sensorCurrent) sensorCurrent.textContent = telem.motor_current_a?.toFixed(1) || "42.0";

    // Update Chart & Digital Twin
    fsCharts.updateRiskTimeData(pred.risk_percentage);
    fsCharts.updateChuteDigitalTwin(telem.distance_cm || 50, telem.weight_kg || 300);

    // Update Alert Event List
    const alertList = document.getElementById("alert-log-list");
    if (alertList && state.alerts.length > 0) {
      alertList.innerHTML = state.alerts.slice(0, 8).map(a => `
        <div class="alert-item ${a.severity?.toLowerCase() || 'warning'} ${a.acknowledged ? 'acknowledged' : ''}">
          <div class="alert-item-header">
            <span>${new Date(a.timestamp).toLocaleTimeString()}</span>
            <span>${a.alert_id || 'ALT-01'} ${a.acknowledged ? '✓ ACK' : ''}</span>
          </div>
          <div class="alert-item-title">${a.title || 'System Alert'}</div>
          <div style="font-size: 0.75rem; color: var(--fs-text-secondary);">${a.message || ''}</div>
        </div>
      `).join('');
    }
  }
});
