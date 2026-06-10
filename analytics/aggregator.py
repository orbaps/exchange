import time
from typing import Dict, Any
from execution.events import ExecutionEvent
from analytics.events import AnalyticsEvent, AnalyticsEventType
from analytics.bus import AnalyticsEventBus

class AnalyticsAggregator:
    """Subscribes to internal sub-systems and broadcasts normalized AnalyticsEvents."""
    
    def __init__(self, bus: AnalyticsEventBus):
        self.bus = bus
        self._execution_counter = 0
        
    def consume_execution(self, event: ExecutionEvent):
        payload = {
            "execution_sequence_id": event.execution_sequence_id,
            "session_id": event.session_id,
            "success": event.success,
            "latency_ns": event.completion_timestamp_ns - event.dispatch_timestamp_ns if event.completion_timestamp_ns > 0 else 0,
            "error": event.error
        }
        
        analytics_event = AnalyticsEvent(
            event_id=f"exec_{self._execution_counter}",
            timestamp_ns=time.time_ns(),
            event_type=AnalyticsEventType.EXECUTION_UPDATE,
            source="ExecutionWorker",
            payload=payload
        )
        self._execution_counter += 1
        self.bus.publish(analytics_event)
        
    def consume_telemetry(self, telemetry_data: Dict[str, Any]):
        analytics_event = AnalyticsEvent(
            event_id=f"tel_{time.time_ns()}",
            timestamp_ns=time.time_ns(),
            event_type=AnalyticsEventType.TELEMETRY_UPDATE,
            source="TelemetryService",
            payload=telemetry_data
        )
        self.bus.publish(analytics_event)
        
    def consume_score(self, score_data: Dict[str, Any]):
        analytics_event = AnalyticsEvent(
            event_id=f"score_{time.time_ns()}",
            timestamp_ns=time.time_ns(),
            event_type=AnalyticsEventType.SCORE_UPDATE,
            source="ScoringEngine",
            payload=score_data
        )
        self.bus.publish(analytics_event)
