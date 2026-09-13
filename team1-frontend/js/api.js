/**
 * FlowSentinel - REST API Client Module
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

class FlowSentinelAPI {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl || window.location.origin;
    if (!baseUrl && window.location.protocol === "file:") {
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

  async postTelemetry(payload) {
    try {
      const res = await fetch(`${this.baseUrl}/api/telemetry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
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
