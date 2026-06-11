from federation.clock import DeterministicClock
from governance.models import ApprovalRequest, ApprovalState, RiskSeverity, GovernanceDecision

class ApprovalLayer:
    def __init__(self, clock: DeterministicClock, block_emergency: bool = True):
        self.clock = clock
        self.block_emergency = block_emergency

    def evaluate_request(self, decision: GovernanceDecision) -> ApprovalRequest:
        now = self.clock.now()
        req_id = f"req_{decision.decision_id}"
        
        severity = RiskSeverity.LOW
        if decision.risk_assessment:
            severity = decision.risk_assessment.severity
            
        required_state = ApprovalState.AUTO_APPROVED
        current_state = ApprovalState.AUTO_APPROVED
        
        if severity == RiskSeverity.CRITICAL:
            required_state = ApprovalState.EMERGENCY_ONLY
            current_state = ApprovalState.PENDING if self.block_emergency else ApprovalState.AUTO_APPROVED
        elif severity == RiskSeverity.HIGH:
            required_state = ApprovalState.FEDERATION_REVIEW
            current_state = ApprovalState.PENDING
        elif severity == RiskSeverity.MEDIUM:
            required_state = ApprovalState.OPERATOR_REVIEW
            current_state = ApprovalState.PENDING
            
        return ApprovalRequest(req_id, decision.decision_id, required_state, current_state, now)
