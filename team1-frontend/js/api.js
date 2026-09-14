/**
 * FlowSentinel - REST API Client Module
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

class FlowSentinelAPI {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl || (typeof window !== "undefined" && window.location ? window.location.origin : "http://localhost:8000");
    if (typeof window !== "undefined" && window.location && (!baseUrl && window.location.protocol === "file:")) {
      this.baseUrl = "http://localhost:8000";
    }
  }

  async getStatus() {
    try {
      const res = await fetch(`${this.baseUrl}/api/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn("⚠️ [API] Failed to fetch /api/status:", e);
      return null;
    }
  }

  async getPresets() {
    try {
      const res = await fetch(`${this.baseUrl}/api/presets`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn("⚠️ [API] Failed to fetch /api/presets:", e);
      return null;
    }
  }

  async getAlerts(limit = 50) {
    try {
      const res = await fetch(`${this.baseUrl}/api/alerts?limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn("⚠️ [API] Failed to fetch /api/alerts:", e);
      return [];
    }
  }

  async acknowledgeAlert(alertId, acknowledgedBy = "operator", notes = null) {
    try {
      const payload = { acknowledged_by: acknowledgedBy };
      if (notes) payload.notes = notes;

      const res = await fetch(`${this.baseUrl}/api/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error(`❌ [API] Failed to acknowledge alert ${alertId}:`, e);
      throw e;
    }
  }

  async clearAlerts() {
    try {
      const res = await fetch(`${this.baseUrl}/api/alerts`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error("❌ [API] Failed to clear alerts:", e);
      throw e;
    }
  }

  async postTelemetry(payload) {
    try {
      // Normalize payload if simple sensors object was passed
      let body = payload;
      if (payload && !payload.sensors && (payload.distance_cm !== undefined || payload.weight_kg !== undefined)) {
        body = {
          sensors: {
            distance_cm: payload.distance_cm,
            weight_kg: payload.weight_kg,
            vibration_g: payload.vibration_g !== undefined ? payload.vibration_g : 3.0
          },
          operational: {
            material_flow_rate_tph: payload.material_flow_rate_tph !== undefined ? payload.material_flow_rate_tph : 200.0
          }
        };
      }

      const res = await fetch(`${this.baseUrl}/api/telemetry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error("❌ [API] Failed to post telemetry:", e);
      throw e;
    }
  }

  async triggerRetrain() {
    try {
      const res = await fetch(`${this.baseUrl}/api/retrain`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error("❌ [API] Failed to trigger retrain:", e);
      throw e;
    }
  }
}

const fsApi = new FlowSentinelAPI();
