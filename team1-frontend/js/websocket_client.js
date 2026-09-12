/**
 * FlowSentinel - Team 1 (Frontend UI/UX)
 * Robust WebSocket Client with Automatic Reconnection & Event Dispatcher
 */

class TelemetryWebSocketClient {
  constructor(url, onMessageCallback, onStatusCallback) {
    this.url = url || `ws://${window.location.host}/ws/telemetry`;
    this.onMessage = onMessageCallback || (() => {});
    this.onStatus = onStatusCallback || (() => {});
    this.socket = null;
    this.reconnectInterval = 2500;
    this.isConnected = false;
    this.shouldReconnect = true;
  }

  connect() {
    console.log(`🔌 [WS Client] Attempting connection to ${this.url}...`);
    this.onStatus("connecting");

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log("✅ [WS Client] Connected to FlowSentinel Backend!");
        this.isConnected = true;
        this.onStatus("online");
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (err) {
          console.error("⚠️ [WS Client] Error parsing incoming JSON:", err);
        }
      };

      this.socket.onclose = (event) => {
        console.warn("⚠️ [WS Client] Disconnected from server.", event.reason);
        this.isConnected = false;
        this.onStatus("offline");
        if (this.shouldReconnect) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.socket.onerror = (error) => {
        console.error("❌ [WS Client] WebSocket Error:", error);
        this.onStatus("offline");
      };

    } catch (e) {
      console.error("❌ [WS Client] Connection instantiation failed:", e);
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  send(type, payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type, payload });
      this.socket.send(message);
    } else {
      console.warn("⚠️ [WS Client] Cannot send message: Socket is not open.");
    }
  }

  sendSimulationUpdate(telemetry) {
    this.send("SIMULATION_UPDATE", telemetry);
  }

  setMode(mode, preset = "NORMAL_FLOW", intervalMs = 500) {
    this.send("SET_SIMULATION_MODE", {
      mode: mode,
      preset: preset,
      interval_ms: intervalMs
    });
  }
}

