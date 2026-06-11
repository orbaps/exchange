from collections import defaultdict

class GovernanceMetrics:
    def __init__(self):
        self.risks_detected = 0
        self.policy_violations = 0
        self.simulations_run = 0
        self.decisions_rendered = 0
        self.policies_evolved = 0
        self.risks_by_severity = defaultdict(int)

    def record_risk(self, severity_name: str):
        self.risks_detected += 1
        self.risks_by_severity[severity_name] += 1

    def record_violation(self):
        self.policy_violations += 1

    def record_simulation(self):
        self.simulations_run += 1

    def record_decision(self):
        self.decisions_rendered += 1

    def record_evolution(self):
        self.policies_evolved += 1
        
    def get_snapshot(self) -> dict:
        return {
            "risks_detected": self.risks_detected,
            "policy_violations": self.policy_violations,
            "simulations_run": self.simulations_run,
            "decisions_rendered": self.decisions_rendered,
            "policies_evolved": self.policies_evolved,
            "risks_by_severity": dict(self.risks_by_severity)
        }
