"""
FlowSentinel - Team 2 (Backend & Architecture)
Stateful Alert Dispatcher with Hysteresis & Debouncing

Prevents rapid alarm flickering by requiring consecutive threshold breaches
and maintains an in-memory alert history audit log.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from schemas import AlertEvent
from websocket_manager import ws_hub

class AlertDispatcher:
    def __init__(self, debounce_window_sec: float = 1.5):
        self.debounce_window_sec = debounce_window_sec
        self.current_state: int = 0  # 0=Normal, 1=Warning, 2=Blockage
        self.last_state_change_time: float = 0.0
        self.last_alert_time: float = 0.0
        self.alert_history: List[AlertEvent] = []
        self.max_history_len = 100

    async def evaluate_prediction(self, prediction: Dict[str, Any], chute_id: str = "CHUTE_01") -> Optional[AlertEvent]:
        now = time.time()
        status_code = prediction.get("status_code", 0)
        is_anomaly = prediction.get("anomaly_detection", {}).get("is_anomaly", False)
        diagnosis = prediction.get("root_cause_analysis", "")
        recommendation = prediction.get("recommended_action", "")

        triggered_alert = None

        # Check for state transition or anomaly trigger
        if status_code != self.current_state or is_anomaly:
            time_since_change = now - self.last_state_change_time

            # Check if condition persisted or is an immediate critical blockage/anomaly
            if time_since_change >= self.debounce_window_sec or status_code == 2 or is_anomaly:
                self.current_state = status_code
                self.last_state_change_time = now

                if status_code == 2:  # CRITICAL BLOCKAGE
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-BLK-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=datetime.utcnow().isoformat(),
                        severity="CRITICAL",
                        title="🚨 CRITICAL CHUTE BLOCKAGE DETECTED",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code
                    )
                elif status_code == 1:  # WARNING
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-WRN-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=datetime.utcnow().isoformat(),
                        severity="WARNING",
                        title="⚠️ FLOW RESTRICTION / BUILDUP WARNING",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code
                    )
                elif is_anomaly:  # ANOMALY
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-ANM-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=datetime.utcnow().isoformat(),
                        severity="WARNING",
                        title="⚡ SENSOR / VIBRATION ANOMALY DETECTED",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code
                    )

                if triggered_alert:
                    self.alert_history.insert(0, triggered_alert)
                    if len(self.alert_history) > self.max_history_len:
                        self.alert_history.pop()

                    # Broadcast alert immediately via WebSocket
                    await ws_hub.broadcast_json("CRITICAL_ALERT", triggered_alert.model_dump())
                    print(f"📢 [AlertDispatcher] Triggered: {triggered_alert.title}")

        return triggered_alert

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [alert.model_dump() for alert in self.alert_history[:limit]]

alert_dispatcher = AlertDispatcher()

