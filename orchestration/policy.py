from typing import List, Dict, Any
from orchestration.models import OrchestrationPolicy, NodeOrchestrationMetrics

class PolicyEngine:
    """Evaluates rules and thresholds to detect policy violations across cluster metrics."""
    
    def __init__(self):
        self.policies: List[OrchestrationPolicy] = []
        # Register default policies
        self.policies.append(OrchestrationPolicy(
            policy_id="pol_cpu_limit",
            name="Critical CPU Limit",
            rule_expr="cpu > 85",
            action_type="REBALANCE"
        ))
        self.policies.append(OrchestrationPolicy(
            policy_id="pol_mem_limit",
            name="Critical Memory Limit",
            rule_expr="memory > 85",
            action_type="REBALANCE"
        ))
        self.policies.append(OrchestrationPolicy(
            policy_id="pol_lag_limit",
            name="Replication Lag Limit",
            rule_expr="replication_lag > 50",
            action_type="RECOVER_REPLICA"
        ))

    def add_policy(self, policy: OrchestrationPolicy) -> None:
        # Remove existing if matches policy_id
        self.policies = [p for p in self.policies if p.policy_id != policy.policy_id]
        self.policies.append(policy)

    def evaluate_node(self, metrics: NodeOrchestrationMetrics) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled policies against a node's metrics.
        Returns a list of violation dictionaries.
        """
        violations = []
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            expr = policy.rule_expr.lower()
            violated = False
            actual_value = 0.0
            
            if "cpu >" in expr:
                threshold = float(expr.split(">")[1].strip())
                actual_value = metrics.cpu_usage
                if actual_value > threshold:
                    violated = True
            elif "memory >" in expr:
                threshold = float(expr.split(">")[1].strip())
                actual_value = metrics.memory_usage
                if actual_value > threshold:
                    violated = True
            elif "replication_lag >" in expr:
                threshold = float(expr.split(">")[1].strip())
                actual_value = float(metrics.replication_lag)
                if actual_value > threshold:
                    violated = True
            
            if violated:
                violations.append({
                    "policy_id": policy.policy_id,
                    "policy_name": policy.name,
                    "node_id": metrics.node_id,
                    "rule_expr": policy.rule_expr,
                    "action_type": policy.action_type,
                    "actual_value": actual_value,
                    "timestamp": metrics.timestamp
                })
        return violations
