"""
FlowSentinel - Team 3 (ML & Simulation)
Physics-Based Synthetic Sensor Telemetry Generator for Steel Plant Chutes.

Simulates 3 logical sensors with realistic industrial noise, physical coupling, and state transitions:
1. Ultrasonic Distance Sensor (cm) - Air gap between sensor and material bed.
2. HX711 Load Cell Sensor (kg) - Instantaneous mass of ore resting in/passing through chute.
3. MPU6050 3-Axis Accelerometer (G RMS) - Kinetic impact oscillations and turbulence.
"""

import numpy as np
import pandas as pd
import random
from typing import Dict, List, Tuple, Any

# Sensor Physical Operating Limits
CHUTE_EMPTY_DISTANCE_CM = 100.0  # Max sensor clearance when empty
CHUTE_FULL_DISTANCE_CM = 5.0     # Minimum clearance when completely choked
MAX_LOAD_CAPACITY_KG = 1500.0    # Structural limit for weight accumulation

class ChutePhysicsGenerator:
    """
    Generates physically consistent telemetry simulating steel manufacturing transfer chutes.
    States:
        0: Normal continuous flow (Dynamic equilibrium, moderate weight, high vibration, good clearance)
        1: Warning / Flow restriction (Material sluggishness, rising weight, dampening vibration, decreasing clearance)
        2: Blockage / Choke (Dead-stop plug, excessive weight, near-zero vibration, minimal clearance)
        3: Anomaly / Sensor fault (Erratic readings, out-of-distribution noise, electrical disconnects)
    """

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)

    def generate_sample(self, state: int = 0, inject_noise: bool = True) -> Dict[str, Any]:
        """
        Generate a single instantaneous sensor sample for a given physical state.
        """
        noise_factor = 1.0 if inject_noise else 0.0

        if state == 0:  # NORMAL FLOW
            # Clearance: 40 - 75 cm
            dist_mean, dist_std = 55.0, 6.0
            # Weight: 180 - 450 kg (continuous movement)
            weight_mean, weight_std = 320.0, 45.0
            # Vibration: 2.0 - 5.5 G RMS (healthy dynamic rock collisions)
            vib_mean, vib_std = 3.2, 0.55
            # Flow rate: 150 - 350 tons/hour
            flow_mean, flow_std = 240.0, 30.0

        elif state == 1:  # WARNING / RISING BUILDUP
            # Clearance decreasing: 18 - 38 cm
            dist_mean, dist_std = 27.0, 4.5
            # Weight increasing: 500 - 800 kg
            weight_mean, weight_std = 660.0, 60.0
            # Vibration dampening as ore bed thickens: 0.8 - 1.8 G RMS
            vib_mean, vib_std = 1.25, 0.25
            # Flow rate dropping: 60 - 150 tons/hour
            flow_mean, flow_std = 110.0, 20.0

        elif state == 2:  # CRITICAL BLOCKAGE
            # Clearance near zero: 4 - 15 cm
            dist_mean, dist_std = 8.0, 2.5
            # Heavy piled material: 850 - 1400 kg
            weight_mean, weight_std = 1080.0, 110.0
            # Dead vibration due to complete choke: 0.05 - 0.45 G RMS
            vib_mean, vib_std = 0.22, 0.08
            # Flow rate zeroed: 0 - 20 tons/hour
            flow_mean, flow_std = 5.0, 3.0

        elif state == 3:  # ANOMALY / SENSOR FAULT
            anomaly_type = random.choice(["sensor_disconnect", "resonance_surge", "inverted_physics"])
            if anomaly_type == "sensor_disconnect":
                dist_mean, dist_std = 0.0, 0.5
                weight_mean, weight_std = 0.0, 1.0
                vib_mean, vib_std = 0.0, 0.01
                flow_mean, flow_std = 0.0, 0.0
            elif anomaly_type == "resonance_surge":
                dist_mean, dist_std = 55.0, 5.0
                weight_mean, weight_std = 300.0, 40.0
                vib_mean, vib_std = 12.5, 2.0  # Massive mechanical chatter
                flow_mean, flow_std = 220.0, 25.0
            else:  # Inverted physics: low weight with zero distance
                dist_mean, dist_std = 5.0, 1.0
                weight_mean, weight_std = 25.0, 5.0
                vib_mean, vib_std = 4.0, 0.5
                flow_mean, flow_std = 200.0, 20.0
        else:
            raise ValueError(f"Unknown state: {state}")

        # Sample values with Gaussian noise
        distance_cm = np.clip(np.random.normal(dist_mean, dist_std * noise_factor), 1.0, CHUTE_EMPTY_DISTANCE_CM)
        weight_kg = np.clip(np.random.normal(weight_mean, weight_std * noise_factor), 0.0, MAX_LOAD_CAPACITY_KG)
        vibration_g = np.clip(np.random.normal(vib_mean, vib_std * noise_factor), 0.01, 15.0)
        flow_rate_tph = np.clip(np.random.normal(flow_mean, flow_std * noise_factor), 0.0, 500.0)

        # Decompose vibration into tri-axial components with noise
        ratio_x = random.uniform(0.3, 0.5)
        ratio_y = random.uniform(0.3, 0.5)
        ratio_z = np.sqrt(max(0.01, 1.0 - ratio_x**2 - ratio_y**2))
        vib_x = round(float(vibration_g * ratio_x + np.random.normal(0, 0.05)), 3)
        vib_y = round(float(vibration_g * ratio_y + np.random.normal(0, 0.05)), 3)
        vib_z = round(float(vibration_g * ratio_z + np.random.normal(0, 0.05)), 3)

        return {
            "distance_cm": round(float(distance_cm), 2),
            "weight_kg": round(float(weight_kg), 2),
            "vibration_g": round(float(vibration_g), 3),
            "vibration_x": vib_x,
            "vibration_y": vib_y,
            "vibration_z": vib_z,
            "material_flow_rate_tph": round(float(flow_rate_tph), 2),
            "state_label": state if state < 3 else 0,  # 0, 1, or 2 for classifier
            "is_anomaly": 1 if state == 3 else 0
        }

    def generate_continuous_trajectory(self, n_steps: int = 5000, transition_prob: float = 0.02) -> pd.DataFrame:
        """
        Generate continuous-time Markov random walk trajectory simulating real chute operational physics.
        Models smooth physical transitions across operational states:
        State 0 (Normal) <--> State 1 (Buildup) <--> State 2 (Blockage)
        plus occasional out-of-distribution State 3 anomalies.
        """
        records = []
        current_state = 0
        
        # Continuous state state-transition probability matrix
        # States: 0=Normal, 1=Warning, 2=Blockage, 3=Anomaly
        transition_matrix = {
            0: [0.980, 0.017, 0.001, 0.002],
            1: [0.030, 0.940, 0.028, 0.002],
            2: [0.005, 0.045, 0.948, 0.002],
            3: [0.150, 0.050, 0.000, 0.800]
        }

        for _ in range(n_steps):
            records.append(self.generate_sample(state=current_state, inject_noise=True))
            probs = transition_matrix[current_state]
            current_state = int(np.random.choice([0, 1, 2, 3], p=probs))

        return pd.DataFrame(records)

    def generate_dataset(self, n_samples: int = 20000, use_markov: bool = True) -> pd.DataFrame:
        """
        Generate training dataset. When use_markov=True, incorporates continuous
        Markov chain physics trajectories to capture dynamic transition states without boundary leakage.
        """
        if use_markov:
            # 70% continuous Markov walk, 30% stratified edge cases for comprehensive coverage
            n_markov = int(n_samples * 0.70)
            n_stratified = n_samples - n_markov

            df_markov = self.generate_continuous_trajectory(n_steps=n_markov)

            n_normal = int(n_stratified * 0.50)
            n_warning = int(n_stratified * 0.25)
            n_blockage = int(n_stratified * 0.15)
            n_anomalies = n_stratified - (n_normal + n_warning + n_blockage)

            strat_records = []
            for _ in range(n_normal):
                strat_records.append(self.generate_sample(state=0))
            for _ in range(n_warning):
                strat_records.append(self.generate_sample(state=1))
            for _ in range(n_blockage):
                strat_records.append(self.generate_sample(state=2))
            for _ in range(n_anomalies):
                strat_records.append(self.generate_sample(state=3))

            df_strat = pd.DataFrame(strat_records)
            df = pd.concat([df_markov, df_strat], ignore_index=True)
        else:
            records = []
            n_normal = int(n_samples * 0.60)
            n_warning = int(n_samples * 0.22)
            n_blockage = int(n_samples * 0.13)
            n_anomalies = n_samples - (n_normal + n_warning + n_blockage)

            for _ in range(n_normal):
                records.append(self.generate_sample(state=0))
            for _ in range(n_warning):
                records.append(self.generate_sample(state=1))
            for _ in range(n_blockage):
                records.append(self.generate_sample(state=2))
            for _ in range(n_anomalies):
                records.append(self.generate_sample(state=3))

            df = pd.DataFrame(records)

        # Shuffle dataset
        df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        return df

if __name__ == "__main__":
    generator = ChutePhysicsGenerator()
    df = generator.generate_dataset(n_samples=1000, use_markov=True)
    print("Dataset Generated with Markov Chain Transitions:")
    print(df.head(10))
    print("\nClass distribution:\n", df['state_label'].value_counts())
    print("\nAnomaly distribution:\n", df['is_anomaly'].value_counts())

