from typing import List, Dict, Any, Optional
from governance.models import CapacityForecast, FailureForecast, PartitionForecast
from federation.clock import DeterministicClock

class PredictionEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def forecast_capacity(self, node_id: str, metric: str, history: List[float]) -> CapacityForecast:
        now = self.clock.now()
        if not history or len(history) < 2:
            return CapacityForecast(node_id, metric, 0.0, 0.0, None, now)
        
        # Simple linear projection
        slope = (history[-1] - history[0]) / max(1, len(history) - 1)
        current = history[-1]
        
        proj_1h = current + (slope * 60) # assuming history items are 1 minute apart
        proj_24h = current + (slope * 60 * 24)
        
        bottleneck = None
        if slope > 0:
            remaining = 100.0 - current
            if remaining > 0:
                bottleneck = (remaining / slope) * 60
                
        return CapacityForecast(node_id, metric, proj_1h, proj_24h, bottleneck, now)

    def forecast_failure(self, node_id: str, history: List[Dict[str, Any]]) -> FailureForecast:
        now = self.clock.now()
        if not history:
            return FailureForecast(node_id, 0.0, None, now)
            
        anomalies = sum(1 for h in history if h.get("status") != "HEALTHY")
        prob = min(1.0, anomalies / len(history) * 1.5)
        
        time_to_failure = None
        if prob > 0.8:
            time_to_failure = 3600.0 # 1 hour
            
        return FailureForecast(node_id, prob, time_to_failure, now)

    def forecast_partition(self, history: List[Dict[str, Any]]) -> PartitionForecast:
        now = self.clock.now()
        prob = 0.0
        affected = []
        if history:
            missed_heartbeats = sum(1 for h in history if h.get("missed_heartbeats", 0) > 3)
            if missed_heartbeats > len(history) * 0.1:
                prob = 0.75
                affected = [h.get("node_id", "") for h in history if h.get("missed_heartbeats", 0) > 3]
                
        return PartitionForecast(affected, prob, now)
