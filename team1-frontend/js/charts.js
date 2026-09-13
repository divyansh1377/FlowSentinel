/**
 * FlowSentinel - Dynamic Industrial SCADA Visualizers & Chart.js Engine
 * Product: FlowSentinel (Predictive Chute Blockage Management)
 */

class FlowSentinelCharts {
  constructor() {
    this.maxPoints = 30;
    this.telemetryChart = null;
    this.riskTimeChart = null;
    this.simulationChart = null;
    this.isPaused = false;
  }

  initTelemetryChart(canvasId = "telemetryChart") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const initialLabels = Array.from({ length: this.maxPoints }, (_, i) => `-${this.maxPoints - i}s`);
    const zeros = Array(this.maxPoints).fill(null);

    this.telemetryChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: initialLabels,
        datasets: [
          {
            label: "Clearance (cm)",
            data: [...zeros],
            borderColor: "#38bdf8",
            backgroundColor: "rgba(56, 189, 248, 0.08)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yDistance"
          },
          {
            label: "Load (kg)",
            data: [...zeros],
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.08)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yWeight"
          },
          {
            label: "Vibration (G RMS)",
            data: [...zeros],
            borderColor: "#10b981",
            backgroundColor: "rgba(16, 185, 129, 0.08)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yVib"
          },
          {
            label: "Motor Current (A)",
            data: [...zeros],
            borderColor: "#a855f7",
            backgroundColor: "rgba(168, 85, 247, 0.08)",
            borderWidth: 1.5,
            borderDash: [4, 4],
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yCurrent"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            labels: { color: "#94a3b8", font: { size: 11, family: "-apple-system, BlinkMacSystemFont, sans-serif" } }
          },
          tooltip: {
            backgroundColor: "#131c31",
            borderColor: "#2c3c58",
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: "#1e293b" },
            ticks: { color: "#64748b", maxTicksLimit: 6 }
          },
          yDistance: {
            type: "linear",
            position: "left",
            min: 0,
            max: 120,
            title: { display: true, text: "Distance (cm)", color: "#38bdf8" },
            ticks: { color: "#38bdf8" },
            grid: { color: "#1e293b" }
          },
          yWeight: {
            type: "linear",
            position: "right",
            min: 0,
            max: 1500,
            title: { display: true, text: "Weight (kg)", color: "#f59e0b" },
            ticks: { color: "#f59e0b" },
            grid: { drawOnChartArea: false }
          },
          yVib: {
            type: "linear",
            position: "right",
            min: 0,
            max: 15,
            display: false,
            grid: { drawOnChartArea: false }
          },
          yCurrent: {
            type: "linear",
            position: "right",
            min: 0,
            max: 100,
            display: false,
            grid: { drawOnChartArea: false }
          }
        }
      }
    });

    return this.telemetryChart;
  }

  initRiskTimeChart(canvasId = "riskTimeChart") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const initialLabels = Array.from({ length: this.maxPoints }, (_, i) => `-${this.maxPoints - i}s`);
    const zeros = Array(this.maxPoints).fill(10);

    this.riskTimeChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: initialLabels,
        datasets: [
          {
            label: "Blockage Risk (%)",
            data: [...zeros],
            borderColor: "#06b6d4",
            backgroundColor: "rgba(6, 182, 212, 0.15)",
            borderWidth: 2.5,
            tension: 0.3,
            fill: true,
            pointRadius: 0
          },
          {
            label: "Critical Threshold (80%)",
            data: Array(this.maxPoints).fill(80),
            borderColor: "rgba(239, 68, 68, 0.6)",
            borderWidth: 1.5,
            borderDash: [6, 6],
            pointRadius: 0,
            fill: false
          },
          {
            label: "Warning Threshold (30%)",
            data: Array(this.maxPoints).fill(30),
            borderColor: "rgba(245, 158, 11, 0.5)",
            borderWidth: 1.5,
            borderDash: [6, 6],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { size: 10 } } }
        },
        scales: {
          x: { grid: { color: "#1e293b" }, ticks: { color: "#64748b", maxTicksLimit: 6 } },
          y: {
            min: 0,
            max: 100,
            title: { display: true, text: "Risk Level (%)", color: "#94a3b8" },
            ticks: { color: "#94a3b8" },
            grid: { color: "#1e293b" }
          }
        }
      }
    });

    return this.riskTimeChart;
  }

  updateTelemetryData(dist, weight, vib, current = 40) {
    if (this.isPaused || !this.telemetryChart) return;
    const nowLabel = new Date().toLocaleTimeString().split(" ")[0];

    const chart = this.telemetryChart;
    chart.data.labels.push(nowLabel);
    if (chart.data.labels.length > this.maxPoints) chart.data.labels.shift();

    const ds = chart.data.datasets;
    ds[0].data.push(dist);
    ds[1].data.push(weight);
    ds[2].data.push(vib);
    ds[3].data.push(current);

    if (ds[0].data.length > this.maxPoints) {
      ds.forEach(d => d.data.shift());
    }

    chart.update("none");
  }

  updateRiskTimeData(riskVal) {
    if (this.isPaused || !this.riskTimeChart) return;
    const nowLabel = new Date().toLocaleTimeString().split(" ")[0];

    const chart = this.riskTimeChart;
    chart.data.labels.push(nowLabel);
    if (chart.data.labels.length > this.maxPoints) chart.data.labels.shift();

    chart.data.datasets[0].data.push(riskVal);
    if (chart.data.datasets[0].data.length > this.maxPoints) {
      chart.data.datasets[0].data.shift();
    }

    // Dynamic coloring based on current risk
    if (riskVal >= 80) {
      chart.data.datasets[0].borderColor = "#ef4444";
      chart.data.datasets[0].backgroundColor = "rgba(239, 68, 68, 0.2)";
    } else if (riskVal >= 30) {
      chart.data.datasets[0].borderColor = "#f59e0b";
      chart.data.datasets[0].backgroundColor = "rgba(245, 158, 11, 0.2)";
    } else {
      chart.data.datasets[0].borderColor = "#06b6d4";
      chart.data.datasets[0].backgroundColor = "rgba(6, 182, 212, 0.15)";
    }

    chart.update("none");
  }

  updateChuteDigitalTwin(dist, weight, bedElementId = "chute-bed-level", labelElementId = "chute-bed-label") {
    const bedEl = document.getElementById(bedElementId);
    const labelEl = document.getElementById(labelElementId);
    if (!bedEl) return;

    // Fill percent: Distance 100cm -> 5%, Distance 5cm -> 95%
    const fillPercent = Math.min(96, Math.max(4, Math.round(((100 - dist) / 95) * 88 + (weight / 1500) * 12)));
    bedEl.style.height = `${fillPercent}%`;

    if (fillPercent > 70) {
      bedEl.style.background = "linear-gradient(180deg, #ef4444, #7f1d1d)";
    } else if (fillPercent > 40) {
      bedEl.style.background = "linear-gradient(180deg, #f59e0b, #78350f)";
    } else {
      bedEl.style.background = "linear-gradient(180deg, #10b981, #064e3b)";
    }

    if (labelEl) {
      labelEl.textContent = `Bed Level: ${fillPercent}% (${weight.toFixed(0)} kg)`;
    }
  }

  clearHistory() {
    [this.telemetryChart, this.riskTimeChart, this.simulationChart].forEach(chart => {
      if (!chart) return;
      chart.data.labels = Array.from({ length: this.maxPoints }, (_, i) => `-${this.maxPoints - i}s`);
      chart.data.datasets.forEach(d => {
        d.data = Array(this.maxPoints).fill(null);
      });
      chart.update();
    });
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    return this.isPaused;
  }
}

const fsCharts = new FlowSentinelCharts();
