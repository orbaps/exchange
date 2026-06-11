from typing import Dict, Any, List
from governance.models import VersionedPolicy, PolicyType

class PolicyEngine:
    def __init__(self):
        self.policies: Dict[str, VersionedPolicy] = {}

    def register_policy(self, policy: VersionedPolicy):
        self.policies[policy.policy_id] = policy

    def evaluate_threshold(self, policy: VersionedPolicy, current_metrics: Dict[str, float]) -> bool:
        if not policy.enabled or policy.policy_type != PolicyType.THRESHOLD:
            return False
            
        metric_name = policy.rules.get("metric")
        threshold = policy.rules.get("value", 100.0)
        operator = policy.rules.get("operator", ">")
        
        current = current_metrics.get(metric_name)
        if current is None:
            return False
            
        if operator == ">":
            return current > threshold
        elif operator == "<":
            return current < threshold
        elif operator == ">=":
            return current >= threshold
        elif operator == "<=":
            return current <= threshold
        return False

    def evaluate_composite(self, policy: VersionedPolicy, current_metrics: Dict[str, float]) -> bool:
        if not policy.enabled or policy.policy_type != PolicyType.COMPOSITE:
            return False
            
        sub_policies: List[str] = policy.rules.get("sub_policies", [])
        logic = policy.rules.get("logic", "AND")
        
        results = []
        for sp_id in sub_policies:
            sp = self.policies.get(sp_id)
            if sp:
                if sp.policy_type == PolicyType.THRESHOLD:
                    results.append(self.evaluate_threshold(sp, current_metrics))
                    
        if not results:
            return False
            
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        return False

    def evaluate_all(self, current_metrics: Dict[str, float]) -> List[str]:
        violations = []
        for p_id, policy in self.policies.items():
            if policy.policy_type == PolicyType.THRESHOLD:
                if self.evaluate_threshold(policy, current_metrics):
                    violations.append(p_id)
            elif policy.policy_type == PolicyType.COMPOSITE:
                if self.evaluate_composite(policy, current_metrics):
                    violations.append(p_id)
        return violations
