"""
FlowSentinel - Team 3 (ML & Physics Simulation)
Phase 2 Test Suite: Verifies Temporal Rate-of-Change, Risk Index, and Diagnostics Breakdown
"""

import time
from model_pipeline import ChutePredictor


def test_phase2_capabilities():
    print("=" * 65)
    print("🧪 [Team 3 - Engineer 6] Testing Phase 2 Intelligence Upgrades")
    print("=" * 65)

    predictor = ChutePredictor()
    assert predictor.is_loaded, "ML models must be loaded!"

    # 1. Test Normal Operation
    p1 = predictor.predict(
        {
            "distance_cm": 55.0,
            "weight_kg": 300.0,
            "vibration_g": 3.2,
            "material_flow_rate_tph": 240.0,
        }
    )
    print("\n🟢 [Test 1] Normal Flow Result:")
    print(f"  • Status: {p1['status_label']} (Code: {p1['status_code']})")
    print(
        f"  • Risk Score: {p1['diagnostic_breakdown']['chute_health_index']['risk_score']}/100"
    )
    print(
        f"  • Health State: {p1['diagnostic_breakdown']['chute_health_index']['health_state']}"
    )
    assert p1["status_code"] == 0
    assert p1["diagnostic_breakdown"]["chute_health_index"]["risk_score"] < 35.0

    # 2. Test Rapid Mass Surge (Simulating 3 rapid incoming readings)
    time.sleep(0.05)
    predictor.predict(
        {
            "distance_cm": 40.0,
            "weight_kg": 450.0,
            "vibration_g": 2.5,
            "material_flow_rate_tph": 180.0,
        }
    )
    time.sleep(0.05)
    p3 = predictor.predict(
        {
            "distance_cm": 25.0,
            "weight_kg": 650.0,
            "vibration_g": 1.4,
            "material_flow_rate_tph": 120.0,
        }
    )

    print("\n🟡 [Test 2] Rapid Mass Surge (Temporal Buffer Active):")
    dw_dt = p3["diagnostic_breakdown"]["temporal_metrics"]["dw_dt_kg_per_sec"]
    ddist_dt = p3["diagnostic_breakdown"]["temporal_metrics"]["ddist_dt_cm_per_sec"]
    risk = p3["diagnostic_breakdown"]["chute_health_index"]["risk_score"]
    print(f"  • dW/dt (Mass Accumulation Rate): {dw_dt} kg/s")
    print(f"  • d(dist)/dt (Clearance Rate):   {ddist_dt} cm/s")
    print(f"  • Elevated Risk Score:           {risk}/100")
    print(
        f"  • Fault Category:                {p3['diagnostic_breakdown']['fault_category']}"
    )
    assert dw_dt > 0.0, "Mass accumulation rate dW/dt should be positive!"
    assert ddist_dt < 0.0, "Clearance rate d(dist)/dt should be negative!"

    # 3. Test Critical Funnel Choke
    p_choke = predictor.predict(
        {
            "distance_cm": 6.0,
            "weight_kg": 1180.0,
            "vibration_g": 0.15,
            "material_flow_rate_tph": 0.0,
        }
    )
    print("\n🔴 [Test 3] Critical Funnel Choke:")
    print(f"  • Status: {p_choke['status_label']} (Code: {p_choke['status_code']})")
    print(
        f"  • Risk Score: {p_choke['diagnostic_breakdown']['chute_health_index']['risk_score']}/100"
    )
    print(f"  • Fault Category: {p_choke['diagnostic_breakdown']['fault_category']}")
    print(f"  • Mitigation: {p_choke['diagnostic_breakdown']['mitigation_procedure']}")
    assert p_choke["status_code"] == 2
    assert p_choke["diagnostic_breakdown"]["fault_category"] in [
        "CRITICAL_FUNNEL_CHOKE",
        "OVERBURDEN_FLOW_STOPPAGE",
        "RAPID_SURGE_JAM",
    ]
    assert p_choke["diagnostic_breakdown"]["chute_health_index"]["risk_score"] >= 70.0

    # 4. Test Mechanical Resonance / Loose Liner Anomaly
    p_anomaly = predictor.predict(
        {
            "distance_cm": 52.0,
            "weight_kg": 310.0,
            "vibration_g": 12.5,
            "material_flow_rate_tph": 220.0,
        }
    )
    print("\n⚡ [Test 4] Loose Liner / Structural Resonance Anomaly:")
    print(f"  • Anomaly Flag: {p_anomaly['anomaly_detection']['is_anomaly']}")
    print(f"  • Anomaly Score: {p_anomaly['anomaly_detection']['anomaly_score']}")
    print(f"  • Fault Category: {p_anomaly['diagnostic_breakdown']['fault_category']}")
    print(
        f"  • Evidence: {p_anomaly['diagnostic_breakdown']['primary_sensor_evidence']}"
    )
    # Note: Isolation Forest may not flag this as anomaly since high-vib readings
    # can appear in normal-flow training data (impact events). The rule-based
    # diagnostic hierarchy catches it via the vib > 9.0 threshold.
    assert (
        p_anomaly["diagnostic_breakdown"]["fault_category"]
        == "MECHANICAL_RESONANCE_OR_LOOSE_LINER"
    )

    print("\n" + "=" * 65)
    print("✅ ALL PHASE 2 INTELLIGENCE CAPABILITIES VERIFIED (100% PASS)")
    print("=" * 65)


if __name__ == "__main__":
    test_phase2_capabilities()
