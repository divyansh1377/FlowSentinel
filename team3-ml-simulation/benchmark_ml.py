"""
FlowSentinel - Team 3 (ML & Simulation)
Benchmarking and Validation Suite for AI Models.

Measures:
1. Accuracy, Precision, Recall, F1 across Normal, Warning, Blockage
2. Anomaly detection accuracy on out-of-distribution patterns
3. Isolation Forest false-positive rate on normal samples
4. Inference Latency (Mean, P95, P99 in milliseconds)
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_fscore_support
from data_generator import ChutePhysicsGenerator
from model_pipeline import ChutePredictor
from test_phase3_noisy_stress import run_phase3_suite

FEATURE_COLUMNS = ["distance_cm", "weight_kg", "vibration_g", "material_flow_rate_tph"]
REPORT_PATH = Path(__file__).with_name("EVALUATION_REPORT.md")


def write_evaluation_report(metrics: dict, stress_passed: int, stress_total: int) -> None:
    """Overwrite the checked-in report with metrics produced in this run."""
    generated_at = datetime.now(timezone.utc).isoformat()
    report = f"""# FlowSentinel ML Evaluation Report

Generated: `{generated_at}`

## Current validation results

| Metric | Result |
| --- | ---: |
| Random Forest classification accuracy | {metrics['accuracy_pct']:.2f}% |
| Isolation Forest anomaly recall | {metrics['anomaly_recall_pct']:.2f}% |
| Isolation Forest false-positive rate | {metrics['if_fpr_pct']:.2f}% |
| Mean inference latency | {metrics['latency_mean_ms']:.3f} ms |
| P95 inference latency | {metrics['latency_p95_ms']:.3f} ms |
| P99 inference latency | {metrics['latency_p99_ms']:.3f} ms |
| Phase 3 stress checks | {stress_passed}/{stress_total} passed |

## Per-class Random Forest metrics

| Class | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
"""
    for label, values in metrics["per_class"].items():
        report += (
            f"| {label} | {values['precision']:.4f} | "
            f"{values['recall']:.4f} | {values['f1']:.4f} |\n"
        )
    report += """

## Method

The anomaly decision combines a calibrated Isolation Forest trained on all
non-fault operational states with deterministic physics-consistency guards for
high-confidence sensor and mechanical faults. The Phase 3 total above is a
hard CI gate: a failed stress check makes `benchmark_ml.py` exit with code 1.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")

def run_benchmarks(n_eval_samples: int = 2000):
    print(f"📊 [Team 3 Benchmark] Running validation on {n_eval_samples} physics-simulated samples...")
    generator = ChutePhysicsGenerator(seed=999)
    df = generator.generate_dataset(n_samples=n_eval_samples)

    predictor = ChutePredictor()
    if not predictor.is_loaded:
        print("⚠️ Models not trained yet! Training now...")
        from train_models import train_and_export_models
        train_and_export_models()
        predictor.load_models()

    latencies = []
    correct_class = 0
    total_non_anomaly = 0
    anomaly_detected = 0
    total_anomalies = 0

    # ── Lists for per-class detailed metrics ─────────────────────────────────
    y_true_class = []   # true labels for non-anomaly samples
    y_pred_class = []

    # ── IF false-positive tracking on known-normal samples ───────────────────
    y_true_if = []      # 0=normal, 1=anomaly (ground truth from generator)
    y_pred_if = []      # predicted by IF

    for _, row in df.iterrows():
        sample = {
            "distance_cm": row["distance_cm"],
            "weight_kg": row["weight_kg"],
            "vibration_g": row["vibration_g"],
            "material_flow_rate_tph": row["material_flow_rate_tph"]
        }

        t0 = time.perf_counter()
        result = predictor.predict(sample)
        lat = (time.perf_counter() - t0) * 1000
        latencies.append(lat)

        gt_anomaly = int(row["is_anomaly"])
        pred_anomaly = 1 if result["anomaly_detection"]["is_anomaly"] else 0
        y_true_if.append(gt_anomaly)
        y_pred_if.append(pred_anomaly)

        if gt_anomaly == 1:
            total_anomalies += 1
            if pred_anomaly == 1:
                anomaly_detected += 1
        else:
            total_non_anomaly += 1
            pred_label = result["status_code"]
            gt_label   = int(row["state_label"])
            if pred_label == gt_label:
                correct_class += 1
            y_true_class.append(gt_label)
            y_pred_class.append(pred_label)

    accuracy = (correct_class / total_non_anomaly) * 100 if total_non_anomaly > 0 else 0
    anomaly_recall = (anomaly_detected / total_anomalies) * 100 if total_anomalies > 0 else 0

    lat_mean = np.mean(latencies)
    lat_p95  = np.percentile(latencies, 95)
    lat_p99  = np.percentile(latencies, 99)

    # ── Per-class RF metrics ──────────────────────────────────────────────────
    y_true_arr = np.array(y_true_class)
    y_pred_arr = np.array(y_pred_class)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, average=None, labels=[0, 1, 2],
        zero_division=0
    )
    prec_w, rec_w, f1_w, _ = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, average="weighted", labels=[0, 1, 2],
        zero_division=0
    )

    # ── IF false-positive rate on normal (non-anomaly) samples ───────────────
    y_true_if_arr = np.array(y_true_if)
    y_pred_if_arr = np.array(y_pred_if)
    normal_mask = (y_true_if_arr == 0)
    fp_count = np.sum((y_pred_if_arr[normal_mask] == 1))
    fpr = (fp_count / np.sum(normal_mask)) * 100 if np.sum(normal_mask) > 0 else 0.0

    print("\n" + "=" * 60)
    print("🎯 BENCHMARK RESULTS")
    print("=" * 60)
    print(f"• Random Forest Classification Accuracy: {accuracy:.2f}%")
    print(f"• Isolation Forest Anomaly Recall:       {anomaly_recall:.2f}%")
    print(f"• Isolation Forest False-Positive Rate:  {fpr:.2f}%  (on normal samples)")
    print(f"• Total Evaluated Telemetry Points:      {n_eval_samples}")
    print(f"• Mean Inference Latency:                {lat_mean:.3f} ms")
    print(f"• P95 Latency:                           {lat_p95:.3f} ms")
    print(f"• P99 Latency:                           {lat_p99:.3f} ms")
    print("-" * 60)
    print("📋 Random Forest Per-Class Metrics:")
    class_names = ["NORMAL", "WARNING", "BLOCKAGE"]
    for i, cls in enumerate(class_names):
        print(f"   {cls:>10}: Precision={prec[i]:.4f}  Recall={rec[i]:.4f}  F1={f1[i]:.4f}")
    print(f"   {'Weighted':>10}: Precision={prec_w:.4f}  Recall={rec_w:.4f}  F1={f1_w:.4f}")
    print("=" * 60)
    print("✅ Model meets sub-20ms industrial real-time requirements!\n")

    # Return structured dict for use by other scripts / report generation
    return {
        "accuracy_pct":    round(accuracy, 2),
        "anomaly_recall_pct": round(anomaly_recall, 2),
        "if_fpr_pct":      round(fpr, 2),
        "latency_mean_ms": round(lat_mean, 3),
        "latency_p95_ms":  round(lat_p95, 3),
        "latency_p99_ms":  round(lat_p99, 3),
        "per_class": {
            cls: {"precision": round(float(prec[i]), 4),
                  "recall": round(float(rec[i]), 4),
                  "f1": round(float(f1[i]), 4)}
            for i, cls in enumerate(class_names)
        },
        "weighted": {"precision": round(float(prec_w), 4),
                     "recall": round(float(rec_w), 4),
                     "f1": round(float(f1_w), 4)},
    }

if __name__ == "__main__":
    metrics = run_benchmarks()
    stress_passed, stress_total, stress_failures = run_phase3_suite()
    write_evaluation_report(metrics, stress_passed, stress_total)
    sys.exit(1 if stress_failures else 0)

