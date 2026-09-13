"""Live WebSocket handoff smoke test. Start the backend before running this."""

import asyncio
import json

import websockets

WS_URL = "ws://localhost:8000/ws/telemetry"
CRITICAL_BLOCKAGE = {
    "type": "SIMULATION_UPDATE",
    "payload": {
        "distance_cm": 5.0,
        "weight_kg": 1200.0,
        "vibration_g": 0.0,
        "material_flow_rate_tph": 0.0,
    },
}


async def main() -> None:
    async with websockets.connect(WS_URL) as websocket:
        handshake = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5))
        assert handshake["type"] == "HANDSHAKE", handshake

        await websocket.send(json.dumps(CRITICAL_BLOCKAGE))
        for _ in range(3):  # alert frames may arrive before the prediction
            response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5))
            if response["type"] == "TELEMETRY_PREDICTION":
                assert response["data"]["status_code"] == 2, response
                print("PASS: critical blockage classified as status_code=2")
                return
        raise AssertionError("No TELEMETRY_PREDICTION frame received")


if __name__ == "__main__":
    asyncio.run(main())
