from federation.clock import DeterministicClock
from typing import Dict, Any

class StrategicMetrics:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock
        self.plans_generated = 0
        self.actions_executed = 0
        self.last_global_risk = "LOW"
        
    def record_plan(self):
        self.plans_generated += 1
        
    def record_action(self):
        self.actions_executed += 1
        
    def set_global_risk(self, severity: str):
        self.last_global_risk = severity
        
    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "timestamp": self.clock.now(),
            "plans_generated": self.plans_generated,
            "actions_executed": self.actions_executed,
            "last_global_risk": self.last_global_risk
        }
