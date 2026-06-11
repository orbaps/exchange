from federation.clock import DeterministicClock
from strategic.models import GlobalRiskAssessment
from typing import List, Dict, Any

class GlobalRiskEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def aggregate_risks(
        self, 
        governance_risks: List[Dict[str, Any]], 
        consensus_risks: List[Dict[str, Any]], 
        replication_risks: List[Dict[str, Any]], 
        capacity_risks: List[Dict[str, Any]]
    ) -> GlobalRiskAssessment:
        now = self.clock.now()
        assessment_id = f"grisk_{now}"
        
        # Simple deterministic severity calculation
        total_risks = len(governance_risks) + len(consensus_risks) + len(replication_risks) + len(capacity_risks)
        
        if total_risks == 0:
            overall_severity = "LOW"
        elif total_risks < 3:
            overall_severity = "MEDIUM"
        elif total_risks < 6:
            overall_severity = "HIGH"
        else:
            overall_severity = "CRITICAL"
            
        return GlobalRiskAssessment(
            assessment_id, 
            overall_severity, 
            governance_risks, 
            consensus_risks, 
            replication_risks, 
            capacity_risks, 
            now
        )
