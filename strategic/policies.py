from strategic.models import PolicyPriority
from typing import Dict, Any, List

class PolicyHierarchyManager:
    def __init__(self):
        self.policies: List[Dict[str, Any]] = []

    def register_policy(self, policy_id: str, priority: PolicyPriority, rules: Dict[str, Any]):
        self.policies.append({
            "policy_id": policy_id,
            "priority": priority,
            "rules": rules
        })
        
    def resolve_conflicts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Sort policies by priority (descending, 4 is highest) then by policy_id ascending for determinism
        sorted_policies = sorted(self.policies, key=lambda p: (-p["priority"].value, p["policy_id"]))
        
        resolved_rules = {}
        for policy in sorted_policies:
            for rule_key, rule_val in policy["rules"].items():
                if rule_key not in resolved_rules:
                    resolved_rules[rule_key] = rule_val
                    
        return resolved_rules
