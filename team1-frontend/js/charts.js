/**
 * FlowSentinel - Team 1 (Frontend UI/UX)
 * Real-Time SCADA Charts & Chute Digital Twin Visualizer
 */

class SCADAVisualizer {
  constructor() {
    this.maxPoints = 30;
    this.telemetryChart = null;
    this.chuteBedLevel = document.getElementById("chute-bed-level");
    this.chuteBedLabel = document.getElementById("chute-bed-label");
    this.initChart();
  }

  initChart() {
    const ctx = document.getElementById("telemetryChart");
    if (!ctx) return;

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
            backgroundColor: "rgba(56, 189, 248, 0.1)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yDistance"
          },
          {
            label: "Weight Load (kg)",
            data: [...zeros],
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.1)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yWeight"
          },
          {
            label: "Vibration (G RMS)",
            data: [...zeros],
            borderColor: "#10b981",
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "yVib"
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
            labels: { color: "#94a3b8", font: { size: 11 } }
          },
          tooltip: {
            backgroundColor: "#1e293b",
            borderColor: "#334155",
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
            title: { display: false },
            ticks: { display: false },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }

  updateTelemetry(dist, weight, vib) {
    if (!this.telemetryChart) return;

    const chart = this.telemetryChart;
    const nowLabel = new Date().toLocaleTimeString().split(" ")[0];

    chart.data.labels.push(nowLabel);
    if (chart.data.labels.length > this.maxPoints) {
      chart.data.labels.shift();
    }

    // Update datasets
    const datasets = chart.data.datasets;
    datasets[0].data.push(dist);
    datasets[1].data.push(weight);
    datasets[2].data.push(vib);

    if (datasets[0].data.length > this.maxPoints) {
      datasets[0].data.shift();
      datasets[1].data.shift();
      datasets[2].data.shift();
    }

    chart.update("none");

    // Update Digital Twin Chute Graphic
    this.updateChuteDigitalTwin(dist, weight);
  }

  updateChuteDigitalTwin(dist, weight) {
    if (!this.chuteBedLevel) return;

    // Calculate height fill percentage based on distance & weight
    // Distance 100cm = 5% fill, Distance 5cm = 95% fill
    const fillPercent = Math.min(95, Math.max(5, Math.round(((100 - dist) / 95) * 90 + (weight / 1500) * 10)));
    this.chuteBedLevel.style.height = `${fillPercent}%`;

    if (fillPercent > 70) {
      this.chuteBedLevel.style.background = "linear-gradient(180deg, #ef4444, #991b1b)";
    } else if (fillPercent > 45) {
      this.chuteBedLevel.style.background = "linear-gradient(180deg, #f59e0b, #92400e)";
    } else {
      this.chuteBedLevel.style.background = "linear-gradient(180deg, #10b981, #065f46)";
    }

    if (this.chuteBedLabel) {
      this.chuteBedLabel.textContent = `Fill: ${fillPercent}% (${weight.toFixed(0)} kg)`;
    }
  }
}

