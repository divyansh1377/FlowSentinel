"""Physics-based synthetic telemetry for the FlowSentinel transfer chute."""

import random
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

GRAVITY_MPS2 = 9.81
CHUTE_ANGLE_DEG = 55.0
CHUTE_LENGTH_M = 3.0
SENSING_BED_AREA_M2 = 0.45
CHUTE_HEIGHT_CM = 100.0
MATERIAL_DENSITY_KG_M3 = 1600.0
MAX_LOAD_CAPACITY_KG = 1500.0

ULTRASONIC_RESOLUTION_CM = 0.1
HX711_RESOLUTION_KG = 0.5
MPU6050_RESOLUTION_G = 0.01
FLOW_RESOLUTION_TPH = 0.1


def _quantize(value: float, resolution: float) -> float:
    return round(round(value / resolution) * resolution, 6)


class ChutePhysicsGenerator:
    """Generate coupled chute telemetry and hardware-fault profiles.

    Operating states specify fill, compaction and friction regimes. Bed height
    determines clearance/mass; gravity and Coulomb friction determine velocity;
    velocity determines throughput and impact vibration.
    """

    _STATE_PARAMETERS = {
        # fill ratio, fill std, friction angle, friction std, velocity damping
        0: (0.45, 0.060, 25.0, 2.0, 0.45),
        1: (0.73, 0.045, 32.0, 2.0, 0.20),
        2: (0.92, 0.025, 38.0, 1.5, 0.008),
    }

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.random = random.Random(seed)
        self._hx711_drift_kg = 0.0
        self._mpu6050_bias_g = 0.0

    def _operating_dynamics(self, state: int) -> Dict[str, float]:
        fill_mean, fill_std, friction_mean, friction_std, damping = (
            self._STATE_PARAMETERS[state]
        )
        fill_ratio = float(np.clip(self.rng.normal(fill_mean, fill_std), 0.02, 0.98))
        friction_deg = float(
            np.clip(self.rng.normal(friction_mean, friction_std), 15.0, 45.0)
        )
        compaction = {0: 0.95, 1: 1.25, 2: 1.65}[state]
        compaction *= float(np.clip(self.rng.normal(1.0, 0.04), 0.85, 1.15))

        bed_height_cm = fill_ratio * CHUTE_HEIGHT_CM
        bed_volume_m3 = (bed_height_cm / 100.0) * SENSING_BED_AREA_M2
        true_weight_kg = min(
            bed_volume_m3 * MATERIAL_DENSITY_KG_M3 * compaction, MAX_LOAD_CAPACITY_KG
        )

        theta = np.deg2rad(CHUTE_ANGLE_DEG)
        friction = np.deg2rad(friction_deg)
        # a = g(sin(theta) - tan(phi) cos(theta)); phi is the friction angle.
        acceleration = max(
            0.05,
            float(GRAVITY_MPS2 * (np.sin(theta) - np.tan(friction) * np.cos(theta))),
        )
        velocity = np.sqrt(2.0 * acceleration * CHUTE_LENGTH_M) * damping
        flow_tph = max(0.0, 240.0 * (velocity / 2.5) * self.rng.normal(1.0, 0.05))

        return {
            "bed_height_cm": bed_height_cm,
            "true_distance_cm": CHUTE_HEIGHT_CM - bed_height_cm,
            "true_weight_kg": true_weight_kg,
            "true_vibration_g": 0.12 + 1.20 * velocity,
            "flow_tph": min(flow_tph, 500.0),
            "friction_angle_deg": friction_deg,
            "effective_accel_mps2": acceleration,
            "ore_velocity_mps": velocity,
        }

    def generate_sample(
        self,
        state: int = 0,
        inject_noise: bool = True,
        fault_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate one quantized reading; state 3 selects a hardware fault."""
        if state not in (0, 1, 2, 3):
            raise ValueError(f"Unknown state: {state}")

        is_fault = state == 3
        dynamics = self._operating_dynamics(0 if is_fault else state)
        noise_scale = 1.0 if inject_noise else 0.0

        # Slow sensor bias random walks plus per-sample electrical/jitter noise.
        self._hx711_drift_kg = float(
            np.clip(
                self._hx711_drift_kg + self.rng.normal(0.0, 0.15 * noise_scale),
                -8.0,
                8.0,
            )
        )
        self._mpu6050_bias_g = float(
            np.clip(
                self._mpu6050_bias_g + self.rng.normal(0.0, 0.002 * noise_scale),
                -0.08,
                0.08,
            )
        )
        hx_noise = self.rng.normal(0.0, 2.0 * noise_scale)
        mpu_jitter = self.rng.normal(0.0, 0.03 * noise_scale)
        distance_cm = dynamics["true_distance_cm"] + self.rng.normal(
            0.0, 0.35 * noise_scale
        )
        weight_kg = dynamics["true_weight_kg"] + self._hx711_drift_kg + hx_noise
        vibration_g = dynamics["true_vibration_g"] + self._mpu6050_bias_g + mpu_jitter
        flow_tph = dynamics["flow_tph"] + self.rng.normal(0.0, 2.0 * noise_scale)

        selected_fault = None
        dropout = False
        if is_fault:
            selected_fault = fault_type or self.random.choice(
                [
                    "signal_dropout",
                    "resonance_surge",
                    "inverted_physics",
                    "load_cell_drift",
                ]
            )
            if selected_fault == "signal_dropout":
                dropout = True
                distance_cm, weight_kg, vibration_g, flow_tph = 0.0, 0.0, 0.0, 0.0
            elif selected_fault == "resonance_surge":
                vibration_g = 12.5 + self.rng.normal(0.0, 1.5 * noise_scale)
            elif selected_fault == "inverted_physics":
                distance_cm = 5.0 + self.rng.normal(0.0, 0.8 * noise_scale)
                weight_kg = 25.0 + self.rng.normal(0.0, 4.0 * noise_scale)
                vibration_g = 4.0 + self.rng.normal(0.0, 0.4 * noise_scale)
                flow_tph = 200.0 + self.rng.normal(0.0, 15.0 * noise_scale)
            elif selected_fault == "load_cell_drift":
                weight_kg = 1350.0 + self.rng.normal(0.0, 25.0 * noise_scale)
                vibration_g = 6.2 + self.rng.normal(0.0, 0.25 * noise_scale)
            else:
                raise ValueError(f"Unknown fault_type: {selected_fault}")

        distance_cm = _quantize(
            float(np.clip(distance_cm, 0.0, CHUTE_HEIGHT_CM)), ULTRASONIC_RESOLUTION_CM
        )
        weight_kg = _quantize(
            float(np.clip(weight_kg, 0.0, MAX_LOAD_CAPACITY_KG)), HX711_RESOLUTION_KG
        )
        vibration_g = _quantize(
            float(np.clip(vibration_g, 0.0, 15.0)), MPU6050_RESOLUTION_G
        )
        flow_tph = _quantize(float(np.clip(flow_tph, 0.0, 500.0)), FLOW_RESOLUTION_TPH)

        ratio_x, ratio_y = self.random.uniform(0.30, 0.50), self.random.uniform(
            0.30, 0.50
        )
        ratio_z = np.sqrt(max(0.01, 1.0 - ratio_x**2 - ratio_y**2))
        vibration_x = _quantize(
            vibration_g * ratio_x + self.rng.normal(0, 0.02 * noise_scale),
            MPU6050_RESOLUTION_G,
        )
        vibration_y = _quantize(
            vibration_g * ratio_y + self.rng.normal(0, 0.02 * noise_scale),
            MPU6050_RESOLUTION_G,
        )
        vibration_z = _quantize(
            vibration_g * ratio_z + self.rng.normal(0, 0.02 * noise_scale),
            MPU6050_RESOLUTION_G,
        )

        return {
            "distance_cm": distance_cm,
            "weight_kg": weight_kg,
            "vibration_g": vibration_g,
            "vibration_x": vibration_x,
            "vibration_y": vibration_y,
            "vibration_z": vibration_z,
            "material_flow_rate_tph": flow_tph,
            "state_label": state if state < 3 else 0,
            "is_anomaly": int(is_fault),
            "fault_type": selected_fault or "none",
            "signal_dropout": dropout,
            "bed_height_cm": round(dynamics["bed_height_cm"], 3),
            "true_distance_cm": round(dynamics["true_distance_cm"], 3),
            "true_weight_kg": round(dynamics["true_weight_kg"], 3),
            "gravity_accel_mps2": GRAVITY_MPS2,
            "friction_angle_deg": round(dynamics["friction_angle_deg"], 3),
            "effective_accel_mps2": round(dynamics["effective_accel_mps2"], 5),
            "ore_velocity_mps": round(dynamics["ore_velocity_mps"], 5),
            "hx711_electrical_noise_kg": round(float(hx_noise), 4),
            "hx711_drift_kg": round(self._hx711_drift_kg, 4),
            "mpu6050_bias_g": round(self._mpu6050_bias_g, 5),
            "mpu6050_jitter_g": round(float(mpu_jitter), 5),
        }

    def generate_dataset(self, n_samples: int = 20000) -> pd.DataFrame:
        """Generate records across all operational states (20,000 by default)."""
        if n_samples <= 0:
            raise ValueError("n_samples must be positive")
        counts = {
            0: int(n_samples * 0.60),
            1: int(n_samples * 0.22),
            2: int(n_samples * 0.13),
        }
        counts[3] = n_samples - sum(counts.values())
        records = [
            self.generate_sample(state)
            for state, count in counts.items()
            for _ in range(count)
        ]
        return (
            pd.DataFrame(records)
            .sample(frac=1.0, random_state=42)
            .reset_index(drop=True)
        )


if __name__ == "__main__":
    print(ChutePhysicsGenerator().generate_dataset().head())
