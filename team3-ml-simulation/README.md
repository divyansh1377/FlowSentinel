# 🧠 Team 3: Machine Learning & Physics Simulation

**Sub-Team**: Data Science & Hardware Modeling Engineers (Engineers 5 & 6)  
**Core Deliverables**:
1. Physics-based synthetic chute sensor telemetry generator (`data_generator.py`).
2. Training pipeline for **Isolation Forest** (anomalies) & **Random Forest** (0=Normal, 1=Warning, 2=Blockage) (`train_models.py`).
3. Thread-safe, ultra-low-latency model packaging and inference class `ChutePredictor` (`model_pipeline.py`).
4. Benchmark validation suite (`benchmark_ml.py`).

---

## 🔬 Sensor Physical Modeling Details
1. **Ultrasonic Sensor (Distance $d$ cm)**:
   - Empty Chute: $\sim 100\text{ cm}$
   - Normal Dynamic Stream: $40 - 75\text{ cm}$
   - Rising Bed / Warning: $18 - 38\text{ cm}$
   - Choke / Full: $4 - 15\text{ cm}$
2. **HX711 Load Cell (Weight $W$ kg)**:
   - Normal Dynamic Flow: $180 - 450\text{ kg}$
   - Buildup Warning: $500 - 800\text{ kg}$
   - Blockage Accumulation: $850 - 1400\text{ kg}$
3. **MPU6050 Accelerometer (Vibration $G$ RMS)**:
   - Normal Flow: $2.0 - 5.5\text{ G}$ (rock collisions against liner)
   - Buildup: $0.8 - 1.8\text{ G}$ (cushion dampening)
   - Stagnant Blockage: $0.05 - 0.45\text{ G}$ (dead kinetic energy)
   - Anomaly Spike: $> 9.0\text{ G}$ (structural resonance or loose plates)

---

## 🛠️ Usage Instructions

### 1. Train AI Models & Serialize Artifacts
```bash
python3 train_models.py
```
Outputs saved to `models/`:
- `chute_random_forest.joblib`
- `chute_isolation_forest.joblib`
- `scaler.joblib`
- `metadata.json`

### 2. Run Benchmarks
```bash
python3 benchmark_ml.py
```

### 3. How Team 2 (Backend) Uses the Model
```python
from model_pipeline import ChutePredictor

predictor = ChutePredictor()
telemetry = {
    "distance_cm": 45.0,
    "weight_kg": 320.0,
    "vibration_g": 3.1,
    "material_flow_rate_tph": 200.0
}
result = predictor.predict(telemetry)
print(result["status_label"]) # "NORMAL", "WARNING", or "BLOCKAGE"
```

