from typing import List, Dict, Any
from uuid import uuid4
from federation.clock import DeterministicClock
from governance.models import RiskAssessment, RiskCategory, RiskSeverity, EvidenceChain, ConfidenceScore, CapacityForecast, FailureForecast, PartitionForecast

class RiskEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def assess_capacity_risk(self, forecast: CapacityForecast) -> RiskAssessment:
        now = self.clock.now()
        severity = RiskSeverity.LOW
        score = 0.1
        rationale = "Capacity within normal limits."
        
        if forecast.projected_value_1h > 90.0:
            severity = RiskSeverity.CRITICAL
            score = 0.95
            rationale = "Capacity projected to exceed 90% in 1 hour."
        elif forecast.projected_value_24h > 85.0:
            severity = RiskSeverity.HIGH
            score = 0.8
            rationale = "Capacity projected to exceed 85% in 24 hours."
            
        evidence = EvidenceChain(f"ev_cap_{now}", events=[{"forecast": "capacity", "value": forecast.projected_value_1h}], correlation_reason=rationale)
        cat = RiskCategory.CAPACITY_CPU if forecast.metric == "cpu" else RiskCategory.CAPACITY_MEMORY
        
        return RiskAssessment(f"risk_{forecast.metric}_{now}", cat, severity, evidence, ConfidenceScore(score, rationale), now)

    def assess_failure_risk(self, forecast: FailureForecast) -> RiskAssessment:
        now = self.clock.now()
        severity = RiskSeverity.LOW
        if forecast.failure_probability > 0.8:
            severity = RiskSeverity.CRITICAL
        elif forecast.failure_probability > 0.5:
            severity = RiskSeverity.HIGH
            
        rationale = f"Failure probability is {forecast.failure_probability:.2f}"
        evidence = EvidenceChain(f"ev_fail_{forecast.node_id}_{now}", events=[{"forecast": "failure", "prob": forecast.failure_probability}], correlation_reason=rationale)
        return RiskAssessment(f"risk_failure_{forecast.node_id}_{now}", RiskCategory.NODE_FAILURE, severity, evidence, ConfidenceScore(forecast.failure_probability, rationale), now)

    def assess_partition_risk(self, forecast: PartitionForecast) -> RiskAssessment:
        now = self.clock.now()
        severity = RiskSeverity.LOW
        if forecast.probability > 0.7:
            severity = RiskSeverity.CRITICAL
        elif forecast.probability > 0.4:
            severity = RiskSeverity.HIGH
            
        rationale = f"Partition probability is {forecast.probability:.2f}"
        evidence = EvidenceChain(f"ev_part_{now}", events=[{"forecast": "partition", "prob": forecast.probability}], correlation_reason=rationale)
        return RiskAssessment(f"risk_partition_{now}", RiskCategory.NETWORK_PARTITION, severity, evidence, ConfidenceScore(forecast.probability, rationale), now)
