/**
 * FlowSentinel - Team 1 (Frontend UI/UX)
 * Main Application Orchestrator
 */

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Initializing FlowSentinel SCADA Dashboard...");

  // Audio Alarm Synth (Web Audio API)
  let audioCtx = null;
  let alarmAudioEnabled = false;

  const toggleSoundBtn = document.getElementById("toggle-sound");
  if (toggleSoundBtn) {
    toggleSoundBtn.addEventListener("click", () => {
      alarmAudioEnabled = !alarmAudioEnabled;
      toggleSoundBtn.textContent = alarmAudioEnabled ? "🔊 ALARM: ON" : "🔇 ALARM: OFF";
      toggleSoundBtn.style.color = alarmAudioEnabled ? "var(--color-blockage)" : "var(--text-muted)";
      if (alarmAudioEnabled && !audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
    });
  }

  function playAlertBeep(freq = 880, duration = 0.2) {
    if (!alarmAudioEnabled || !audioCtx) return;
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sawtooth";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      console.warn("Audio synth issue:", e);
    }
  }

  // DOM references
  const wsStatusBadge = document.getElementById("ws-status-badge");
  const wsStatusText = document.getElementById("ws-status-text");

  const statusBanner = document.getElementById("status-banner");
  const statusIcon = document.getElementById("status-icon");
  const statusTitle = document.getElementById("status-title");
  const statusDiagnosis = document.getElementById("status-diagnosis");
  const statusRecommendation = document.getElementById("status-recommendation");

  const metricConfidence = document.getElementById("metric-confidence");
  const metricLatency = document.getElementById("metric-latency");
  const metricAnomaly = document.getElementById("metric-anomaly");

  const probNormalBar = document.getElementById("prob-normal-bar");
  const probNormalVal = document.getElementById("prob-normal-val");
  const probWarningBar = document.getElementById("prob-warning-bar");
  const probWarningVal = document.getElementById("prob-warning-val");
  const probBlockageBar = document.getElementById("prob-blockage-bar");
  const probBlockageVal = document.getElementById("prob-blockage-val");

  const alertLogList = document.getElementById("alert-log-list");

  // Initialize Visualizer
  const visualizer = new SCADAVisualizer();

  // Status updates callback
  const onWsStatus = (status) => {
    if (wsStatusBadge && wsStatusText) {
      if (status === "online") {
        wsStatusBadge.className = "badge online";
        wsStatusText.textContent = "CONNECTED (WS LIVE)";
      } else if (status === "connecting") {
        wsStatusBadge.className = "badge";
        wsStatusText.textContent = "CONNECTING...";
      } else {
        wsStatusBadge.className = "badge offline";
        wsStatusText.textContent = "DISCONNECTED";
      }
    }
  };

  // Incoming WebSocket messages callback
  const onWsMessage = (msg) => {
    const msgType = msg.type;
    const data = msg.data || msg.payload;

    if (msgType === "TELEMETRY_PREDICTION" && data) {
      handlePredictionUpdate(data);
    } else if (msgType === "CRITICAL_ALERT" && data) {
      addAlertToLog(data);
      playAlertBeep(920, 0.4);
    } else if (msgType === "HANDSHAKE") {
      console.log("🤝 Server handshake received:", data);
    }
  };

  // Instantiate WebSocket client
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
  const wsClient = new TelemetryWebSocketClient(wsUrl, onWsMessage, onWsStatus);
  wsClient.connect();

  // Instantiate Simulation Panel
  const simPanel = new SimulationPanel(wsClient);

  // Handle incoming prediction
  function handlePredictionUpdate(pred) {
    const statusCode = pred.status_code;
    const statusLabel = pred.status_label;
    const isAnomaly = pred.anomaly_detection?.is_anomaly;
    const anomalyScore = pred.anomaly_detection?.anomaly_score || 0;
    const conf = (pred.confidence_score * 100).toFixed(1);
    const latency = pred.latency_ms?.toFixed(1) || "<1";

    const echo = pred.telemetry_echo || {};
    const dist = echo.distance_cm || 50;
    const weight = echo.weight_kg || 300;
    const vib = echo.vibration_g || 3;

    // Update charts & digital twin
    visualizer.updateTelemetry(dist, weight, vib);
    simPanel.updateSlidersFromIncoming(echo);

    // Update metrics readouts
    if (metricConfidence) metricConfidence.textContent = `${conf}%`;
    if (metricLatency) metricLatency.textContent = `${latency} ms`;
    if (metricAnomaly) {
      metricAnomaly.textContent = isAnomaly ? `ANOMALY (${(anomalyScore * 100).toFixed(0)}%)` : "NORMAL";
      metricAnomaly.style.color = isAnomaly ? "var(--color-anomaly)" : "var(--color-normal)";
    }

    // Update status banner
    if (statusBanner) {
      statusBanner.className = "status-banner";
      if (isAnomaly) {
        statusBanner.classList.add("anomaly");
        statusIcon.textContent = "⚡";
        statusTitle.textContent = "ANOMALOUS SENSOR SIGNATURE";
      } else if (statusCode === 2) {
        statusBanner.classList.add("blockage");
        statusIcon.textContent = "🚨";
        statusTitle.textContent = "CRITICAL CHUTE BLOCKAGE DETECTED";
        playAlertBeep(880, 0.15);
      } else if (statusCode === 1) {
        statusBanner.classList.add("warning");
        statusIcon.textContent = "⚠️";
        statusTitle.textContent = "FLOW RESTRICTION / BUILDUP WARNING";
      } else {
        statusBanner.classList.add("normal");
        statusIcon.textContent = "✅";
        statusTitle.textContent = "NORMAL DYNAMIC MATERIAL FLOW";
      }
    }

    if (statusDiagnosis) statusDiagnosis.textContent = pred.root_cause_analysis || "";
    if (statusRecommendation) statusRecommendation.textContent = `Action: ${pred.recommended_action || "Maintain current feed rate."}`;

    // Update Probabilities
    const probs = pred.probabilities || { normal: 0.9, warning: 0.08, blockage: 0.02 };
    if (probNormalBar && probNormalVal) {
      const pNorm = (probs.normal * 100).toFixed(1);
      probNormalBar.style.width = `${pNorm}%`;
      probNormalVal.textContent = `${pNorm}%`;
    }
    if (probWarningBar && probWarningVal) {
      const pWarn = (probs.warning * 100).toFixed(1);
      probWarningBar.style.width = `${pWarn}%`;
      probWarningVal.textContent = `${pWarn}%`;
    }
    if (probBlockageBar && probBlockageVal) {
      const pBlock = (probs.blockage * 100).toFixed(1);
      probBlockageBar.style.width = `${pBlock}%`;
      probBlockageVal.textContent = `${pBlock}%`;
    }
  }

  function addAlertToLog(alert) {
    if (!alertLogList) return;
    const item = document.createElement("div");
    const isCrit = alert.severity === "CRITICAL";
    item.className = `alert-item ${isCrit ? "critical" : "warning"}`;
    const timeStr = new Date(alert.timestamp).toLocaleTimeString();

    item.innerHTML = `
      <div class="alert-time">${timeStr} • ${alert.alert_id || "ALERT"}</div>
      <div class="alert-msg">${alert.title}</div>
      <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem;">${alert.message}</div>
    `;

    alertLogList.insertBefore(item, alertLogList.firstChild);
    if (alertLogList.children.length > 25) {
      alertLogList.removeChild(alertLogList.lastChild);
    }
  }

  // Initial trigger
  setTimeout(() => {
    simPanel.sendCurrentState();
  }, 400);
});

