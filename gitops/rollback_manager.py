from federation.clock import DeterministicClock
from typing import Dict, Any, List

class RollbackManager:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock
        self.history: List[Dict[str, Any]] = []

    def record_deployment(self, deployment_id: str, state: Dict[str, Any]):
        self.history.append({
            "id": deployment_id,
            "state": state,
            "timestamp": self.clock.now()
        })

    def generate_rollback(self, steps_back: int = 1) -> Dict[str, Any]:
        if len(self.history) <= steps_back:
            return {}
        target_idx = len(self.history) - 1 - steps_back
        return self.history[target_idx]["state"]
