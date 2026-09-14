/**
 * FlowSentinel - Team 1 (Frontend UI/UX)
 * Robust WebSocket Client with Automatic Reconnection & Event Dispatcher
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

class TelemetryWebSocketClient {
  constructor(url, onMessageCallback, onStatusCallback) {
    this.url = this._resolveUrl(url);
    this.onMessage = onMessageCallback || (() => {});
    this.onStatus = onStatusCallback || (() => {});
    this.socket = null;
    this.reconnectTimer = null;
    this.reconnectInterval = 2500;
    this.maxReconnectInterval = 10000;
    this.currentBackoff = this.reconnectInterval;
    this.isConnected = false;
    this.shouldReconnect = true;
    this.listeners = new Map();
  }

  _resolveUrl(customUrl) {
    if (customUrl && typeof customUrl === "string" && customUrl.trim().length > 0) {
      return customUrl;
    }

    if (typeof window === "undefined" || !window.location) {
      return "ws://localhost:8000/ws/telemetry";
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let host = window.location.host;

    if (!host || window.location.protocol === "file:") {
      host = "localhost:8000";
    }

    return `${protocol}//${host}/ws/telemetry`;
  }

  connect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      try {
        this.socket.onopen = null;
        this.socket.onmessage = null;
        this.socket.onclose = null;
        this.socket.onerror = null;
        if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close();
        }
      } catch (e) {
        console.warn("⚠️ [WS Client] Error cleaning prior socket:", e);
      }
      this.socket = null;
    }

    console.log(`🔌 [WS Client] Connecting to ${this.url}...`);
    this.onStatus("connecting");
    this._dispatchStatus("connecting");

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log("✅ [WS Client] Connected to FlowSentinel Backend!");
        this.isConnected = true;
        this.currentBackoff = this.reconnectInterval;
        this.onStatus("online");
        this._dispatchStatus("online");
      };

      this.socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          const msgType = parsed.type;
          const msgData = parsed.data !== undefined ? parsed.data : parsed.payload;

          // Invoke global callback
          this.onMessage(parsed);

          // Dispatch to typed listeners
          if (msgType) {
            this._dispatchEvent(msgType, msgData);
          }
        } catch (err) {
          console.error("⚠️ [WS Client] Error parsing incoming JSON:", err, event.data);
        }
      };

      this.socket.onclose = (event) => {
        console.warn("⚠️ [WS Client] Disconnected from server.", event.reason || "");
        this.isConnected = false;
        this.onStatus("offline");
        this._dispatchStatus("offline");

        if (this.shouldReconnect) {
          this._scheduleReconnect();
        }
      };

      this.socket.onerror = (error) => {
        console.warn("❌ [WS Client] WebSocket Transport Error:", error);
        this.isConnected = false;
        this.onStatus("offline");
        this._dispatchStatus("offline");
      };

    } catch (e) {
      console.error("❌ [WS Client] Connection instantiation failed:", e);
      this.isConnected = false;
      this.onStatus("offline");
      this._dispatchStatus("offline");

      if (this.shouldReconnect) {
        this._scheduleReconnect();
      }
    }
  }

  _scheduleReconnect() {
    if (this.reconnectTimer) return;
    const delay = this.currentBackoff;
    this.currentBackoff = Math.min(this.maxReconnectInterval, this.currentBackoff * 1.5);
    console.log(`⏱️ [WS Client] Reconnecting in ${delay}ms...`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type).add(callback);
    return () => this.off(type, callback);
  }

  off(type, callback) {
    if (this.listeners.has(type)) {
      this.listeners.get(type).delete(callback);
    }
  }

  _dispatchEvent(type, data) {
    if (this.listeners.has(type)) {
      this.listeners.get(type).forEach((cb) => {
        try {
          cb(data);
        } catch (e) {
          console.error(`Error in listener for '${type}':`, e);
        }
      });
    }
  }

  _dispatchStatus(status) {
    this._dispatchEvent("STATUS_CHANGE", status);
  }

  send(type, payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type, payload: payload || {} });
      this.socket.send(message);
      return true;
    } else {
      console.warn(`⚠️ [WS Client] Cannot send '${type}': Socket is not open (readyState: ${this.socket ? this.socket.readyState : 'null'}).`);
      return false;
    }
  }

  sendSimulationUpdate(telemetry) {
    return this.send("SIMULATION_UPDATE", telemetry);
  }

  setMode(mode, preset = "NORMAL_FLOW", intervalMs = 500) {
    return this.send("SET_SIMULATION_MODE", {
      mode: mode,
      preset: preset,
      interval_ms: intervalMs
    });
  }

  acknowledgeAlert(alertId, acknowledgedBy = "operator") {
    return this.send("ACKNOWLEDGE_ALERT", {
      alert_id: alertId,
      acknowledged_by: acknowledgedBy
    });
  }

  sendPing() {
    return this.send("PING", { timestamp: new Date().toISOString() });
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      try {
        this.socket.close();
      } catch (e) {
        // ignore
      }
      this.socket = null;
    }
    this.isConnected = false;
    this.onStatus("offline");
  }
}
