/**
 * FlowSentinel - Global Application State Store
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

class FlowSentinelState {
  constructor() {
    this.telemetry = {
      distance_cm: 52.0,
      weight_kg: 320.0,
      vibration_g: 3.4,
      motor_current_a: 42.5,
      material_flow_rate_tph: 240.0
    };

    this.prediction = {
      status_code: 0,
      status_label: "NORMAL",
      status_color: "GREEN",
      confidence_score: 0.965,
      risk_percentage: 12.5,
      risk_level: "NORMAL",
      probabilities: { normal: 0.965, warning: 0.030, blockage: 0.005 },
      anomaly_detection: { is_anomaly: false, anomaly_score: 0.12, isolation_forest_raw: 0.45 },
      root_cause_analysis: "Dynamic equilibrium flow. Clearance and vibration within nominal bounds.",
      recommended_action: "Maintain standard operating feed rate.",
      latency_ms: 12.4
    };

    this.connectionState = "connecting";
    this.alerts = [];
    this.listeners = [];
  }

  calculateRiskMetrics(pred) {
    const probs = pred.probabilities || { normal: 0.9, warning: 0.08, blockage: 0.02 };
    // Risk formula: Weighted probability + anomaly weighting
    let risk = (probs.warning * 50) + (probs.blockage * 100);
    if (pred.anomaly_detection?.is_anomaly) {
      risk = Math.max(risk, pred.anomaly_detection.anomaly_score * 100);
    }
    risk = Math.min(100, Math.max(0, risk));

    let riskLevel = "NORMAL";
    if (risk >= 80 || pred.status_code === 2) riskLevel = "CRITICAL";
    else if (risk >= 60) riskLevel = "HIGH";
    else if (risk >= 30 || pred.status_code === 1) riskLevel = "WARNING";

    return {
      riskPercentage: parseFloat(risk.toFixed(1)),
      riskLevel: riskLevel
    };
  }

  updateFromPrediction(pred) {
    const riskData = this.calculateRiskMetrics(pred);

    this.prediction = {
      ...pred,
      risk_percentage: riskData.riskPercentage,
      risk_level: riskData.riskLevel
    };

    if (pred.telemetry_echo) {
      this.telemetry = {
        ...this.telemetry,
        ...pred.telemetry_echo
      };
      // Synthesize motor current derived from load & flow
      this.telemetry.motor_current_a = parseFloat((30 + (this.telemetry.weight_kg / 1200) * 35).toFixed(1));
    }

    this.notify();
  }

  addAlert(alert) {
    this.alerts.unshift(alert);
    if (this.alerts.length > 50) this.alerts.pop();
    this.notify();
  }

  setConnectionState(state) {
    this.connectionState = state;
    this.notify();
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(cb => {
      try { cb(this); } catch (e) { console.error("State listener error:", e); }
    });
  }
}

const fsState = new FlowSentinelState();

