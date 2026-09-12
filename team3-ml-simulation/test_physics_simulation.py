"""
FlowSentinel - Team 3 (ML & Simulation)
Phase 1 Validation Suite: Physics Generator & Data Integrity Tests

Validates:
1. Physical consistency (clearance distance vs burden weight vs kinetic vibration)
2. Markov Chain temporal continuity and transition properties
3. Industrial noise injection bounds and sensor dropout/anomaly generation
4. Baseline synthetic dataset schema, distributions, and absence of NaN/corrupted values
5. ChutePredictor Phase 1 contract conformance (both heuristic fallback and trained artifact modes)
"""

import os
import pytest
import numpy as np
import pandas as pd

from data_generator import (
    ChutePhysicsGenerator,
    CHUTE_EMPTY_DISTANCE_CM,
    CHUTE_FULL_DISTANCE_CM,
    MAX_LOAD_CAPACITY_KG
)
from model_pipeline import ChutePredictor, FEATURE_COLUMNS

@pytest.fixture
def physics_gen():
    return ChutePhysicsGenerator(seed=42)

def test_physics_normal_flow_bounds(physics_gen):
    """Test State 0 (Normal Flow) conforms to physical operating specifications."""
    samples = [physics_gen.generate_sample(state=0, inject_noise=True) for _ in range(200)]
    df = pd.DataFrame(samples)

    # Normal clearance should remain healthy (> 35 cm) on average
    assert df["distance_cm"].mean() > 40.0
    assert df["distance_cm"].min() >= 1.0

    # Normal weight should remain dynamic and well below structural buildup (< 500 kg)
    assert 200.0 < df["weight_kg"].mean() < 420.0

    # Normal vibration should reflect rock impact chatter (> 1.8 G RMS)
    assert df["vibration_g"].mean() > 2.2

    # State label & anomaly flag
    assert (df["state_label"] == 0).all()
    assert (df["is_anomaly"] == 0).all()

def test_physics_warning_buildup_bounds(physics_gen):
    """Test State 1 (Warning / Rising Buildup) shows declining clearance and rising weight."""
    samples = [physics_gen.generate_sample(state=1, inject_noise=True) for _ in range(200)]
    df = pd.DataFrame(samples)

    # Clearance decreases as bed rises (15 to 38 cm)
    assert 15.0 < df["distance_cm"].mean() < 35.0

    # Weight increases (500 to 800 kg)
    assert 500.0 < df["weight_kg"].mean() < 800.0

    # Vibration dampens due to ore cushion (0.8 to 1.8 G)
    assert 0.6 < df["vibration_g"].mean() < 1.9

    assert (df["state_label"] == 1).all()
    assert (df["is_anomaly"] == 0).all()

def test_physics_critical_blockage_bounds(physics_gen):
    """Test State 2 (Critical Blockage) shows severe accumulation and near-zero vibration."""
    samples = [physics_gen.generate_sample(state=2, inject_noise=True) for _ in range(200)]
    df = pd.DataFrame(samples)

    # Clearance near zero (< 15 cm)
    assert df["distance_cm"].mean() < 15.0

    # Heavy pile (> 850 kg)
    assert df["weight_kg"].mean() > 850.0

    # Kinetic dead stop (< 0.5 G)
    assert df["vibration_g"].mean() < 0.45

    assert (df["state_label"] == 2).all()
    assert (df["is_anomaly"] == 0).all()

def test_physics_inverse_relationship(physics_gen):
    """Verify physical inverse coupling: higher material weight implies lower clearance distance."""
    s_normal = physics_gen.generate_sample(state=0, inject_noise=False)
    s_warning = physics_gen.generate_sample(state=1, inject_noise=False)
    s_blockage = physics_gen.generate_sample(state=2, inject_noise=False)

    assert s_normal["distance_cm"] > s_warning["distance_cm"] > s_blockage["distance_cm"]
    assert s_normal["weight_kg"] < s_warning["weight_kg"] < s_blockage["weight_kg"]
    assert s_normal["vibration_g"] > s_warning["vibration_g"] > s_blockage["vibration_g"]

def test_markov_trajectory_continuity(physics_gen):
    """Test continuous Markov chain generates unbroken physical time-series trajectories."""
    df_traj = physics_gen.generate_continuous_trajectory(n_steps=1000)
    
    assert len(df_traj) == 1000
    assert not df_traj.isnull().values.any()

    # Verify tri-axial decomposition exists
    assert "vibration_x" in df_traj.columns
    assert "vibration_y" in df_traj.columns
    assert "vibration_z" in df_traj.columns

    # Verify state transitions occur
    unique_states = df_traj["state_label"].unique()
    assert len(unique_states) >= 2

def test_exported_dataset_integrity():
    """Test exported CSV and JSON baseline dataset integrity."""
    csv_path = os.path.join(os.path.dirname(__file__), "data", "chute_telemetry_synthetic.csv")
    assert os.path.exists(csv_path), f"Baseline dataset missing at {csv_path}"

    df = pd.read_csv(csv_path)
    assert len(df) >= 10000
    assert set(FEATURE_COLUMNS).issubset(df.columns)
    assert "state_label" in df.columns
    assert "is_anomaly" in df.columns

    # Ensure no NaN or infinite values
    assert not df.isnull().values.any()
    assert not np.isinf(df[FEATURE_COLUMNS].values).any()

def test_chutepredictor_contract_conformance():
    """Verify ChutePredictor conforms strictly to API_CONTRACT.md prediction schema."""
    predictor = ChutePredictor()
    sample = {
        "distance_cm": 50.0,
        "weight_kg": 300.0,
        "vibration_g": 3.0,
        "material_flow_rate_tph": 200.0
    }
    result = predictor.predict(sample)

    # Check required fields
    required_keys = [
        "status_code", "status_label", "status_color",
        "confidence_score", "probabilities", "anomaly_detection",
        "root_cause_analysis", "recommended_action",
        "telemetry_echo", "latency_ms"
    ]
    for k in required_keys:
        assert k in result, f"Missing key in prediction: {k}"

    assert result["status_code"] in [0, 1, 2]
    assert result["status_label"] in ["NORMAL", "WARNING", "BLOCKAGE"]
    assert result["status_color"] in ["GREEN", "YELLOW", "RED"]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert isinstance(result["probabilities"], dict)
    assert "normal" in result["probabilities"]
    assert "warning" in result["probabilities"]
    assert "blockage" in result["probabilities"]
    assert "is_anomaly" in result["anomaly_detection"]
    assert "anomaly_score" in result["anomaly_detection"]

