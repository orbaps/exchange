from federation.clock import DeterministicClock
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ResourceCostProfile:
    cluster_id: str
    current_cost: float
    optimization_potential: float

@dataclass
class CostOptimizationPlan:
    plan_id: str
    target_savings: float
    actions: List[Dict[str, Any]]
    timestamp: float

class CostOptimizer:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def optimize_cluster_costs(self, profiles: List[ResourceCostProfile]) -> CostOptimizationPlan:
        now = self.clock.now()
        actions = []
        total_savings = 0.0
        
        # Sort deterministically
        sorted_profiles = sorted(profiles, key=lambda p: (-p.optimization_potential, p.cluster_id))
        
        for p in sorted_profiles:
            if p.optimization_potential > 100.0:
                actions.append({"action": "SCALE_DOWN", "cluster": p.cluster_id})
                total_savings += p.optimization_potential
                
        return CostOptimizationPlan(f"opt_cost_{now}", total_savings, actions, now)
