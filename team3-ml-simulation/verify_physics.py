"""
FlowSentinel - Team 3 (ML & Physics Simulation)
Phase 1 Deliverable: Physics Logic & Data Distribution Verification Suite
Engineer 6: Validation & Machine Learning Pipeline Preparation

Verifies:
1. Clearance-Weight Inverse Coupling (Correlation Analysis)
2. Kinetic Energy Dissipation during Blockage (Vibration Dampening Analysis)
3. Tri-Axial Decomposition Consistency (Vector magnitude)
4. Anomaly Characterization (Out-of-Distribution Profiles)
5. Sensor Boundary and Data Quality Constraints
"""

import os
import sys
import numpy as np
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_generator import ChutePhysicsGenerator

def run_physics_verification(n_samples: int = 10000):
    print("=" * 70)
    print("🔍 [Team 3 - Engineer 6] Initiating Phase 1 Physics & Data Verification")
    print("=" * 70)

    generator = ChutePhysicsGenerator(seed=42)
    df = generator.generate_dataset(n_samples=n_samples)

    # -------------------------------------------------------------
    # 1. Data Integrity & Completeness Check
    # -------------------------------------------------------------
    print("\n📋 [Test 1] Data Integrity & Boundary Constraints:")
    null_count = df.isnull().sum().sum()
    assert null_count == 0, f"Found {null_count} null values in generated dataset!"
    print(f"  ✓ Null Values: 0 ({n_samples} rows validated)")

    dist_valid = (df["distance_cm"] >= 0.0) & (df["distance_cm"] <= 120.0)
    weight_valid = (df["weight_kg"] >= 0.0) & (df["weight_kg"] <= 2000.0)
    vib_valid = (df["vibration_g"] >= 0.0) & (df["vibration_g"] <= 20.0)
    
    assert dist_valid.all(), "Distance sensor out-of-bounds detected!"
    assert weight_valid.all(), "Weight sensor out-of-bounds detected!"
    assert vib_valid.all(), "Vibration sensor out-of-bounds detected!"
    print("  ✓ Sensor Physical Boundaries: All sensor readings within safe operational limits")

    # -------------------------------------------------------------
    # 2. Physics Law 1: Clearance vs Weight Inverse Correlation
    # -------------------------------------------------------------
    print("\n⚖️ [Test 2] Physics Law 1: Clearance vs Mass Coupling (Normal & Warning & Blockage):")
    non_anomalies = df[df["is_anomaly"] == 0]
    corr_dist_weight = non_anomalies["distance_cm"].corr(non_anomalies["weight_kg"])
    print(f"  • Correlation r(Distance, Weight): {corr_dist_weight:.4f}")
    assert corr_dist_weight < -0.75, f"Expected strong negative correlation, got {corr_dist_weight}"
    print("  ✓ PASS: Strong inverse correlation confirmed. As material accumulates, clearance strictly decreases.")

    # -------------------------------------------------------------
    # 3. Physics Law 2: Kinetic Impact Energy Dissipation in Chokes
    # -------------------------------------------------------------
    print("\n⚡ [Test 3] Physics Law 2: Kinetic Oscillation & Chute Dampening:")
    norm_vib = non_anomalies[non_anomalies["state_label"] == 0]["vibration_g"]
    warn_vib = non_anomalies[non_anomalies["state_label"] == 1]["vibration_g"]
    blk_vib = non_anomalies[non_anomalies["state_label"] == 2]["vibration_g"]

    print(f"  • State 0 (Normal Flow) Vibration Mean:      {norm_vib.mean():.3f} G (RMS)")
    print(f"  • State 1 (Warning Buildup) Vibration Mean:  {warn_vib.mean():.3f} G (RMS)")
    print(f"  • State 2 (Critical Blockage) Vibration Mean:{blk_vib.mean():.3f} G (RMS)")

    assert blk_vib.mean() < 0.50, f"Expected blockage vibration < 0.50 G, got {blk_vib.mean():.3f}"
    assert norm_vib.mean() > 2.50, f"Expected normal vibration > 2.50 G, got {norm_vib.mean():.3f}"
    print("  ✓ PASS: Kinetic dissipation confirmed. Flow stoppage deadens impact oscillations.")

    # -------------------------------------------------------------
    # 4. Physics Law 3: Tri-Axial Vector Consistency
    # -------------------------------------------------------------
    print("\n📐 [Test 4] Physics Law 3: Tri-Axial Acceleration Magnitude Consistency:")
    calc_magnitude = np.sqrt(df["vibration_x"]**2 + df["vibration_y"]**2 + df["vibration_z"]**2)
    mag_diff = np.abs(calc_magnitude - df["vibration_g"])
    mean_diff = mag_diff.mean()
    print(f"  • Mean Vector Error |sqrt(x^2+y^2+z^2) - G_rms|: {mean_diff:.4f} G")
    assert mean_diff < 0.15, f"Vector magnitude mismatch too large: {mean_diff}"
    print("  ✓ PASS: Tri-axial acceleration vectors mathematically agree with scalar RMS.")

    # -------------------------------------------------------------
    # 5. Class & Anomaly Balance Breakdown
    # -------------------------------------------------------------
    print("\n📊 [Test 5] Dataset Distribution & Class Breakdown:")
    counts = df["state_label"].value_counts().to_dict()
    anomaly_count = int(df["is_anomaly"].sum())

    print(f"  • Class 0 (NORMAL):    {counts.get(0, 0)} ({counts.get(0, 0)/n_samples*100:.1f}%)")
    print(f"  • Class 1 (WARNING):   {counts.get(1, 0)} ({counts.get(1, 0)/n_samples*100:.1f}%)")
    print(f"  • Class 2 (BLOCKAGE):  {counts.get(2, 0)} ({counts.get(2, 0)/n_samples*100:.1f}%)")
    print(f"  • Anomalies (IForest): {anomaly_count} ({anomaly_count/n_samples*100:.1f}%)")

    print("\n" + "=" * 70)
    print("✅ PHASE 1 PHYSICS VERIFICATION COMPLETE: ALL CHECKS PASSED (100%)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_physics_verification()

