"""
FlowSentinel - Team 3 (ML & Simulation)
Step 6 Validation: Sequence Testing for Temporal Intelligence & Transient Spike Handling
"""

import time
from model_pipeline import ChutePredictor

def test_temporal_sequence_robustness():
    print("=" * 75)
    print("🧪 [Team 3 - Engineer 6] Step 6: Sequence & Transient Spike Resistance Test")
    print("=" * 75)

    predictor = ChutePredictor()

    # -------------------------------------------------------------
    # Test 1: Transient Spike Resistance
    # Scenario: Normal -> 1-frame vibration/weight noise spike -> Normal
    # Expected: No false CRITICAL blockage alert
    # -------------------------------------------------------------
    print("\n[Sequence Test 1] Single-Frame Transient Noise Spike:")
    predictor.history_buffer.clear()

    # Frame 1: Normal
    r1 = predictor.predict({"distance_cm": 55.0, "weight_kg": 320.0, "vibration_g": 3.2, "material_flow_rate_tph": 240.0})
    print(f"  • Frame 1 (Normal):    Status={r1['status_label']}, Risk={r1['diagnostic_breakdown']['chute_health_index']['risk_score']}/100")

    # Frame 2: Transient Noise Spike
    time.sleep(0.02)
    r2 = predictor.predict({"distance_cm": 55.0, "weight_kg": 750.0, "vibration_g": 11.0, "material_flow_rate_tph": 240.0})
    print(f"  • Frame 2 (Spike):     Status={r2['status_label']}, Anomaly={r2['anomaly_detection']['is_anomaly']}, Risk={r2['diagnostic_breakdown']['chute_health_index']['risk_score']}/100")

    # Frame 3: Normal return
    time.sleep(0.02)
    r3 = predictor.predict({"distance_cm": 55.0, "weight_kg": 320.0, "vibration_g": 3.2, "material_flow_rate_tph": 240.0})
    print(f"  • Frame 3 (Recovery):  Status={r3['status_label']}, Risk={r3['diagnostic_breakdown']['chute_health_index']['risk_score']}/100")

    assert r1["status_code"] == 0
    assert r3["status_code"] == 0
    assert r2["status_code"] != 2, "Transient spike MUST NOT trigger CRITICAL Blockage!"
    print("  ✓ PASS: Single-frame transient noise spike successfully absorbed without false blockage.")

    # -------------------------------------------------------------
    # Test 2: Progressive Buildup to Choke (Monotonic Risk Escalation)
    # Scenario: Normal -> Sidewall Buildup -> Full Choke
    # -------------------------------------------------------------
    print("\n[Sequence Test 2] Progressive Material Buildup to Choke:")
    predictor.history_buffer.clear()

    step_normal = {"distance_cm": 60.0, "weight_kg": 280.0, "vibration_g": 3.5, "material_flow_rate_tph": 250.0}
    step_warn   = {"distance_cm": 28.0, "weight_kg": 650.0, "vibration_g": 1.2, "material_flow_rate_tph": 120.0}
    step_block  = {"distance_cm": 7.0,  "weight_kg": 1150.0, "vibration_g": 0.18, "material_flow_rate_tph": 0.0}

    s1 = predictor.predict(step_normal)
    time.sleep(0.02)
    s2 = predictor.predict(step_warn)
    time.sleep(0.02)
    s3 = predictor.predict(step_block)

    risk1 = s1['diagnostic_breakdown']['chute_health_index']['risk_score']
    risk2 = s2['diagnostic_breakdown']['chute_health_index']['risk_score']
    risk3 = s3['diagnostic_breakdown']['chute_health_index']['risk_score']

    print(f"  • Stage 1 (Normal Flow):  Status={s1['status_label']}, Risk={risk1}/100")
    print(f"  • Stage 2 (Buildup):      Status={s2['status_label']}, Risk={risk2}/100")
    print(f"  • Stage 3 (Full Choke):   Status={s3['status_label']}, Risk={risk3}/100")

    assert risk1 < risk2 < risk3, "Risk score MUST be strictly monotonic during progressive choke!"
    assert s3["status_code"] == 2, "Stage 3 MUST trigger BLOCKAGE!"
    print("  ✓ PASS: Risk score strictly monotonic during progressive chute failure.")

    print("\n" + "=" * 75)
    print("✅ TEMPORAL INTELLIGENCE & SEQUENCE TESTS COMPLETE (100% PASS)")
    print("=" * 75)

if __name__ == "__main__":
    test_temporal_sequence_robustness()

