from typing import List, Dict, Any
from orchestration.models import OrchestrationDecision, AutonomousAction, AnomalyRecord, CapacityForecast

class DecisionEngine:
    """Consolidates system anomalies, forecasts, and policy violations into explainable autonomous actions."""
    
    def __init__(self):
        self.decision_counter = 0
        self.action_counter = 0

    def _next_decision_id(self) -> str:
        self.decision_counter += 1
        return f"dec_{self.decision_counter}"

    def _next_action_id(self) -> str:
        self.action_counter += 1
        return f"act_{self.action_counter}"

    def make_decision(
        self,
        anomalies: List[AnomalyRecord],
        forecasts: List[CapacityForecast],
        violations: List[Dict[str, Any]],
        timestamp: float
    ) -> OrchestrationDecision:
        """
        Correlate anomalies, forecasts, and violations to determine recovery recommendations.
        """
        recommendations: List[AutonomousAction] = []
        evidence_chain: List[str] = []
        analyses: List[str] = []
        
        # 1. Process Anomalies
        for anomaly in anomalies:
            evidence_chain.append(f"Anomaly detected: {anomaly.type} on {anomaly.node_id} (Severity: {anomaly.severity}) - '{anomaly.details}'")
            
            if anomaly.type == "CPU_SPIKE" and anomaly.severity == "HIGH":
                # Recommend workload rebalancing to offload jobs
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id=anomaly.node_id,
                    action_type="REBALANCE",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation=f"Trigger rebalance to offload high CPU usage from node {anomaly.node_id}.",
                    evidence=[anomaly.anomaly_id]
                ))
                analyses.append(f"High CPU workload spike on node {anomaly.node_id}.")
                
            elif anomaly.type == "MEM_PRESSURE" and anomaly.severity == "HIGH":
                # Recommend rebalancing or snapshot compaction
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id=anomaly.node_id,
                    action_type="REBALANCE",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation=f"Trigger rebalance to offload memory pressure from node {anomaly.node_id}.",
                    evidence=[anomaly.anomaly_id]
                ))
                analyses.append(f"Critical memory pressure on node {anomaly.node_id}.")
                
            elif anomaly.type == "REP_LAG" and anomaly.severity == "HIGH":
                # Recommend replication recovery catch-up
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id=anomaly.node_id,
                    action_type="RECOVER_REPLICA",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation=f"Trigger replica recovery catch-up for lagging node {anomaly.node_id}.",
                    evidence=[anomaly.anomaly_id]
                ))
                analyses.append(f"Replication lag on node {anomaly.node_id} exceeded warning threshold.")
                
            elif anomaly.type == "PARTITION_INSTABILITY" and anomaly.severity == "HIGH":
                # Recommend network rejoin
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id=anomaly.node_id,
                    action_type="REJOIN",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation=f"Rebuild network links to stabilize flapping partition node {anomaly.node_id}.",
                    evidence=[anomaly.anomaly_id]
                ))
                analyses.append(f"Partition toggle instability detected on node {anomaly.node_id}.")

            elif anomaly.type == "ELECTION_STORM":
                # Recommend node restart to elect a stable leader
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id="cluster",
                    action_type="REBUILD_REPLICATION",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation="Rebuild replication maps on leader to stabilize cluster election storm.",
                    evidence=[anomaly.anomaly_id]
                ))
                analyses.append("Consensus election storm detected.")

        # 2. Process Capacity Forecasts
        for fc in forecasts:
            if fc.predicted_failure_risk > 0.7:
                evidence_chain.append(f"Capacity Forecast warning: High failure risk ({fc.predicted_failure_risk}) predicted for node {fc.node_id}.")
                
                # Recommend proactive rebalance to prevent failure
                recommendations.append(AutonomousAction(
                    action_id=self._next_action_id(),
                    node_id=fc.node_id,
                    action_type="REBALANCE",
                    status="PENDING",
                    timestamp=timestamp,
                    explanation=f"Proactively rebalance workload to avoid projected capacity bottleneck on node {fc.node_id}.",
                    evidence=[f"fc_{fc.node_id}"]
                ))
                analyses.append(f"Proactive forecast alert for node {fc.node_id} failure risk.")

        # 3. Process Policy Violations
        for violation in violations:
            evidence_chain.append(f"Policy violation: Policy '{violation['policy_name']}' violated on {violation['node_id']} (Rule: '{violation['rule_expr']}', Value: {violation['actual_value']}).")
            
            # Match policy recommended action
            recommendations.append(AutonomousAction(
                action_id=self._next_action_id(),
                node_id=violation["node_id"],
                action_type=violation["action_type"],
                status="PENDING",
                timestamp=timestamp,
                explanation=f"Enforce policy action '{violation['action_type']}' due to violation of '{violation['policy_name']}' on {violation['node_id']}.",
                evidence=[violation["policy_id"]]
            ))
            analyses.append(f"Enforcing policy action {violation['action_type']} on node {violation['node_id']}.")

        # Deduplicate recommendations by action_type + node_id to prevent redundant execution
        seen = set()
        dedup_recs = []
        for r in recommendations:
            key = (r.action_type, r.node_id)
            if key not in seen:
                seen.add(key)
                dedup_recs.append(r)

        # Compute Confidence Score based on correlation
        confidence = 0.5
        if dedup_recs:
            # If an issue was confirmed by both anomalies and policy violations, confidence increases
            if len(anomalies) > 0 and len(violations) > 0:
                confidence = 0.9
            elif len(anomalies) > 0 or len(violations) > 0:
                confidence = 0.75
        else:
            confidence = 1.0  # High confidence that no action is needed
            
        analysis_str = " | ".join(analyses) if analyses else "Cluster is stable. No recovery actions recommended."
        
        return OrchestrationDecision(
            decision_id=self._next_decision_id(),
            timestamp=timestamp,
            analysis=analysis_str,
            recommendations=dedup_recs,
            confidence_score=confidence,
            evidence_chain=evidence_chain
        )
