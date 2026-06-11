from federation.clock import DeterministicClock
from strategic.planner import StrategicPlanner
from strategic.optimizer import FederationOptimizer
from strategic.risk import GlobalRiskEngine
from strategic.recovery import DisasterRecoveryPlanner
from strategic.policies import PolicyHierarchyManager
from strategic.simulation import FederationSimulationEngine
from strategic.journal import StrategicJournal
from strategic.metrics import StrategicMetrics
from strategic.models import ClusterProfile, OptimizationAlgorithm, GlobalRiskAssessment
from typing import List, Dict, Any

class MultiClusterGovernanceCoordinator:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock
        self.planner = StrategicPlanner(clock)
        self.optimizer = FederationOptimizer(clock)
        self.risk_engine = GlobalRiskEngine(clock)
        self.recovery = DisasterRecoveryPlanner(clock)
        self.policies = PolicyHierarchyManager()
        self.simulator = FederationSimulationEngine(clock)
        self.journal = StrategicJournal()
        self.metrics = StrategicMetrics(clock)

    def execute_pipeline(
        self, 
        clusters: List[ClusterProfile], 
        gov_risks: List[Dict[str, Any]],
        cons_risks: List[Dict[str, Any]],
        rep_risks: List[Dict[str, Any]],
        cap_risks: List[Dict[str, Any]]
    ):
        now = self.clock.now()
        
        # 1. Risk
        global_risk = self.risk_engine.aggregate_risks(gov_risks, cons_risks, rep_risks, cap_risks)
        self.metrics.set_global_risk(global_risk.overall_severity)
        
        # 2. Optimization (Evaluate current state)
        # We always evaluate LEAST_LOADED as baseline
        opt_scores = self.optimizer.optimize_workload(clusters, OptimizationAlgorithm.LEAST_LOADED)
        
        # 3. Planning
        active_cluster_ids = [c.cluster_id for c in clusters if c.health_status == "HEALTHY"]
        plans = self.planner.generate_all_plans(active_cluster_ids, {"avg_score": opt_scores[0].score if opt_scores else 0})
        self.metrics.record_plan()
        
        # 4. Simulation & Journaling of immediate plan (+1h)
        if plans and len(plans) > 0:
            short_term_plan = plans[0]
            sim_fingerprint = self.simulator.simulate_plan(short_term_plan.actions, {"risk": global_risk.overall_severity})
            
            # Execute Actions deterministically
            for action in short_term_plan.actions:
                self.metrics.record_action()
                self.journal.append(
                    timestamp=now,
                    plan_id=short_term_plan.plan_id,
                    action=action.action_type,
                    cluster_id=action.target_cluster
                )
