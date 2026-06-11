from typing import Dict, Any, List
from uuid import uuid4
from federation.clock import DeterministicClock
from governance.models import GovernanceDecision, VersionedPolicy, ApprovalState, SimulationConfig, SimulationType
from governance.prediction import PredictionEngine
from governance.risk import RiskEngine
from governance.simulation import SimulationEngine
from governance.policies import PolicyEngine
from governance.evolution import PolicyEvolutionEngine
from governance.approval import ApprovalLayer
from governance.explainability import ExplainabilityEngine
from governance.journal import GovernanceJournal
from governance.metrics import GovernanceMetrics

class GovernanceEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock
        self.prediction_engine = PredictionEngine(clock)
        self.risk_engine = RiskEngine(clock)
        self.simulation_engine = SimulationEngine(clock)
        self.policy_engine = PolicyEngine()
        self.evolution_engine = PolicyEvolutionEngine(self.simulation_engine)
        self.approval_layer = ApprovalLayer(clock, block_emergency=True)
        self.explainability_engine = ExplainabilityEngine()
        self.journal = GovernanceJournal()
        self.metrics = GovernanceMetrics()

    def process_system_state(self, current_state: Dict[str, Any], historical_metrics: Dict[str, Any]):
        now = self.clock.now()
        
        # 1. Prediction & Risk
        for node_id, history in historical_metrics.get("cpu_history", {}).items():
            forecast = self.prediction_engine.forecast_capacity(node_id, "cpu", history)
            risk = self.risk_engine.assess_capacity_risk(forecast)
            
            if risk.severity.name != "LOW":
                self.metrics.record_risk(risk.severity.name)
                # 2. Simulation & Decision
                sim_config = SimulationConfig(SimulationType.CAPACITY, [], {"cpu_increase": -10.0}) # simulate mitigation
                sim_result = self.simulation_engine.run_simulation(sim_config, current_state)
                self.metrics.record_simulation()
                
                decision = GovernanceDecision(
                    decision_id=f"dec_{node_id}_{now}",
                    action_type="THROTTLE_WORKLOAD",
                    target=node_id,
                    parameters={"throttle_pct": 10},
                    risk_assessment=risk,
                    simulation_result=sim_result,
                    approval_request=None,
                    timestamp=now
                )
                
                # 3. Approval
                app_req = self.approval_layer.evaluate_request(decision)
                decision.approval_request = app_req
                
                if app_req.current_state == ApprovalState.AUTO_APPROVED:
                    decision.executed = True
                
                # 4. Journaling
                self.journal.append(decision, now)
                self.metrics.record_decision()
                
        # 5. Policy Evolution
        violations = self.policy_engine.evaluate_all(current_state.get("current_metrics", {}))
        for p_id in violations:
            self.metrics.record_violation()
            policy = self.policy_engine.policies[p_id]
            evolved = self.evolution_engine.evolve_policy(policy, current_state)
            if evolved:
                self.policy_engine.register_policy(evolved)
                self.metrics.record_evolution()
                
                decision = GovernanceDecision(
                    decision_id=f"dec_evolve_{p_id}_{now}",
                    action_type="EVOLVE_POLICY",
                    target=p_id,
                    parameters={"old_version": policy.version, "new_version": evolved.version},
                    risk_assessment=None,
                    simulation_result=None,
                    approval_request=None,
                    timestamp=now,
                    executed=True
                )
                self.journal.append(decision, now)
                self.metrics.record_decision()
