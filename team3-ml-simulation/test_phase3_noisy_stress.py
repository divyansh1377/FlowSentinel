"""
FlowSentinel — Team 3 (ML & Simulation)
Phase 3 Hardening: Noisy Temporal Stress Tests, Transient Spike Validation,
Six-Diagnostic Robustness, and Temporal Buffer Verification.

TASK 1 — Noisy temporal sequences for all 6 diagnostic categories
TASK 2 — Transient spike / false-alarm validation (1-frame, 3-frame, 5-frame,
          sustained, recovery) across mass, distance, and vibration axes
TASK 3 — Six-diagnostic robustness under clean / mild / moderate noise / recovery
TASK 4 — Temporal buffer behavioral validation (state leak, persistence, recovery)

All tests use seeded numpy.random for deterministic / reproducible results.
Run from team3-ml-simulation/ directory:
    python test_phase3_noisy_stress.py
"""

import sys
import time
import numpy as np
from collections import defaultdict
from model_pipeline import ChutePredictor

# ── Seeded RNG for deterministic noise ───────────────────────────────────────
RNG = np.random.default_rng(seed=42)

# ── Canonical sensor states ───────────────────────────────────────────────────
NORMAL_FLOW   = {"distance_cm": 55.0, "weight_kg": 300.0, "vibration_g": 3.2,  "material_flow_rate_tph": 240.0}
WARN_BUILDUP  = {"distance_cm": 28.0, "weight_kg": 650.0, "vibration_g": 1.2,  "material_flow_rate_tph": 120.0}
BLOCKAGE_CHOKE= {"distance_cm": 8.0,  "weight_kg": 1150.0,"vibration_g": 0.18, "material_flow_rate_tph": 0.0}
MECH_RESON    = {"distance_cm": 52.0, "weight_kg": 310.0, "vibration_g": 12.8, "material_flow_rate_tph": 220.0}
OPTICAL_BLIND = {"distance_cm": 6.0,  "weight_kg": 20.0,  "vibration_g": 2.5,  "material_flow_rate_tph": 190.0}
LOAD_CELL_FAULT={"distance_cm": 55.0, "weight_kg": 1350.0,"vibration_g": 6.2,  "material_flow_rate_tph": 240.0}

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS    = defaultdict(list)


def _sleep():
    """20 ms between frames to allow meaningful dW/dt / ddist/dt."""
    time.sleep(0.020)


def _noisy(base: dict, noise_level: float) -> dict:
    """Add seeded Gaussian noise to a telemetry dict.
    noise_level == 0 → clean, 0.03 → mild (~3%), 0.07 → moderate (~7%).
    """
    out = {}
    # Per-channel noise scales (physical units)
    scales = {
        "distance_cm":           max(0.5, base["distance_cm"]  * noise_level),
        "weight_kg":             max(5.0, base["weight_kg"]     * noise_level),
        "vibration_g":           max(0.05, base["vibration_g"]  * noise_level),
        "material_flow_rate_tph": max(2.0, base["material_flow_rate_tph"] * noise_level),
    }
    for k, v in base.items():
        delta = float(RNG.normal(0.0, scales[k]))
        out[k] = max(0.0, v + delta)
    return out


def _check(test_name: str, condition: bool, reason: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        RESULTS[test_name].append("PASS")
        print(f"    ✓ PASS: {reason}")
    else:
        FAIL_COUNT += 1
        RESULTS[test_name].append("FAIL")
        print(f"    ✗ FAIL: {reason}")


def _run_sequence(predictor: ChutePredictor, frames: list, sleep: bool = True) -> list:
    """Run a list of telemetry dicts through predictor; return list of results."""
    results = []
    for i, frame in enumerate(frames):
        if sleep and i > 0:
            _sleep()
        results.append(predictor.predict(frame))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — Noisy Temporal Sequences for all 6 Diagnostic Categories
# ══════════════════════════════════════════════════════════════════════════════

def task1_noisy_temporal_sequences():
    """
    For each diagnostic category, run a realistic temporal sequence:
      normal conditions → gradual change → sensor noise → transient fluctuations
      → sustained abnormal condition → recovery back to normal.
    Verify that the diagnostic engine behaves correctly over time.
    """
    print("\n" + "═" * 75)
    print("TASK 1 — Noisy Temporal Sequence Testing (all 6 diagnostic categories)")
    print("═" * 75)

    predictor = ChutePredictor()

    # ── 1a. CRITICAL_FUNNEL_CHOKE: gradual buildup with noise ─────────────────
    print("\n[1a] CRITICAL_FUNNEL_CHOKE — gradual buildup sequence with noise:")
    predictor.history_buffer.clear()
    frames = []
    # 5 normal frames with mild noise
    for _ in range(5):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    # 4 progressive narrowing frames (warning band)
    for step in range(4):
        frames.append(_noisy({
            "distance_cm": 40.0 - step * 8.0,
            "weight_kg": 450.0 + step * 120.0,
            "vibration_g": 2.0 - step * 0.4,
            "material_flow_rate_tph": 160.0 - step * 30.0
        }, 0.04))
    # 3 sustained choke frames
    for _ in range(3):
        frames.append(_noisy(BLOCKAGE_CHOKE, 0.03))
    results = _run_sequence(predictor, frames)

    # The last 3 frames must be BLOCKAGE
    choke_results = results[-3:]
    all_blockage = all(r["status_code"] == 2 for r in choke_results)
    _check("1a_choke_blockage", all_blockage,
           "Sustained choke frames classified as BLOCKAGE")

    # Risk must escalate: average risk of last-3 > average risk of first-5
    early_risk = np.mean([r["diagnostic_breakdown"]["chute_health_index"]["risk_score"] for r in results[:5]])
    late_risk  = np.mean([r["diagnostic_breakdown"]["chute_health_index"]["risk_score"] for r in results[-3:]])
    _check("1a_risk_escalation", late_risk > early_risk,
           f"Risk escalated from {early_risk:.1f} (normal) to {late_risk:.1f} (choke)")

    # Diagnostic category of final frame
    final_cat = results[-1]["diagnostic_breakdown"]["fault_category"]
    _check("1a_category", final_cat in ("CRITICAL_FUNNEL_CHOKE", "RAPID_SURGE_JAM", "OVERBURDEN_FLOW_STOPPAGE"),
           f"Final category is a valid choke variant: {final_cat}")

    # Normal frames must not trigger BLOCKAGE
    normal_no_block = all(r["status_code"] != 2 for r in results[:5])
    _check("1a_no_false_blockage_in_normal", normal_no_block,
           "No false BLOCKAGE during normal operating noise")

    # ── 1b. RAPID_SURGE_JAM: sudden surge with noise ──────────────────────────
    print("\n[1b] RAPID_SURGE_JAM — sudden mass surge sequence with noise:")
    predictor.history_buffer.clear()
    frames = []
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    # Rapid surge: 300→950 kg in one step
    frames.append(_noisy({"distance_cm": 14.0, "weight_kg": 950.0,
                           "vibration_g": 0.25, "material_flow_rate_tph": 10.0}, 0.02))
    results = _run_sequence(predictor, frames)

    pre_status  = [r["status_code"] for r in results[:3]]
    surge_result = results[-1]
    _check("1b_pre_surge_normal", all(c == 0 for c in pre_status),
           "Pre-surge frames stay NORMAL")
    _check("1b_surge_blockage", surge_result["status_code"] == 2,
           f"Surge frame classified as BLOCKAGE (got {surge_result['status_label']})")
    surge_cat = surge_result["diagnostic_breakdown"]["fault_category"]
    _check("1b_surge_category", surge_cat in ("RAPID_SURGE_JAM", "CRITICAL_FUNNEL_CHOKE", "OVERBURDEN_FLOW_STOPPAGE"),
           f"Surge category is a blockage variant: {surge_cat}")

    # ── 1c. SLUGGISH_SIDEWALL_RESTRICTION: sustained warning + noise ──────────
    print("\n[1c] SLUGGISH_SIDEWALL_RESTRICTION — sustained warning with noise + recovery:")
    predictor.history_buffer.clear()
    frames = []
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    for _ in range(5):
        frames.append(_noisy(WARN_BUILDUP, 0.04))
    # Recovery
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    results = _run_sequence(predictor, frames)

    warn_results   = results[3:8]
    recover_results= results[8:]
    warn_any       = any(r["status_code"] >= 1 for r in warn_results)
    recover_ok     = all(r["status_code"] == 0 for r in recover_results)
    _check("1c_warning_triggered", warn_any,
           "Warning band produces WARNING or higher status")
    _check("1c_recovery_ok", recover_ok,
           "Recovery back to NORMAL after clearing warning condition")

    # ── 1d. MECHANICAL_RESONANCE_OR_LOOSE_LINER: high-vib spike + noise ──────
    print("\n[1d] MECHANICAL_RESONANCE_OR_LOOSE_LINER — high-vibration spike with noise:")
    predictor.history_buffer.clear()
    frames = []
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    for _ in range(3):
        frames.append(_noisy(MECH_RESON, 0.04))
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    results = _run_sequence(predictor, frames)

    # High-vib frames must not be classified as BLOCKAGE (they're a mechanical anomaly)
    vib_frames = results[3:6]
    no_false_block = all(r["status_code"] != 2 for r in vib_frames)
    _check("1d_mech_no_false_blockage", no_false_block,
           "High-vibration mechanical spike NOT classified as BLOCKAGE")

    # Diagnostic category of high-vib frames
    vib_cats = [r["diagnostic_breakdown"]["fault_category"] for r in vib_frames]
    correct_cat = all(c == "MECHANICAL_RESONANCE_OR_LOOSE_LINER" for c in vib_cats)
    _check("1d_mech_category", correct_cat,
           f"All high-vib frames → MECHANICAL_RESONANCE_OR_LOOSE_LINER: {vib_cats}")

    # Recovery: returns to NORMAL
    recovery_ok = all(r["status_code"] == 0 for r in results[6:])
    _check("1d_recovery_ok", recovery_ok,
           "Recovery to NORMAL after vibration spike subsides")

    # ── 1e. SENSOR_OPTICAL_BLINDING: sensor blinding with noise ──────────────
    print("\n[1e] SENSOR_OPTICAL_BLINDING — blinding event with surrounding normal frames:")
    predictor.history_buffer.clear()
    frames = []
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    for _ in range(3):
        frames.append(_noisy(OPTICAL_BLIND, 0.03))
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    results = _run_sequence(predictor, frames)

    blind_cats = [r["diagnostic_breakdown"]["fault_category"] for r in results[3:6]]
    blind_correct = all(c == "SENSOR_OPTICAL_BLINDING" for c in blind_cats)
    _check("1e_optical_category", blind_correct,
           f"Optical blinding frames categorised correctly: {blind_cats}")

    # Must not classify blinding as physical BLOCKAGE (weight is negligible)
    blind_no_block = all(r["status_code"] != 2 for r in results[3:6])
    _check("1e_optical_no_false_blockage", blind_no_block,
           "Optical blinding NOT classified as physical BLOCKAGE")

    # Recovery
    recover_ok = all(r["status_code"] == 0 for r in results[6:])
    _check("1e_recovery_ok", recover_ok,
           "Normal status restored after blinding event")

    # ── 1f. LOAD_CELL_DRIFT_OR_FAULT: phantom high weight + noise ────────────
    print("\n[1f] LOAD_CELL_DRIFT_OR_FAULT — phantom weight reading with noise:")
    predictor.history_buffer.clear()
    frames = []
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    for _ in range(3):
        frames.append(_noisy(LOAD_CELL_FAULT, 0.03))
    for _ in range(3):
        frames.append(_noisy(NORMAL_FLOW, 0.04))
    results = _run_sequence(predictor, frames)

    fault_cats = [r["diagnostic_breakdown"]["fault_category"] for r in results[3:6]]
    fault_correct = all(c == "LOAD_CELL_DRIFT_OR_FAULT" for c in fault_cats)
    _check("1f_loadcell_category", fault_correct,
           f"Load cell drift frames categorised correctly: {fault_cats}")

    # Physical clearance is open, so must NOT be classified as BLOCKAGE
    fault_no_block = all(r["status_code"] != 2 for r in results[3:6])
    _check("1f_loadcell_no_false_blockage", fault_no_block,
           "Load cell fault NOT classified as physical BLOCKAGE")

    recover_ok = all(r["status_code"] == 0 for r in results[6:])
    _check("1f_recovery_ok", recover_ok,
           "Normal status restored after load cell fault event")


# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — Transient Spike / False-Alarm Validation
# ══════════════════════════════════════════════════════════════════════════════

def task2_transient_spike_validation():
    """
    Validate transient spike handling:
      A. 1-frame spike   B. 3-frame spike   C. 5-frame spike
      D. Sustained abnormal condition       E. Spike followed by recovery
    Across: mass/load, distance/clearance, vibration.
    """
    print("\n" + "═" * 75)
    print("TASK 2 — Transient Spike / False-Alarm Validation")
    print("═" * 75)

    predictor = ChutePredictor()

    def _warmup():
        """Prime the temporal buffer with 3 normal frames before each test."""
        predictor.history_buffer.clear()
        for _ in range(3):
            predictor.predict(_noisy(NORMAL_FLOW, 0.02))
            _sleep()

    # ── A. 1-frame spike (mass) ───────────────────────────────────────────────
    print("\n[2A] 1-frame mass spike:")
    _warmup()
    spike_result = predictor.predict({
        "distance_cm": 55.0, "weight_kg": 1100.0,
        "vibration_g": 3.0, "material_flow_rate_tph": 240.0
    })
    _sleep()
    recovery_result = predictor.predict(_noisy(NORMAL_FLOW, 0.02))

    _check("2A_1frame_not_blockage", spike_result["status_code"] != 2,
           f"1-frame mass spike NOT classified as BLOCKAGE (got {spike_result['status_label']})")
    _check("2A_recovery", recovery_result["status_code"] == 0,
           "Recovery to NORMAL after 1-frame spike")

    # ── A. 1-frame spike (vibration) ─────────────────────────────────────────
    print("\n[2A-vib] 1-frame vibration spike:")
    _warmup()
    vib_spike = predictor.predict({
        "distance_cm": 55.0, "weight_kg": 300.0,
        "vibration_g": 12.5, "material_flow_rate_tph": 240.0
    })
    _sleep()
    vib_recovery = predictor.predict(_noisy(NORMAL_FLOW, 0.02))

    _check("2A_vib_not_blockage", vib_spike["status_code"] != 2,
           f"1-frame vib spike NOT classified as BLOCKAGE (got {vib_spike['status_label']})")
    _check("2A_vib_mech_cat", vib_spike["diagnostic_breakdown"]["fault_category"]
           == "MECHANICAL_RESONANCE_OR_LOOSE_LINER",
           "1-frame vib spike → MECHANICAL_RESONANCE_OR_LOOSE_LINER")
    _check("2A_vib_recovery", vib_recovery["status_code"] == 0,
           "Recovery to NORMAL after vib spike")

    # ── A. 1-frame spike (distance/clearance) ────────────────────────────────
    print("\n[2A-dist] 1-frame distance spike (false low clearance):")
    _warmup()
    dist_spike = predictor.predict({
        "distance_cm": 5.0, "weight_kg": 300.0,
        "vibration_g": 3.2, "material_flow_rate_tph": 240.0
    })
    _sleep()
    dist_recovery = predictor.predict(_noisy(NORMAL_FLOW, 0.02))

    # Low dist with normal weight can go WARNING or higher — it should NOT be
    # classified as CRITICAL_FUNNEL_CHOKE since weight is low/normal
    final_cat = dist_spike["diagnostic_breakdown"]["fault_category"]
    _check("2A_dist_not_funnel_choke",
           final_cat != "CRITICAL_FUNNEL_CHOKE",
           f"1-frame dist spike (normal weight) NOT → CRITICAL_FUNNEL_CHOKE; got {final_cat}")
    _check("2A_dist_recovery", dist_recovery["status_code"] == 0,
           "Recovery after 1-frame dist spike")

    # ── B. 3-frame spike (mass) ───────────────────────────────────────────────
    print("\n[2B] 3-frame mass spike:")
    _warmup()
    spike_frames = []
    for _ in range(3):
        spike_frames.append(predictor.predict({
            "distance_cm": 55.0, "weight_kg": 1050.0,
            "vibration_g": 3.0, "material_flow_rate_tph": 240.0
        }))
        _sleep()
    _sleep()
    b_recovery = predictor.predict(_noisy(NORMAL_FLOW, 0.02))

    # A 3-frame mass-only spike (clearance still open) should stay WARNING, not BLOCKAGE
    # This is physically implausible as blockage without distance reduction
    b_not_blockage = all(r["status_code"] != 2 for r in spike_frames)
    _check("2B_3frame_not_blockage", b_not_blockage,
           f"3-frame mass spike (clearance open) stays below BLOCKAGE")
    _check("2B_recovery", b_recovery["status_code"] == 0,
           "Recovery after 3-frame spike")

    # ── C. 5-frame spike (vibration) ─────────────────────────────────────────
    print("\n[2C] 5-frame vibration spike:")
    _warmup()
    c_frames = []
    for _ in range(5):
        c_frames.append(predictor.predict({
            "distance_cm": 55.0, "weight_kg": 300.0,
            "vibration_g": 11.5, "material_flow_rate_tph": 240.0
        }))
        _sleep()
    c_recovery = predictor.predict(_noisy(NORMAL_FLOW, 0.02))

    # Vibration-only spike should always go to MECHANICAL_RESONANCE, never BLOCKAGE
    c_no_block = all(r["status_code"] != 2 for r in c_frames)
    c_mech     = all(r["diagnostic_breakdown"]["fault_category"]
                     == "MECHANICAL_RESONANCE_OR_LOOSE_LINER" for r in c_frames)
    _check("2C_5frame_vib_not_blockage", c_no_block,
           "5-frame vib spike never classified as BLOCKAGE")
    _check("2C_5frame_vib_mech_cat", c_mech,
           "5-frame vib spike always → MECHANICAL_RESONANCE_OR_LOOSE_LINER")
    _check("2C_recovery", c_recovery["status_code"] == 0,
           "Recovery after 5-frame vib spike")

    # ── D. Sustained abnormal condition (progressive blockage) ────────────────
    print("\n[2D] Sustained blockage condition (D: 8 sustained frames):")
    predictor.history_buffer.clear()
    d_frames = []
    for _ in range(3):
        d_frames.append(predictor.predict(_noisy(NORMAL_FLOW, 0.03)))
        _sleep()
    for _ in range(5):
        d_frames.append(predictor.predict(_noisy(BLOCKAGE_CHOKE, 0.02)))
        _sleep()

    sustained = d_frames[3:]
    sustained_blockage = all(r["status_code"] == 2 for r in sustained)
    _check("2D_sustained_blockage", sustained_blockage,
           f"Sustained choke frames all BLOCKAGE ({[r['status_label'] for r in sustained]})")
    risk_vals = [r["diagnostic_breakdown"]["chute_health_index"]["risk_score"] for r in sustained]
    _check("2D_sustained_high_risk", all(rv >= 70.0 for rv in risk_vals),
           f"Sustained blockage risk >= 70 on all frames: {risk_vals}")

    # ── E. Spike followed by full recovery ────────────────────────────────────
    print("\n[2E] Spike + full recovery sequence:")
    predictor.history_buffer.clear()
    pre    = [predictor.predict(_noisy(NORMAL_FLOW, 0.03)) for _ in range(3)]
    [_sleep() for _ in range(3)]
    spike  = predictor.predict({"distance_cm": 8.0, "weight_kg": 1200.0,
                                 "vibration_g": 0.2, "material_flow_rate_tph": 0.0})
    _sleep()
    post   = []
    for _ in range(5):
        post.append(predictor.predict(_noisy(NORMAL_FLOW, 0.03)))
        _sleep()

    _check("2E_spike_is_blockage", spike["status_code"] == 2,
           "Spike correctly classified as BLOCKAGE")
    _check("2E_recovery_returns_normal", all(r["status_code"] == 0 for r in post[-3:]),
           f"Last 3 recovery frames all NORMAL: {[r['status_label'] for r in post[-3:]]}")
    # Risk must fall after recovery
    spike_risk   = spike["diagnostic_breakdown"]["chute_health_index"]["risk_score"]
    recover_risk = np.mean([r["diagnostic_breakdown"]["chute_health_index"]["risk_score"]
                            for r in post[-3:]])
    _check("2E_risk_drops", recover_risk < spike_risk,
           f"Risk drops from {spike_risk} (spike) to {recover_risk:.1f} (recovery)")


# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — Six-Diagnostic Robustness (clean / mild / moderate / recovery)
# ══════════════════════════════════════════════════════════════════════════════

def task3_diagnostic_robustness():
    """
    For each of the 6 diagnostic categories, test diagnostic stability under:
      clean signal, mild noise (3%), moderate noise (7%),
      short transient disturbance, sustained fault, and recovery.
    """
    print("\n" + "═" * 75)
    print("TASK 3 — Six-Diagnostic Robustness Under Noise Levels")
    print("═" * 75)

    predictor = ChutePredictor()

    categories = [
        ("CRITICAL_FUNNEL_CHOKE",            BLOCKAGE_CHOKE,  2),
        ("RAPID_SURGE_JAM",                   None,            2),   # needs sequence
        ("SLUGGISH_SIDEWALL_RESTRICTION",    WARN_BUILDUP,    1),
        ("MECHANICAL_RESONANCE_OR_LOOSE_LINER", MECH_RESON,   0),
        ("SENSOR_OPTICAL_BLINDING",          OPTICAL_BLIND,   0),
        ("LOAD_CELL_DRIFT_OR_FAULT",         LOAD_CELL_FAULT, 0),
    ]

    for cat_name, base_state, expected_status in categories:
        print(f"\n  ── {cat_name} ──")

        if cat_name == "RAPID_SURGE_JAM":
            # RAPID_SURGE_JAM requires a temporal sequence to generate dW/dt > 50
            for noise_label, noise_lvl in [("clean", 0.0), ("mild", 0.03), ("moderate", 0.06)]:
                predictor.history_buffer.clear()
                predictor.predict(_noisy(NORMAL_FLOW, noise_lvl))
                _sleep()
                result = predictor.predict(_noisy(
                    {"distance_cm": 14.0, "weight_kg": 950.0,
                     "vibration_g": 0.25, "material_flow_rate_tph": 10.0},
                    noise_lvl
                ))
                cat_got = result["diagnostic_breakdown"]["fault_category"]
                # RAPID_SURGE_JAM or valid blockage fallback is acceptable
                ok = result["status_code"] == 2
                _check(f"3_{cat_name}_{noise_label}",
                       ok,
                       f"{noise_label} → status BLOCKAGE ({cat_got})")
            continue

        for noise_label, noise_lvl in [("clean", 0.0), ("mild", 0.03), ("moderate", 0.07)]:
            predictor.history_buffer.clear()
            # Feed 3 frames of the fault state
            results = []
            for _ in range(3):
                results.append(predictor.predict(_noisy(base_state, noise_lvl)))
                _sleep()
            last = results[-1]
            cat_got = last["diagnostic_breakdown"]["fault_category"]
            status_got = last["status_code"]
            # Status must be stable at expected level
            _check(f"3_{cat_name}_{noise_label}_status",
                   status_got == expected_status,
                   f"{noise_label} → status {STATUS_LABELS[status_got]} (expected {STATUS_LABELS[expected_status]})")
            # Category must be correct
            _check(f"3_{cat_name}_{noise_label}_cat",
                   cat_got == cat_name,
                   f"{noise_label} → category {cat_got}")

        # Short transient disturbance test: 1 normal frame, 1 fault frame, verify fault caught
        predictor.history_buffer.clear()
        predictor.predict(_noisy(NORMAL_FLOW, 0.03))
        _sleep()
        fault_result = predictor.predict(_noisy(base_state, 0.03))
        _check(f"3_{cat_name}_transient_single_frame",
               fault_result["diagnostic_breakdown"]["fault_category"] == cat_name,
               f"Single fault frame → correct category {cat_name}")

        # Recovery: after 3 fault frames, 3 normal frames should return to NORMAL
        predictor.history_buffer.clear()
        for _ in range(3):
            predictor.predict(_noisy(base_state, 0.03))
            _sleep()
        for _ in range(3):
            r = predictor.predict(_noisy(NORMAL_FLOW, 0.03))
            _sleep()
        recover_status = r["status_code"]
        _check(f"3_{cat_name}_recovery",
               recover_status == 0,
               f"After fault+recovery: status {STATUS_LABELS[recover_status]} (expected NORMAL)")


# ══════════════════════════════════════════════════════════════════════════════
# TASK 4 — Temporal Buffer Behavioral Validation
# ══════════════════════════════════════════════════════════════════════════════

STATUS_LABELS = {0: "NORMAL", 1: "WARNING", 2: "BLOCKAGE"}

def task4_temporal_buffer_validation():
    """
    Verify:
    1. Fresh buffer returns zero temporal derivatives for first frame.
    2. After clearing, buffer starts fresh (no state leak).
    3. dW/dt sign correctly reflects accumulation vs. depletion.
    4. Buffer does not produce false persistent alarms after recovery.
    5. Buffer rolls correctly at max capacity (10 frames).
    6. Vibration std tracks actual variance in sequence.
    """
    print("\n" + "═" * 75)
    print("TASK 4 — Temporal Buffer Behavioral Validation")
    print("═" * 75)

    predictor = ChutePredictor()

    # 4.1 Fresh buffer: first frame yields zero temporal derivatives
    print("\n[4.1] Fresh buffer returns zero dW/dt on first frame:")
    predictor.history_buffer.clear()
    r = predictor.predict(NORMAL_FLOW)
    dw_dt_first = r["diagnostic_breakdown"]["temporal_metrics"]["dw_dt_kg_per_sec"]
    _check("4.1_first_frame_zero_dw_dt", abs(dw_dt_first) < 1e-3,
           f"First frame dW/dt = {dw_dt_first} (expected 0.0)")

    # 4.2 Buffer clear resets state
    print("\n[4.2] Buffer clear eliminates prior state:")
    predictor.history_buffer.clear()
    predictor.predict(BLOCKAGE_CHOKE)
    _sleep()
    predictor.history_buffer.clear()
    r2 = predictor.predict(NORMAL_FLOW)
    dw_dt_after_clear = r2["diagnostic_breakdown"]["temporal_metrics"]["dw_dt_kg_per_sec"]
    _check("4.2_clear_resets_state", abs(dw_dt_after_clear) < 1e-3,
           f"Post-clear first frame dW/dt = {dw_dt_after_clear} (expected 0.0)")

    # 4.3 dW/dt sign: increasing mass → positive; decreasing mass → negative
    print("\n[4.3] dW/dt sign reflects accumulation vs. depletion:")
    predictor.history_buffer.clear()
    predictor.predict({"distance_cm": 55.0, "weight_kg": 200.0,
                       "vibration_g": 3.0, "material_flow_rate_tph": 200.0})
    _sleep()
    r_inc = predictor.predict({"distance_cm": 40.0, "weight_kg": 800.0,
                                "vibration_g": 2.0, "material_flow_rate_tph": 100.0})
    dw_inc = r_inc["diagnostic_breakdown"]["temporal_metrics"]["dw_dt_kg_per_sec"]
    _check("4.3_positive_dw_dt", dw_inc > 0,
           f"Increasing mass → positive dW/dt = {dw_inc:.2f} kg/s")

    predictor.history_buffer.clear()
    predictor.predict({"distance_cm": 10.0, "weight_kg": 1200.0,
                       "vibration_g": 0.2, "material_flow_rate_tph": 0.0})
    _sleep()
    r_dec = predictor.predict({"distance_cm": 50.0, "weight_kg": 300.0,
                                "vibration_g": 3.2, "material_flow_rate_tph": 200.0})
    dw_dec = r_dec["diagnostic_breakdown"]["temporal_metrics"]["dw_dt_kg_per_sec"]
    _check("4.3_negative_dw_dt", dw_dec < 0,
           f"Decreasing mass → negative dW/dt = {dw_dec:.2f} kg/s")

    # 4.4 No false persistent alarm after recovery
    print("\n[4.4] No false persistent alarm after recovery:")
    predictor.history_buffer.clear()
    for _ in range(5):
        predictor.predict(_noisy(BLOCKAGE_CHOKE, 0.02))
        _sleep()
    # Now feed 5 normal frames
    last_normal = None
    for _ in range(5):
        last_normal = predictor.predict(_noisy(NORMAL_FLOW, 0.02))
        _sleep()
    _check("4.4_no_persistent_alarm", last_normal["status_code"] == 0,
           f"5 post-recovery normal frames → NORMAL (got {STATUS_LABELS[last_normal['status_code']]})")
    last_risk = last_normal["diagnostic_breakdown"]["chute_health_index"]["risk_score"]
    _check("4.4_risk_below_50", last_risk < 50.0,
           f"Post-recovery risk {last_risk:.1f} < 50.0 (non-alarming)")

    # 4.5 Buffer rolls at max capacity (maxlen=10)
    print("\n[4.5] Buffer rolls correctly at max capacity (10 frames):")
    predictor.history_buffer.clear()
    # Fill 12 frames — buffer should cap at 10
    for i in range(12):
        predictor.predict({"distance_cm": 55.0 - i * 0.5, "weight_kg": 300.0 + i * 5.0,
                           "vibration_g": 3.0, "material_flow_rate_tph": 240.0})
        if i > 0:
            _sleep()
    _check("4.5_buffer_maxlen", len(predictor.history_buffer) == 10,
           f"Buffer length after 12 frames = {len(predictor.history_buffer)} (expected 10)")

    # 4.6 Vib std tracks variance
    print("\n[4.6] Vibration std tracks actual variance:")
    predictor.history_buffer.clear()
    # Feed 5 constant-vib frames → std should be ~0
    for _ in range(5):
        predictor.predict({"distance_cm": 55.0, "weight_kg": 300.0,
                           "vibration_g": 3.0, "material_flow_rate_tph": 240.0})
        _sleep()
    r_const = predictor.predict({"distance_cm": 55.0, "weight_kg": 300.0,
                                  "vibration_g": 3.0, "material_flow_rate_tph": 240.0})
    vib_std_const = r_const["diagnostic_breakdown"]["temporal_metrics"]["vibration_variance"]
    _check("4.6_low_std_constant_vib", vib_std_const < 0.1,
           f"Constant vibration → std = {vib_std_const:.4f} (expected ~0)")

    # Feed alternating vib frames → std should be non-negligible
    predictor.history_buffer.clear()
    for i in range(6):
        vib = 1.0 if i % 2 == 0 else 9.0
        predictor.predict({"distance_cm": 55.0, "weight_kg": 300.0,
                           "vibration_g": vib, "material_flow_rate_tph": 240.0})
        _sleep()
    r_var = predictor.predict({"distance_cm": 55.0, "weight_kg": 300.0,
                                "vibration_g": 3.0, "material_flow_rate_tph": 240.0})
    vib_std_var = r_var["diagnostic_breakdown"]["temporal_metrics"]["vibration_variance"]
    _check("4.6_high_std_varying_vib", vib_std_var > 1.0,
           f"Alternating vibration → std = {vib_std_var:.4f} (expected > 1.0)")


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_phase3_suite():
    """Run the suite and return machine-readable counts for CI/reporting."""
    global PASS_COUNT, FAIL_COUNT

    PASS_COUNT = 0
    FAIL_COUNT = 0
    RESULTS.clear()

    print("=" * 75)
    print("🔬 FlowSentinel — PHASE 3 HARDENING & VALIDATION TEST SUITE")
    print("   Engineer 6 | Team 3 | ML Inference Pipeline & Validation Lead")
    print("=" * 75)

    task1_noisy_temporal_sequences()
    task2_transient_spike_validation()
    task3_diagnostic_robustness()
    task4_temporal_buffer_validation()

    total = PASS_COUNT + FAIL_COUNT
    print("\n" + "═" * 75)
    print(f"📊 PHASE 3 TEST SUITE RESULTS: {PASS_COUNT}/{total} PASS  |  {FAIL_COUNT} FAIL")
    print("═" * 75)

    if FAIL_COUNT > 0:
        print("\n❌ FAILED CHECKS:")
        for suite, outcomes in RESULTS.items():
            if "FAIL" in outcomes:
                print(f"  • {suite}")
    else:
        print("\n✅ ALL CHECKS PASSED — Phase 3 ML hardening complete.")

    return PASS_COUNT, total, FAIL_COUNT


def main():
    _, _, failures = run_phase3_suite()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
