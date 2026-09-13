"""
FlowSentinel - Team 2 (Backend & Architecture)
Stateful Alert Dispatcher with Hysteresis & Debouncing

Prevents rapid alarm flickering by requiring consecutive threshold breaches
and maintains an in-memory alert history audit log.
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from schemas import AlertEvent
from websocket_manager import ws_hub

logger = logging.getLogger("FlowSentinel.AlertDispatcher")

def get_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class AlertDispatcher:
    def __init__(self, debounce_window_sec: float = 3.0):
        self.debounce_window_sec = debounce_window_sec
        self.current_state: int = 0  # 0=Normal, 1=Warning, 2=Blockage
        self.last_state_change_time: float = 0.0
        self.last_alert_time: float = 0.0
        self.alert_history: List[AlertEvent] = []
        self.max_history_len: int = 200

    async def evaluate_prediction(self, prediction: Dict[str, Any], chute_id: str = "CHUTE_BLAST_FURNACE_01") -> Optional[AlertEvent]:
        now = time.time()
        status_code = prediction.get("status_code", 0)
        anomaly_dict = prediction.get("anomaly_detection", {})
        is_anomaly = anomaly_dict.get("is_anomaly", False) if isinstance(anomaly_dict, dict) else False
        diagnosis = prediction.get("root_cause_analysis", "Unknown anomaly condition")
        recommendation = prediction.get("recommended_action", "Inspect chute immediately.")

        triggered_alert = None

        # Check for state transition or anomaly trigger
        if status_code != self.current_state or is_anomaly:
            time_since_change = now - self.last_state_change_time

            # Immediate trigger on Critical Blockage (state 2) or Anomaly, or after debounce window for Warning
            is_immediate = (status_code == 2) or is_anomaly
            if is_immediate or time_since_change >= self.debounce_window_sec:
                prev_state = self.current_state
                self.current_state = status_code
                self.last_state_change_time = now

                if status_code == 2:  # CRITICAL BLOCKAGE
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-BLK-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=get_utc_iso(),
                        severity="CRITICAL",
                        title="🚨 CRITICAL CHUTE BLOCKAGE DETECTED",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code,
                        acknowledged=False
                    )
                elif status_code == 1:  # WARNING
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-WRN-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=get_utc_iso(),
                        severity="WARNING",
                        title="⚠️ FLOW RESTRICTION / BUILDUP WARNING",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code,
                        acknowledged=False
                    )
                elif is_anomaly and status_code == 0:  # ANOMALY IN NORMAL STATE
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-ANM-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=get_utc_iso(),
                        severity="WARNING",
                        title="⚡ SENSOR / VIBRATION ANOMALY DETECTED",
                        message=f"{diagnosis} Action: {recommendation}",
                        chute_id=chute_id,
                        status_code=status_code,
                        acknowledged=False
                    )
                elif status_code == 0 and prev_state in (1, 2):  # RECOVERY BACK TO NORMAL
                    triggered_alert = AlertEvent(
                        alert_id=f"ALT-REC-{uuid.uuid4().hex[:6].upper()}",
                        timestamp=get_utc_iso(),
                        severity="INFO",
                        title="✅ CHUTE FLOW RESTORED TO NORMAL",
                        message=f"Flow stabilized. Previous status: {prev_state}.",
                        chute_id=chute_id,
                        status_code=status_code,
                        acknowledged=True
                    )

                if triggered_alert:
                    self.alert_history.insert(0, triggered_alert)
                    if len(self.alert_history) > self.max_history_len:
                        self.alert_history.pop()

                    # Broadcast alert immediately via WebSocket
                    await ws_hub.broadcast_json("CRITICAL_ALERT", triggered_alert.model_dump())
                    logger.warning(f"📢 [AlertDispatcher] Triggered: {triggered_alert.title} ({triggered_alert.alert_id})")

        return triggered_alert

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [alert.model_dump() for alert in self.alert_history[:limit]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def clear_history(self):
        self.alert_history.clear()
        self.current_state = 0
        self.last_state_change_time = 0.0

alert_dispatcher = AlertDispatcher()
