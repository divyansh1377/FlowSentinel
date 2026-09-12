"""
FlowSentinel - Team 3 (ML & Simulation)
Unified Model Inference Engine (ChutePredictor)

Provides a clean, thread-safe, high-speed inference interface for Team 2 (Backend).
Handles feature transformation, dual model scoring (Isolation Forest + Random Forest),
anomaly detection, and automated root cause diagnosis.
"""

import os
import time
import json
import joblib
import numpy as np
from typing import Dict, Any, Optional

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
    Production-ready inference class imported by Team 2 (FastAPI Backend).
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        self.models_dir = models_dir
        self.rf_model = None
        self.if_model = None
        self.scaler = None
        self.metadata = None
        self.is_loaded = False
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
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        self.metadata = json.load(f)
                self.is_loaded = True
                print("✅ [ChutePredictor] ML Models and Scaler successfully loaded.")
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
        Perform high-speed prediction and anomaly scoring for incoming telemetry.
        """
        start_time = time.perf_counter()

        # Extract features
        distance = float(telemetry.get("distance_cm", 50.0))
        weight = float(telemetry.get("weight_kg", 300.0))
        vibration = float(telemetry.get("vibration_g", 3.0))
        flow_rate = float(telemetry.get("material_flow_rate_tph", 200.0))

        features = np.array([[distance, weight, vibration, flow_rate]])

        if self.is_loaded and self.rf_model and self.if_model and self.scaler:
            # Scaled features
            features_scaled = self.scaler.transform(features)

            # Random Forest Inference
            class_pred = int(self.rf_model.predict(features_scaled)[0])
            probabilities = self.rf_model.predict_proba(features_scaled)[0]
            prob_dict = {
                "normal": round(float(probabilities[0]), 4),
                "warning": round(float(probabilities[1]) if len(probabilities) > 1 else 0.0, 4),
                "blockage": round(float(probabilities[2]) if len(probabilities) > 2 else 0.0, 4),
            }
            confidence = round(float(np.max(probabilities)), 4)

            # Isolation Forest Anomaly Detection
            # -1 = anomaly, 1 = normal in scikit-learn
            if_pred = int(self.if_model.predict(features_scaled)[0])
            is_anomaly = True if if_pred == -1 else False
            raw_score = float(self.if_model.score_samples(features_scaled)[0])
            # Normalize raw_score to 0.0-1.0 anomaly index (higher = more anomalous)
            anomaly_score = round(float(np.clip(-raw_score, 0.0, 1.0)), 4)

        else:
            # Physics-based heuristic fallback (ensures backend never crashes even without models)
            if distance < 15.0 or weight > 850.0 or (distance < 25.0 and vibration < 0.5):
                class_pred = 2
                prob_dict = {"normal": 0.02, "warning": 0.08, "blockage": 0.90}
                confidence = 0.90
            elif distance < 35.0 or weight > 500.0 or vibration < 1.5:
                class_pred = 1
                prob_dict = {"normal": 0.10, "warning": 0.85, "blockage": 0.05}
                confidence = 0.85
            else:
                class_pred = 0
                prob_dict = {"normal": 0.95, "warning": 0.04, "blockage": 0.01}
                confidence = 0.95

            is_anomaly = True if (vibration > 10.0 or (distance < 5.0 and weight < 50.0)) else False
            anomaly_score = 0.85 if is_anomaly else 0.12
            raw_score = -0.75 if is_anomaly else 0.25

        # Root cause diagnosis & recommended action
        diagnosis, recommendation = self._generate_diagnosis(class_pred, is_anomaly, distance, weight, vibration)

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
                "isolation_forest_raw": round(raw_score, 4)
            },
            "root_cause_analysis": diagnosis,
            "recommended_action": recommendation,
            "telemetry_echo": {
                "distance_cm": distance,
                "weight_kg": weight,
                "vibration_g": vibration,
                "material_flow_rate_tph": flow_rate
            },
            "latency_ms": latency_ms
        }

    def _generate_diagnosis(self, status_code: int, is_anomaly: bool, dist: float, weight: float, vib: float) -> Tuple[str, str]:
        if is_anomaly:
            if vib > 9.0:
                return (
                    "Erratic mechanical vibration surge detected. Possible loose liner plate or severe structural resonance.",
                    "Inspect chute structural mounting and damping pads immediately."
                )
            elif dist < 10.0 and weight < 50.0:
                return (
                    "Ultrasonic sensor lens blinding / dust coating suspected (low clearance but negligible mass).",
                    "Purge ultrasonic transducer air ring and check sensor alignment."
                )
            else:
                return (
                    "Out-of-distribution multi-sensor pattern identified by Isolation Forest.",
                    "Perform instrument diagnostic check on sensor junction box."
                )

        if status_code == 2:  # BLOCKAGE
            if dist < 15.0 and weight > 900.0:
                return (
                    "Critical material choke: Bed accumulation reached maximum fill with dead mechanical vibration.",
                    "Trigger emergency upstream conveyor stop. Activate air cannons / vibrators."
                )
            elif vib < 0.3:
                return (
                    "Stagnant material plug formed in lower chute funnel.",
                    "Halt feed and initiate mechanical clearing sequence."
                )
            else:
                return (
                    "Overburden threshold exceeded with severe flow constriction.",
                    "Shutdown feeder immediately to prevent motor burnout."
                )

        elif status_code == 1:  # WARNING
            if weight > 600.0:
                return (
                    "Progressive material buildup detected along chute sidewalls.",
                    "Throttle upstream feed rate by 30% and monitor clearance."
                )
            elif vib < 1.2:
                return (
                    "Material flow sluggishness causing vibration dampening.",
                    "Inspect moisture content and trigger periodic vibrator pulsing."
                )
            else:
                return (
                    "Transient surge in chute loading above nominal threshold.",
                    "Verify secondary conveyor discharge clearance."
                )

        else:  # NORMAL
            return (
                "Dynamic equilibrium flow. Kinetic impact frequency and clearance within nominal bounds.",
                "Maintain standard operating feed rate."
            )

