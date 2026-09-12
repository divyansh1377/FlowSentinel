/**
 * FlowSentinel - Team 1 (Frontend UI/UX)
 * Manual & Auto Simulation Controller Module
 */

class SimulationPanel {
  constructor(wsClient) {
    this.wsClient = wsClient;
    this.mode = "manual"; // "manual" or "auto"
    this.activePreset = "NORMAL_FLOW";
    this.debounceTimer = null;

    // DOM Elements
    this.distanceSlider = document.getElementById("slider-distance");
    this.weightSlider = document.getElementById("slider-weight");
    this.vibrationSlider = document.getElementById("slider-vibration");
    this.flowSlider = document.getElementById("slider-flow");

    this.distanceVal = document.getElementById("val-distance");
    this.weightVal = document.getElementById("val-weight");
    this.vibrationVal = document.getElementById("val-vibration");
    this.flowVal = document.getElementById("val-flow");

    this.modeToggle = document.getElementById("toggle-sim-mode");
    this.modeLabel = document.getElementById("sim-mode-label");

    this.presets = {
      NORMAL_FLOW: { distance: 55.0, weight: 320.0, vibration: 3.2, flow: 240.0 },
      RISING_BUILDUP: { distance: 24.0, weight: 680.0, vibration: 1.2, flow: 110.0 },
      COMPLETE_BLOCKAGE: { distance: 6.0, weight: 1150.0, vibration: 0.18, flow: 0.0 },
      EMPTY_CHUTE: { distance: 95.0, weight: 0.0, vibration: 0.08, flow: 0.0 },
      ERRATIC_SENSOR_SPIKE: { distance: 50.0, weight: 310.0, vibration: 12.8, flow: 220.0 }
    };

    this.initEventListeners();
  }

  initEventListeners() {
    // Slider event listeners
    const sliders = [
      { el: this.distanceSlider, valEl: this.distanceVal, unit: " cm" },
      { el: this.weightSlider, valEl: this.weightVal, unit: " kg" },
      { el: this.vibrationSlider, valEl: this.vibrationVal, unit: " G" },
      { el: this.flowSlider, valEl: this.flowVal, unit: " TPH" }
    ];

    sliders.forEach(s => {
      s.el.addEventListener("input", () => {
        s.valEl.textContent = s.el.value + s.unit;
        this.clearActivePresetButtons();
        if (this.mode === "manual") {
          this.triggerDebouncedSend();
        }
      });
    });

    // Preset buttons
    document.querySelectorAll(".btn-preset").forEach(btn => {
      btn.addEventListener("click", () => {
        const presetKey = btn.getAttribute("data-preset");
        this.applyPreset(presetKey);
      });
    });

    // Auto / Manual mode toggle
    if (this.modeToggle) {
      this.modeToggle.addEventListener("change", (e) => {
        this.mode = e.target.checked ? "auto" : "manual";
        this.modeLabel.textContent = this.mode === "auto" ? "LIVE AUTO PHYSICS" : "MANUAL SLIDERS";
        this.modeLabel.style.color = this.mode === "auto" ? "var(--color-cyan)" : "var(--text-primary)";

        this.wsClient.setMode(this.mode, this.activePreset, 400);
      });
    }
  }

  applyPreset(presetKey) {
    if (!this.presets[presetKey]) return;
    this.activePreset = presetKey;
    const p = this.presets[presetKey];

    this.distanceSlider.value = p.distance;
    this.distanceVal.textContent = p.distance + " cm";

    this.weightSlider.value = p.weight;
    this.weightVal.textContent = p.weight + " kg";

    this.vibrationSlider.value = p.vibration;
    this.vibrationVal.textContent = p.vibration + " G";

    this.flowSlider.value = p.flow;
    this.flowVal.textContent = p.flow + " TPH";

    // Highlight active preset button
    this.clearActivePresetButtons();
    const activeBtn = document.querySelector(`.btn-preset[data-preset="${presetKey}"]`);
    if (activeBtn) activeBtn.classList.add("active");

    if (this.mode === "auto") {
      this.wsClient.setMode("auto", presetKey, 400);
    } else {
      this.sendCurrentState();
    }
  }

  clearActivePresetButtons() {
    document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
  }

  triggerDebouncedSend() {
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.sendCurrentState();
    }, 40); // 40ms debounce for ultra-smooth 25fps slider responsiveness
  }

  sendCurrentState() {
    const payload = {
      distance_cm: parseFloat(this.distanceSlider.value),
      weight_kg: parseFloat(this.weightSlider.value),
      vibration_g: parseFloat(this.vibrationSlider.value),
      material_flow_rate_tph: parseFloat(this.flowSlider.value)
    };
    this.wsClient.sendSimulationUpdate(payload);
  }

  updateSlidersFromIncoming(telemetry) {
    if (this.mode === "auto") {
      if (telemetry.distance_cm !== undefined) {
        this.distanceSlider.value = telemetry.distance_cm;
        this.distanceVal.textContent = telemetry.distance_cm.toFixed(1) + " cm";
      }
      if (telemetry.weight_kg !== undefined) {
        this.weightSlider.value = telemetry.weight_kg;
        this.weightVal.textContent = telemetry.weight_kg.toFixed(1) + " kg";
      }
      if (telemetry.vibration_g !== undefined) {
        this.vibrationSlider.value = telemetry.vibration_g;
        this.vibrationVal.textContent = telemetry.vibration_g.toFixed(2) + " G";
      }
      if (telemetry.material_flow_rate_tph !== undefined) {
        this.flowSlider.value = telemetry.material_flow_rate_tph;
        this.flowVal.textContent = telemetry.material_flow_rate_tph.toFixed(0) + " TPH";
      }
    }
  }
}

