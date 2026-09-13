"""
FlowSentinel - Team 3 (ML & Simulation)
Training Pipeline for Isolation Forest & Random Forest Models.

Artifacts Output:
- models/chute_random_forest.joblib
- models/chute_isolation_forest.joblib
- models/scaler.joblib
- models/metadata.json
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from data_generator import ChutePhysicsGenerator

# Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    "distance_cm",
    "weight_kg",
    "vibration_g",
    "material_flow_rate_tph"
]

# The anomaly detector describes *sensor/mechanical faults*, not normal process
# transitions.  WARNING and BLOCKAGE are therefore valid operating signatures
# for the Isolation Forest and must be part of its inlier population.
IF_CONTAMINATION = 0.02
IF_CALIBRATION_FALSE_POSITIVE_RATE = 0.02
IF_RANDOM_STATE = 42

def train_and_export_models(n_samples: int = 20000):
    print("🚀 [Team 3 ML] Starting Synthetic Physics Dataset Generation...")
    generator = ChutePhysicsGenerator(seed=42)
    df = generator.generate_dataset(n_samples=n_samples)
    
    X = df[FEATURE_COLUMNS].values
    y_class = df["state_label"].values
    is_anomaly = df["is_anomaly"].values

    # Step 1: train/calibrate the Isolation Forest on all non-fault operating
    # states.  Training only on NORMAL flow incorrectly labels legitimate
    # WARNING and BLOCKAGE telemetry as sensor anomalies.
    print("🧠 [Team 3 ML] Training Isolation Forest for Unsupervised Anomaly Detection...")
    healthy_mask = df["is_anomaly"].values == 0
    healthy_indices = np.flatnonzero(healthy_mask)
    if_train_idx, if_calibration_idx = train_test_split(
        healthy_indices, test_size=0.25, random_state=IF_RANDOM_STATE,
        stratify=df.loc[healthy_indices, "state_label"]
    )
    X_if_train = X[if_train_idx]
    X_if_calibration = X[if_calibration_idx]

    scaler = StandardScaler()
    X_scaled_if_train = scaler.fit_transform(X_if_train)

    # A larger forest stabilizes the decision boundary while keeping
    # single-sample inference below the project latency budget.
    isolation_forest = IsolationForest(
        n_estimators=200,
        max_samples=512,
        contamination=IF_CONTAMINATION,
        random_state=IF_RANDOM_STATE,
        n_jobs=1
    )
    isolation_forest.fit(X_scaled_if_train)

    # Calibrate against held-out healthy process telemetry rather than relying
    # exclusively on the model's fitted offset.  The threshold is persisted so
    # inference and validation use exactly the same operating point.
    calibration_scores = isolation_forest.decision_function(
        scaler.transform(X_if_calibration)
    )
    anomaly_threshold = float(np.quantile(
        calibration_scores, IF_CALIBRATION_FALSE_POSITIVE_RATE
    ))

    # Step 2: Train Random Forest Classifier on non-anomalous labeled data
    print("🌲 [Team 3 ML] Training Random Forest for 3-State Chute Classification (0=Normal, 1=Warning, 2=Blockage)...")
    valid_mask = df["is_anomaly"] == 0
    X_valid = X[valid_mask]
    y_valid = y_class[valid_mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X_valid, y_valid, test_size=0.25, random_state=42, stratify=y_valid
    )

    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    random_forest = RandomForestClassifier(
        n_estimators=20,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=1
    )
    random_forest.fit(X_train_scaled, y_train)

    # Step 3: Evaluate Random Forest
    y_pred = random_forest.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, target_names=["NORMAL", "WARNING", "BLOCKAGE"], output_dict=True)
    conf_mat = confusion_matrix(y_test, y_pred).tolist()

    print(f"\n✅ Random Forest Test Accuracy: {acc * 100:.2f}% | F1-Score: {f1:.4f}")
    print("\nClassification Report Summary:")
    print(classification_report(y_test, y_pred, target_names=["NORMAL", "WARNING", "BLOCKAGE"]))

    # Step 4: Feature Importances
    importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in random_forest.feature_importances_]))
    print("📊 Feature Importances:", importances)

    # Step 5: Save Model Artifacts
    rf_path = os.path.join(MODELS_DIR, "chute_random_forest.joblib")
    if_path = os.path.join(MODELS_DIR, "chute_isolation_forest.joblib")
    scaler_path = os.path.join(MODELS_DIR, "scaler.joblib")
    meta_path = os.path.join(MODELS_DIR, "metadata.json")

    joblib.dump(random_forest, rf_path)
    joblib.dump(isolation_forest, if_path)
    joblib.dump(scaler, scaler_path)

    metadata = {
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "n_samples": n_samples,
        "features": FEATURE_COLUMNS,
        "metrics": {
            "accuracy": round(float(acc), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": conf_mat,
            "feature_importances": importances
        },
        "anomaly_detection": {
            "training_population": "all_non_fault_operational_states",
            "contamination": IF_CONTAMINATION,
            "calibration_false_positive_rate": IF_CALIBRATION_FALSE_POSITIVE_RATE,
            "decision_threshold": round(anomaly_threshold, 6),
            "n_estimators": isolation_forest.n_estimators,
            "max_samples": isolation_forest.max_samples,
        },
        "classes": {
            0: "NORMAL",
            1: "WARNING",
            2: "BLOCKAGE"
        }
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Artifacts successfully saved to {MODELS_DIR}/")
    return metadata

if __name__ == "__main__":
    train_and_export_models()
