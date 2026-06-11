from federation.clock import DeterministicClock
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class FailoverPlan:
    plan_id: str
    source_provider: str
    target_provider: str
    actions: List[Dict[str, Any]]
    estimated_time_s: float
    timestamp: float

class MultiCloudFailoverManager:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def simulate_evacuation(self, provider: str, available_providers: List[str]) -> FailoverPlan:
        now = self.clock.now()
        actions = []
        
        # Deterministically select target provider
        sorted_providers = sorted([p for p in available_providers if p != provider])
        target_provider = sorted_providers[0] if sorted_providers else "UNKNOWN"
        
        actions.append({"action": "PROVISION_CLUSTER", "provider": target_provider})
        actions.append({"action": "SYNC_STATE", "source": provider, "target": target_provider})
        actions.append({"action": "SWAP_TRAFFIC", "target": target_provider})
        
        return FailoverPlan(f"evac_{provider}_{now}", provider, target_provider, actions, 1800.0, now)
