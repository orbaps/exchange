from governance.models import GovernanceDecision, DecisionGraph

class ExplainabilityEngine:
    def generate_explanation(self, decision: GovernanceDecision) -> str:
        parts = []
        parts.append(f"Decision {decision.decision_id} to {decision.action_type} on {decision.target}.")
        
        if decision.risk_assessment:
            ra = decision.risk_assessment
            parts.append(f"Mitigates {ra.severity.name} risk of {ra.category.name}.")
            parts.append(f"Confidence: {ra.confidence.score*100:.1f}%. Rationale: {ra.confidence.rationale}")
            
        if decision.simulation_result:
            sr = decision.simulation_result
            status = "maintained" if sr.quorum_maintained else "lost"
            parts.append(f"Simulation validated action with quorum {status}.")
            
        if decision.approval_request:
            ar = decision.approval_request
            parts.append(f"Approval state: {ar.current_state.name} (Required: {ar.required_state.name}).")
            
        return " ".join(parts)

    def generate_graph(self, decision: GovernanceDecision) -> DecisionGraph:
        nodes = [{"id": decision.decision_id, "label": decision.action_type}]
        edges = []
        
        if decision.risk_assessment:
            nodes.append({"id": "risk", "label": decision.risk_assessment.category.name})
            edges.append({"source": "risk", "target": decision.decision_id, "label": "triggers"})
            
        if decision.simulation_result:
            nodes.append({"id": "sim", "label": "Simulation"})
            edges.append({"source": decision.decision_id, "target": "sim", "label": "validated_by"})
            
        return DecisionGraph(nodes, edges)
