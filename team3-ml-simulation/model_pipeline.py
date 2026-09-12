"""
FlowSentinel - Team 3 (ML & Simulation)
Phase 2: High-Performance Model Inference Engine & Intelligent SCADA Diagnostics (ChutePredictor)

Features:
1. Sub-3ms Fast-Path Inference with pre-allocated NumPy memory buffers.
2. Single-pass Isolation Forest scoring using decision_function().
3. In-Memory Rolling Buffer (last 10 readings) for temporal rate-of-change (dW/dt, d(dist)/dt, vib jitter).
4. Composite Chute Health & Risk Index (0–100 scale).
5. Granular Industrial Root-Cause Diagnostics and Mitigation Procedures.
"""

import os
import time
import json
from collections import deque
import joblib
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

FEATURE_COLUMNS = [
    "distance_cm",
    "weight_kg",
    "vibration_g",
    "material_flow_rate_tph"
]

STATUS_COLORS = {
    0: "GREEN",
    1: "YELLOW",
    2: "RED"
}

STATUS_LABELS = {
    0: "NORMAL",
    1: "WARNING",
    2: "BLOCKAGE"
}

class ChutePredictor:
    """
    Production-grade inference engine with sub-3ms execution and temporal tracking.
    """

    def __init__(self, models_dir: Optional[str] = None, buffer_size: int = 10):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        self.models_dir = models_dir
        self.rf_model = None
        self.if_model = None
        self.scaler = None
        self.metadata = None
        self.is_loaded = False
        
        # Pre-allocated feature buffer for zero-overhead NumPy allocation
        self._feature_buffer = np.zeros((1, 4), dtype=np.float64)

        # Thread-safe rolling temporal buffer: stores (time_sec, weight, distance, vibration)
        self.history_buffer = deque(maxlen=buffer_size)

        self.load_models()

    def load_models(self) -> bool:
        """
        Loads pre-trained joblib model artifacts from the models directory.
        """
        rf_path = os.path.join(self.models_dir, "chute_random_forest.joblib")
        if_path = os.path.join(self.models_dir, "chute_isolation_forest.joblib")
        scaler_path = os.path.join(self.models_dir, "scaler.joblib")
        meta_path = os.path.join(self.models_dir, "metadata.json")

        if os.path.exists(rf_path) and os.path.exists(if_path) and os.path.exists(scaler_path):
            try:
                self.rf_model = joblib.load(rf_path)
                self.if_model = joblib.load(if_path)
                self.scaler = joblib.load(scaler_path)

                # Ensure n_jobs=1 for zero joblib threading overhead on single-sample inference
                if self.rf_model:
                    self.rf_model.n_jobs = 1
                if self.if_model:
                    self.if_model.n_jobs = 1

                if self.scaler:
                    self._mean = self.scaler.mean_
                    self._scale_inv = 1.0 / self.scaler.scale_
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        self.metadata = json.load(f)
                self.is_loaded = True
                print("✅ [ChutePredictor] Optimized ML Models and Scaler successfully loaded.")
                return True
            except Exception as e:
                print(f"⚠️ [ChutePredictor] Error loading models: {e}. Falling back to heuristic mode.")
                self.is_loaded = False
                return False
        else:
            print("⚠️ [ChutePredictor] Serialized models not found. Running in heuristic fallback mode.")
            self.is_loaded = False
            return False

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute sub-3ms prediction, temporal dynamics calculation, and root-cause analysis.
        """
        start_time = time.perf_counter()
        now = time.time()

        # Extract features directly into pre-allocated NumPy array
        dist = float(telemetry.get("distance_cm", 50.0))
        weight = float(telemetry.get("weight_kg", 300.0))
        vib = float(telemetry.get("vibration_g", 3.0))
        flow = float(telemetry.get("material_flow_rate_tph", 200.0))

        self._feature_buffer[0, 0] = dist
        self._feature_buffer[0, 1] = weight
        self._feature_buffer[0, 2] = vib
        self._feature_buffer[0, 3] = flow

        # Compute temporal rates of change
        dw_dt, ddist_dt, vib_std = self._update_temporal_buffer(now, weight, dist, vib)

        if self.is_loaded and self.rf_model and self.if_model and hasattr(self, "_mean"):
            # Zero-overhead inline vector scaling
            features_scaled = (self._feature_buffer - self._mean) * self._scale_inv

            # Random Forest Inference
            probabilities = self.rf_model.predict_proba(features_scaled)[0]
            class_pred = int(np.argmax(probabilities))
            prob_dict = {
                "normal": round(float(probabilities[0]), 4),
                "warning": round(float(probabilities[1]) if len(probabilities) > 1 else 0.0, 4),
                "blockage": round(float(probabilities[2]) if len(probabilities) > 2 else 0.0, 4),
            }
            confidence = round(float(probabilities[class_pred]), 4)

            # Isolation Forest Fast-Path (single pass decision_function avoids dual tree traversals)
            raw_decision = float(self.if_model.decision_function(features_scaled)[0])
            is_anomaly = raw_decision < 0.0
            # Normalize decision score to [0.0, 1.0] anomaly index (higher = more anomalous)
            anomaly_score = round(float(np.clip(0.5 - raw_decision, 0.0, 1.0)), 4)
            raw_score = round(raw_decision, 4)

        else:
            # Resilient physics heuristic fallback
            if dist < 15.0 or weight > 850.0 or (dist < 25.0 and vib < 0.5):
                class_pred = 2
                prob_dict = {"normal": 0.02, "warning": 0.08, "blockage": 0.90}
                confidence = 0.90
            elif dist < 35.0 or weight > 500.0 or vib < 1.5:
                class_pred = 1
                prob_dict = {"normal": 0.10, "warning": 0.85, "blockage": 0.05}
                confidence = 0.85
            else:
                class_pred = 0
                prob_dict = {"normal": 0.95, "warning": 0.04, "blockage": 0.01}
                confidence = 0.95

            is_anomaly = True if (vib > 9.5 or (dist < 5.0 and weight < 50.0)) else False
            anomaly_score = 0.85 if is_anomaly else 0.12
            raw_score = -0.75 if is_anomaly else 0.25

        # Calculate Composite Chute Health & Risk Index (0-100)
        risk_score, health_state = self._compute_composite_risk(prob_dict, anomaly_score, dw_dt, dist)

        # Advanced Industrial Diagnostics
        diag = self._generate_detailed_diagnosis(
            class_pred, is_anomaly, dist, weight, vib, dw_dt, ddist_dt, vib_std, risk_score, health_state
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "status_code": class_pred,
            "status_label": STATUS_LABELS[class_pred],
            "status_color": STATUS_COLORS[class_pred],
            "confidence_score": confidence,
            "probabilities": prob_dict,
            "anomaly_detection": {
                "is_anomaly": is_anomaly,
                "anomaly_score": anomaly_score,
                "isolation_forest_raw": raw_score
            },
            "root_cause_analysis": diag["root_cause_summary"],
            "recommended_action": diag["recommended_action"],
            "diagnostic_breakdown": diag,
            "telemetry_echo": {
                "distance_cm": dist,
                "weight_kg": weight,
                "vibration_g": vib,
                "material_flow_rate_tph": flow
            },
            "latency_ms": latency_ms
        }

    def _update_temporal_buffer(self, t: float, weight: float, dist: float, vib: float) -> Tuple[float, float, float]:
        """
        Appends reading and computes dW/dt, d(dist)/dt, and rolling vibration variance.
        """
        self.history_buffer.append((t, weight, dist, vib))
        if len(self.history_buffer) < 2:
            return 0.0, 0.0, 0.0

        oldest = self.history_buffer[0]
        dt = max(0.001, t - oldest[0])

        dw_dt = (weight - oldest[1]) / dt
        ddist_dt = (dist - oldest[2]) / dt

        vibs = [sample[3] for sample in self.history_buffer]
        vib_std = float(np.std(vibs))

        return round(float(dw_dt), 2), round(float(ddist_dt), 2), round(vib_std, 3)

    def _compute_composite_risk(self, probs: Dict[str, float], anomaly_score: float, dw_dt: float, dist: float) -> Tuple[float, str]:
        """
        Calculates a 0–100 Chute Risk Score fusing probabilities, anomaly scores, and temporal surge rates.
        """
        # Base risk from classification probabilities
        base_risk = (probs["blockage"] * 70.0) + (probs["warning"] * 25.0)

        # Anomaly contribution (0 - 20)
        anomaly_risk = anomaly_score * 20.0

        # Surge rate penalty: sudden mass surge rate dW/dt > 40 kg/s
        surge_penalty = 0.0
        if dw_dt > 40.0:
            surge_penalty = min(20.0, (dw_dt - 40.0) * 0.4)

        # Clearance fill penalty
        fill_penalty = 0.0
        if dist < 20.0:
            fill_penalty = min(15.0, (20.0 - dist) * 1.0)

        total_risk = round(float(np.clip(base_risk + anomaly_risk + surge_penalty + fill_penalty, 0.0, 100.0)), 1)

        if total_risk >= 75.0:
            health_state = "CRITICAL_INTERVENTION_REQUIRED"
        elif total_risk >= 50.0:
            health_state = "ELEVATED_RISK_WARNING"
        elif total_risk >= 25.0:
            health_state = "MODERATE_BUILDUP_STABLE"
        else:
            health_state = "OPTIMAL_CONTINUOUS_FLOW"

        return total_risk, health_state

    def _generate_detailed_diagnosis(
        self,
        status_code: int,
        is_anomaly: bool,
        dist: float,
        weight: float,
        vib: float,
        dw_dt: float,
        ddist_dt: float,
        vib_std: float,
        risk_score: float,
        health_state: str
    ) -> Dict[str, Any]:
        """
        Pinpoints failure modes among 6 industrial root causes with mitigation recommendations.
        """
        # 1. Specific Sensor & Mechanical Hardware Anomalies
        if vib > 9.0:
            cat = "MECHANICAL_RESONANCE_OR_LOOSE_LINER"
            sev = "HIGH"
            evidence = f"Extreme vibration spike ({vib:.2f} G RMS) without mass blockage. Liner plate or impact pad loose."
            action = "Halt conveyor at next scheduled stop; inspect chute liner bolts and damping rubber pads."
            summary = "Severe mechanical vibration surge detected. Structural wear liner looseness suspected."
        elif dist < 10.0 and weight < 50.0:
            cat = "SENSOR_OPTICAL_BLINDING"
            sev = "MODERATE"
            evidence = f"Ultrasonic clearance near-zero ({dist:.1f} cm) with negligible load mass ({weight:.1f} kg)."
            action = "Purge ultrasonic transducer face with compressed air ring; clean dust coating on sensor window."
            summary = "Ultrasonic sensor blinding suspected (air gap zeroed without corresponding mass loading)."
        elif weight > 1200.0 and vib > 5.0 and dist > 40.0:
            cat = "LOAD_CELL_DRIFT_OR_FAULT"
            sev = "MODERATE"
            evidence = f"Weight sensor reports {weight:.1f} kg while clearance remains open ({dist:.1f} cm)."
            action = "Check load cell strain gauge excitation voltage and zero-tare calibration."
            summary = "Load cell calibration drift suspected. Mass reading contradicts clearance profile."

        # 2. Confirmed Physical Blockage
        elif status_code == 2:
            if dw_dt > 50.0:
                cat = "RAPID_SURGE_JAM"
                sev = "CRITICAL"
                evidence = f"Rapid mass accumulation rate (+{dw_dt:.1f} kg/s) leading to instant throat choke."
                action = "Trip conveyor interlock; activate discharge vibrator motors to disperse jam."
                summary = "Rapid material surge jam formed in transfer chute."
            elif dist < 15.0 and vib < 0.40:
                cat = "CRITICAL_FUNNEL_CHOKE"
                sev = "CRITICAL"
                evidence = f"Full bed accumulation ({dist:.1f} cm clearance) with near-zero vibration ({vib:.2f} G) and heavy mass ({weight:.1f} kg)."
                action = "IMMEDIATE EMERGENCY STOP of upstream feeder belt. Trigger high-pressure pneumatic air cannons."
                summary = "Critical material choke: Bed accumulation reached maximum fill with dead mechanical vibration."
            else:
                cat = "OVERBURDEN_FLOW_STOPPAGE"
                sev = "CRITICAL"
                evidence = f"Chute burden exceeds capacity ({weight:.1f} kg) with severe material stagnation."
                action = "Shut down upstream feed to prevent belt motor overload; initiate manual clearing sequence."
                summary = "Overburden threshold exceeded with complete flow stoppage."

        # 3. Confirmed Warning / Sluggish Buildup
        elif status_code == 1:
            if dw_dt > 25.0:
                cat = "ACCELERATING_BUILDUP"
                sev = "ELEVATED"
                evidence = f"Material mass increasing at +{dw_dt:.1f} kg/s with declining clearance ({ddist_dt:.1f} cm/s)."
                action = "Throttle upstream feed by 35%; pulse auxiliary acoustic vibrators."
                summary = "Accelerating material buildup detected. Rate of accumulation indicates impending jam."
            elif vib < 1.2:
                cat = "SLUGGISH_SIDEWALL_RESTRICTION"
                sev = "WARNING"
                evidence = f"Vibration dampening ({vib:.2f} G) indicates thick material cushion adhering to chute walls."
                action = "Reduce belt speed by 20%; inspect moisture content and fine ore proportion."
                summary = "Progressive material buildup detected along chute sidewalls with dampening vibration."
            else:
                cat = "TRANSIENT_RESTRICTION"
                sev = "WARNING"
                evidence = f"Nominal clearance narrowing ({dist:.1f} cm) with elevated load ({weight:.1f} kg)."
                action = "Monitor discharge conveyor clearance and prepare vibrator sequence."
                summary = "Transient surge in chute loading above nominal threshold."

        # 4. Out-of-Distribution Sensor Anomaly on Non-Blockage
        elif is_anomaly:
            cat = "UNCLASSIFIED_SENSOR_ANOMALY"
            sev = "WARNING"
            evidence = f"Out-of-distribution multi-sensor vector identified by Isolation Forest."
            action = "Inspect local sensor junction box and signal cabling for RF interference."
            summary = "Out-of-distribution multi-sensor pattern identified by Isolation Forest."

        # 5. Normal Flow
        else:
            cat = "NORMAL_OPERATION"
            sev = "NOMINAL"
            evidence = f"Clearance ({dist:.1f} cm), load ({weight:.1f} kg), and kinetic vibration ({vib:.2f} G) in dynamic balance."
            action = "No intervention required. Maintain current continuous feed setpoint."
            summary = "Dynamic equilibrium flow. Kinetic impact frequency and clearance within nominal bounds."

        return {
            "fault_category": cat,
            "fault_severity": sev,
            "primary_sensor_evidence": evidence,
            "mitigation_procedure": action,
            "root_cause_summary": summary,
            "recommended_action": action,
            "temporal_metrics": {
                "dw_dt_kg_per_sec": dw_dt,
                "ddist_dt_cm_per_sec": ddist_dt,
                "vibration_variance": vib_std
            },
            "chute_health_index": {
                "risk_score": risk_score,
                "health_state": health_state
            }
        }
