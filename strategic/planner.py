from federation.clock import DeterministicClock
from strategic.models import StrategicPlan, StrategicAction
from typing import List, Dict

class StrategicPlanner:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate_plan(self, timeframe: str, active_clusters: List[str], global_metrics: Dict[str, float]) -> StrategicPlan:
        now = self.clock.now()
        plan_id = f"plan_{timeframe}_{now}"
        
        actions = []
        evidence = [f"Metrics: {global_metrics}"]
        confidence = 0.95
        
        if timeframe == "+1h":
            # Short term workload balancing
            for cluster in active_clusters:
                actions.append(StrategicAction(f"act_{cluster}_{now}", "BALANCE_WORKLOAD", cluster, {"intensity": "low"}))
        elif timeframe == "+6h":
            # Medium term capacity prep
            for cluster in active_clusters:
                actions.append(StrategicAction(f"act_{cluster}_{now}", "SCALE_RESOURCES", cluster, {"target": "cpu", "buffer": 15}))
        elif timeframe == "+24h":
            # Daily optimization
            actions.append(StrategicAction(f"act_global_{now}", "OPTIMIZE_FEDERATION", "GLOBAL", {"mode": "cost"}))
            confidence = 0.85
        elif timeframe == "+7d":
            # Weekly forecast
            actions.append(StrategicAction(f"act_global_{now}", "EVALUATE_REGION_PROMOTION", "GLOBAL", {}))
            confidence = 0.70
            
        return StrategicPlan(plan_id, timeframe, actions, confidence, evidence, now)

    def generate_all_plans(self, active_clusters: List[str], global_metrics: Dict[str, float]) -> List[StrategicPlan]:
        return [
            self.generate_plan("+1h", active_clusters, global_metrics),
            self.generate_plan("+6h", active_clusters, global_metrics),
            self.generate_plan("+24h", active_clusters, global_metrics),
            self.generate_plan("+7d", active_clusters, global_metrics),
        ]
