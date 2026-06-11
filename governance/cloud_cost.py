from federation.clock import DeterministicClock
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class CloudCostForecast:
    forecast_id: str
    projected_monthly_cost: float
    cost_per_tournament: float
    cost_per_submission: float
    timestamp: float

class CloudCostGovernance:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate_forecast(self, metrics: Dict[str, float]) -> CloudCostForecast:
        now = self.clock.now()
        # Deterministic cost heuristic
        base_cost = metrics.get("active_nodes", 0) * 50.0
        projected = base_cost * 1.05  # 5% overhead buffer
        
        cpt = projected / max(metrics.get("tournaments_run", 1), 1)
        cps = projected / max(metrics.get("submissions_processed", 1), 1)
        
        return CloudCostForecast(f"cost_{now}", projected, cpt, cps, now)
