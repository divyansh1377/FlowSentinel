/**
 * FlowSentinel - Global Navigation & Shell Injector
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 * Shared across all 8 pages for Team 1 & Team 2 consistency.
 */

class FlowSentinelNavigation {
  constructor(activeRoute = "/") {
    this.activeRoute = activeRoute;
    this.audioCtx = null;
    this.alarmAudioEnabled = false;
    this.init();
  }

  init() {
    this.renderSidebar();
    this.renderHeader();
    this.setupAudio();
    this.setupGlobalEventListeners();
  }

  renderSidebar() {
    const sidebarContainer = document.getElementById("sidebar-container");
    if (!sidebarContainer) return;

    const navItems = [
      { section: "Operational Monitoring" },
      { label: "Dashboard", route: "/", icon: "📊", file: "index.html" },
      { label: "Live Monitoring", route: "/monitoring", icon: "📡", file: "monitoring.html" },
      { label: "Simulation", route: "/simulation", icon: "🎛️", file: "simulation.html" },
      { label: "Manual Prediction", route: "/manual", icon: "🧪", file: "manual.html" },
      { section: "Model & Diagnostics (T2)" },
      { label: "Training Center", route: "/training", icon: "🧠", file: "training.html" },
      { label: "Analytics", route: "/analytics", icon: "📈", file: "analytics.html" },
      { label: "System / Hardware", route: "/system", icon: "⚙️", file: "system.html" },
      { label: "About", route: "/about", icon: "ℹ️", file: "about.html" }
    ];

    let navHtml = `
      <aside class="fs-sidebar">
        <div class="fs-brand">
          <div class="fs-brand-logo">🛡️</div>
          <div class="fs-brand-info">
            <h1>FlowSentinel</h1>
            <p>Predictive Chute Blockage Management</p>
          </div>
        </div>

        <nav class="fs-nav">
    `;

    navItems.forEach(item => {
      if (item.section) {
        navHtml += `<div class="fs-nav-section-title">${item.section}</div>`;
      } else {
        const isActive = this.activeRoute === item.route || window.location.pathname.endsWith(item.file);
        navHtml += `
          <a href="${item.file}" class="fs-nav-item ${isActive ? 'active' : ''}">
            <span class="fs-nav-icon">${item.icon}</span>
            <span>${item.label}</span>
          </a>
        `;
      }
    });

    navHtml += `
        </nav>
        <div class="fs-sidebar-footer">
          <div>Blast Furnace Transfer Chute #01</div>
          <div style="color: var(--fs-accent-cyan); font-weight: 600;">v1.0.0 • SIH 2026</div>
        </div>
      </aside>
    `;

    sidebarContainer.innerHTML = navHtml;
  }

  renderHeader() {
    const headerContainer = document.getElementById("header-container");
    if (!headerContainer) return;

    const pageMeta = {
      "/": { title: "DASHBOARD", desc: "Predictive Chute Health & Anomaly Overview" },
      "/monitoring": { title: "LIVE MONITORING", desc: "Real-time Chute Health & Sensor Monitoring" },
      "/simulation": { title: "SIMULATION ENGINE", desc: "Virtual Chute Physics & Blockage Scenario Testbed" },
      "/manual": { title: "MANUAL PREDICTION", desc: "Hypothetical Telemetry Multi-Model Inference Studio" },
      "/training": { title: "TRAINING CENTER", desc: "Model Retraining & Sensor Dataset Management" },
      "/analytics": { title: "ANALYTICS & PERFORMANCE", desc: "Model Precision, Recall & Ablation Insights" },
      "/system": { title: "SYSTEM & HARDWARE", desc: "ESP32 Gateway & Multi-Sensor Diagnostics" },
      "/about": { title: "ABOUT FLOWSENTINEL", desc: "System Architecture & Engineering Methodology" }
    };

    const currentMeta = pageMeta[this.activeRoute] || { title: "FLOWSENTINEL", desc: "Predictive Chute Blockage Management" };

    headerContainer.innerHTML = `
      <header class="fs-header">
        <div class="fs-header-title">
          <h2>${currentMeta.title}</h2>
          <p>${currentMeta.desc}</p>
        </div>

        <div class="fs-header-actions">
          <button id="toggle-sound-btn" class="badge" style="cursor: pointer; background: var(--fs-bg-input); border-color: var(--fs-border-medium);">
            🔇 ALARM: OFF
          </button>

          <div id="ws-status-badge" class="badge">
            <span class="pulse-dot"></span>
            <span id="ws-status-text">CONNECTING...</span>
          </div>

          <div class="badge" style="color: var(--fs-text-secondary); border-color: var(--fs-border-subtle);">
            ⏱️ <span id="header-clock">--:--:--</span>
          </div>
        </div>
      </header>
    `;

    // Clock update
    setInterval(() => {
      const clockEl = document.getElementById("header-clock");
      if (clockEl) {
        clockEl.textContent = new Date().toLocaleTimeString();
      }
    }, 1000);
  }

  setupAudio() {
    const soundBtn = document.getElementById("toggle-sound-btn");
    if (!soundBtn) return;

    soundBtn.addEventListener("click", () => {
      this.alarmAudioEnabled = !this.alarmAudioEnabled;
      soundBtn.textContent = this.alarmAudioEnabled ? "🔊 ALARM: ON" : "🔇 ALARM: OFF";
      soundBtn.style.color = this.alarmAudioEnabled ? "var(--fs-status-critical)" : "var(--fs-text-secondary)";
      soundBtn.style.borderColor = this.alarmAudioEnabled ? "var(--fs-status-critical)" : "var(--fs-border-medium)";

      if (this.alarmAudioEnabled && !this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
    });
  }

  playAlertBeep(freq = 880, duration = 0.25) {
    if (!this.alarmAudioEnabled || !this.audioCtx) return;
    try {
      if (this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = "sawtooth";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.2, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {
      console.warn("Audio synthesizer exception:", e);
    }
  }

  updateWsStatus(status) {
    const badge = document.getElementById("ws-status-badge");
    const text = document.getElementById("ws-status-text");
    if (!badge || !text) return;

    if (status === "online") {
      badge.className = "badge online";
      text.textContent = "ONLINE (WS)";
    } else if (status === "connecting") {
      badge.className = "badge";
      text.textContent = "CONNECTING...";
    } else {
      badge.className = "badge offline";
      text.textContent = "OFFLINE";
    }
  }

  setupGlobalEventListeners() {
    // Un-mute AudioContext safely on first user gesture
    window.addEventListener("click", () => {
      if (this.audioCtx && this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
    }, { once: true });
  }
}

