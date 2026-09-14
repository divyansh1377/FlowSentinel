# FlowSentinel ML Evaluation Report

Generated: `2026-09-14T06:11:20.500745+00:00`

## Current validation results

| Metric | Result |
| --- | ---: |
| Random Forest classification accuracy | 100.00% |
| Isolation Forest anomaly recall | 100.00% |
| Isolation Forest false-positive rate | 1.21% |
| Mean inference latency | 11.518 ms |
| P95 inference latency | 12.730 ms |
| P99 inference latency | 13.558 ms |
| Phase 3 stress checks | 87/87 passed |

## Per-class Random Forest metrics

| Class | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| NORMAL | 1.0000 | 1.0000 | 1.0000 |
| WARNING | 1.0000 | 1.0000 | 1.0000 |
| BLOCKAGE | 1.0000 | 1.0000 | 1.0000 |


## Method

The anomaly decision combines a calibrated Isolation Forest trained on all
non-fault operational states with deterministic physics-consistency guards for
high-confidence sensor and mechanical faults. The Phase 3 total above is a
hard CI gate: a failed stress check makes `benchmark_ml.py` exit with code 1.
