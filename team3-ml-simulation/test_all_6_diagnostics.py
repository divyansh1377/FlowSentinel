"""
FlowSentinel - Team 3 (ML & Simulation)
Step 7 Validation: Verification Suite for All 6 Industrial Diagnostic Categories

Categories Tested:
1. CRITICAL_FUNNEL_CHOKE
2. RAPID_SURGE_JAM
3. SLUGGISH_SIDEWALL_RESTRICTION
4. MECHANICAL_RESONANCE_OR_LOOSE_LINER
5. SENSOR_OPTICAL_BLINDING
6. LOAD_CELL_DRIFT_OR_FAULT
"""

import time
from model_pipeline import ChutePredictor

def run_6_diagnostics_validation():
    print("=" * 75)
    print("🧪 [Team 3 - Engineer 6] Step 7: Validating All 6 Diagnostic Categories")
    print("=" * 75)

    predictor = ChutePredictor()
    results = []

    test_cases = [
        {
            "name": "1. CRITICAL_FUNNEL_CHOKE",
            "expected_cat": "CRITICAL_FUNNEL_CHOKE",
            "sequence": [
                {"distance_cm": 8.0, "weight_kg": 1150.0, "vibration_g": 0.18, "material_flow_rate_tph": 0.0}
            ]
        },
        {
            "name": "2. RAPID_SURGE_JAM",
            "expected_cat": "RAPID_SURGE_JAM",
            "sequence": [
                {"distance_cm": 50.0, "weight_kg": 300.0, "vibration_g": 3.0, "material_flow_rate_tph": 200.0},
                {"distance_cm": 14.0, "weight_kg": 950.0, "vibration_g": 0.25, "material_flow_rate_tph": 10.0}  # Rapid surge
            ]
        },
        {
            "name": "3. SLUGGISH_SIDEWALL_RESTRICTION",
            "expected_cat": "SLUGGISH_SIDEWALL_RESTRICTION",
            "sequence": [
                {"distance_cm": 26.0, "weight_kg": 680.0, "vibration_g": 1.1, "material_flow_rate_tph": 110.0}
            ]
        },
        {
            "name": "4. MECHANICAL_RESONANCE_OR_LOOSE_LINER",
            "expected_cat": "MECHANICAL_RESONANCE_OR_LOOSE_LINER",
            "sequence": [
                {"distance_cm": 52.0, "weight_kg": 310.0, "vibration_g": 12.8, "material_flow_rate_tph": 220.0}
            ]
        },
        {
            "name": "5. SENSOR_OPTICAL_BLINDING",
            "expected_cat": "SENSOR_OPTICAL_BLINDING",
            "sequence": [
                {"distance_cm": 6.0, "weight_kg": 20.0, "vibration_g": 2.5, "material_flow_rate_tph": 190.0}
            ]
        },
        {
            "name": "6. LOAD_CELL_DRIFT_OR_FAULT",
            "expected_cat": "LOAD_CELL_DRIFT_OR_FAULT",
            "sequence": [
                {"distance_cm": 55.0, "weight_kg": 1350.0, "vibration_g": 6.2, "material_flow_rate_tph": 240.0}
            ]
        }
    ]

    for tc in test_cases:
        print(f"\n--- Testing: {tc['name']} ---")
        # Clear predictor sequence for isolated test case
        predictor.history_buffer.clear()
        
        last_res = None
        for step in tc["sequence"]:
            time.sleep(0.02)
            last_res = predictor.predict(step)

        diag = last_res["diagnostic_breakdown"]
        actual_cat = diag["fault_category"]
        pass_fail = "PASS" if actual_cat == tc["expected_cat"] else "FAIL"

        print(f"  • Input Telemetry: {tc['sequence'][-1]}")
        print(f"  • ML Prediction:   {last_res['status_label']} (Code {last_res['status_code']})")
        print(f"  • Anomaly Flag:    {last_res['anomaly_detection']['is_anomaly']}")
        print(f"  • Risk Score:      {diag['chute_health_index']['risk_score']}/100")
        print(f"  • Actual Category: {actual_cat}")
        print(f"  • Expected:        {tc['expected_cat']}")
        print(f"  • Result:          [{pass_fail}]")

        results.append({
            "name": tc["name"],
            "expected": tc["expected_cat"],
            "actual": actual_cat,
            "passed": pass_fail == "PASS",
            "risk_score": diag['chute_health_index']['risk_score'],
            "status": last_res['status_label']
        })

    print("\n" + "=" * 75)
    all_passed = all(r["passed"] for r in results)
    print(f"✅ DIAGNOSTIC VERIFICATION RESULT: {'ALL 6 PASSED (100%)' if all_passed else 'SOME FAILED'}")
    print("=" * 75)
    return results

if __name__ == "__main__":
    run_6_diagnostics_validation()

