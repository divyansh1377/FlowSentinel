"""
FlowSentinel - Team 2 (Backend & Architecture)
Background Live Simulator Daemon

When Auto-Simulation mode is active, this service continuously generates
physics-based sensor data and pushes real-time inferences through WebSockets.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone

# Allow importing from team3-ml-simulation
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team3-ml-simulation"))

from data_generator import ChutePhysicsGenerator
from websocket_manager import ws_hub

logger = logging.getLogger("FlowSentinel.SimulatorService")

class LiveSimulatorService:
    def __init__(self):
        self.is_running = False
        self.mode = "manual"  # "manual" or "auto"
        self.preset = "NORMAL_FLOW"
        self.interval_seconds = 0.5
        self.physics_generator = ChutePhysicsGenerator()
        self.predictor = None
        self.alert_dispatcher = None
        self.task = None

    def initialize(self, predictor, alert_dispatcher):
        self.predictor = predictor
        self.alert_dispatcher = alert_dispatcher

    def set_mode(self, mode: str, preset: str = "NORMAL_FLOW", interval_ms: int = 500):
        self.mode = mode
        self.preset = preset
        self.interval_seconds = max(0.1, interval_ms / 1000.0)
        logger.info(f"🔄 [SimulatorService] Mode set to: {self.mode} (Preset: {self.preset}, Interval: {self.interval_seconds}s)")

    async def start_loop(self):
        self.is_running = True
        logger.info("▶️ [SimulatorService] Background simulation loop started.")
        while self.is_running:
            try:
                if self.mode == "auto" and ws_hub.active_connections and self.predictor:
                    state_id = 0
                    if self.preset == "NORMAL_FLOW":
                        state_id = 0
                    elif self.preset == "RISING_BUILDUP":
                        state_id = 1
                    elif self.preset == "COMPLETE_BLOCKAGE":
                        state_id = 2
                    elif self.preset == "ERRATIC_SENSOR_SPIKE":
                        state_id = 3

                    raw_sample = self.physics_generator.generate_sample(state=state_id, inject_noise=True)
                    
                    # Run inference
                    prediction = self.predictor.predict(raw_sample)
                    prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
                    prediction["chute_id"] = "CHUTE_BLAST_FURNACE_01"

                    # Evaluate alert
                    if self.alert_dispatcher:
                        await self.alert_dispatcher.evaluate_prediction(prediction, "CHUTE_BLAST_FURNACE_01")

                    # Broadcast to UI
                    await ws_hub.broadcast_json("TELEMETRY_PREDICTION", prediction)

                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"⚠️ [SimulatorService] Error in loop: {e}")
                await asyncio.sleep(1.0)

    def stop(self):
        self.is_running = False

simulator_service = LiveSimulatorService()
