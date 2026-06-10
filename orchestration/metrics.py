from typing import Dict, Any

class OrchestrationMetricsTracker:
    """Tracks performance and volume statistics for the cluster orchestration layer."""

    def __init__(self):
        self.active_anomalies_count: int = 0
        self.policy_violations_count: int = 0
        self.rebalance_executions_count: int = 0
        self.completed_healing_actions: int = 0
        self.failed_healing_actions: int = 0

    def record_rebalance(self) -> None:
        self.rebalance_executions_count += 1

    def record_policy_violation(self) -> None:
        self.policy_violations_count += 1

    def record_healing_success(self) -> None:
        self.completed_healing_actions += 1

    def record_healing_failure(self) -> None:
        self.failed_healing_actions += 1

    def get_self_healing_success_rate(self) -> float:
        total = self.completed_healing_actions + self.failed_healing_actions
        if total == 0:
            return 1.0
        return self.completed_healing_actions / total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_anomalies_count": self.active_anomalies_count,
            "policy_violations_count": self.policy_violations_count,
            "rebalance_executions_count": self.rebalance_executions_count,
            "completed_healing_actions": self.completed_healing_actions,
            "failed_healing_actions": self.failed_healing_actions,
            "self_healing_success_rate": round(self.get_self_healing_success_rate(), 4)
        }
