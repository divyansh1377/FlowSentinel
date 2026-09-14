"""
FlowSentinel - Team 3 (ML & Simulation)
Exports synthetic datasets in CSV and JSON formats for offline inspection and data science experimentation.
"""

import os
from data_generator import ChutePhysicsGenerator

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def export_synthetic_datasets(n_samples: int = 20000):
    if n_samples < 20000:
        raise ValueError("Export at least 20,000 records to satisfy the project plan")
    generator = ChutePhysicsGenerator(seed=42)
    df = generator.generate_dataset(n_samples=n_samples)

    csv_path = os.path.join(DATA_DIR, "chute_telemetry_synthetic.csv")
    json_path = os.path.join(DATA_DIR, "chute_telemetry_synthetic.json")

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    print(f"✅ Exported {n_samples} records to:")
    print(f"   • CSV:  {csv_path}")
    print(f"   • JSON: {json_path}")


if __name__ == "__main__":
    export_synthetic_datasets()
