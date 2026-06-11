from federation.clock import DeterministicClock
from strategic.models import RecoveryPlan, StrategicAction
from typing import List

class DisasterRecoveryPlanner:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def simulate_failure(self, scenario: str, affected_clusters: List[str]) -> RecoveryPlan:
        now = self.clock.now()
        recovery_id = f"rec_{scenario}_{now}"
        
        steps = []
        estimated_downtime = 0.0
        
        if scenario == "CLUSTER_FAILURE":
            for cluster in affected_clusters:
                steps.append(StrategicAction(f"act_failover_{cluster}_{now}", "INITIATE_FAILOVER", cluster, {"target_region": "backup"}))
            estimated_downtime = 120.0
        elif scenario == "REGION_FAILURE":
            steps.append(StrategicAction(f"act_promote_{now}", "PROMOTE_REGION", "GLOBAL", {"region": "secondary"}))
            estimated_downtime = 600.0
        elif scenario == "QUORUM_LOSS":
            steps.append(StrategicAction(f"act_force_quorum_{now}", "FORCE_QUORUM", "GLOBAL", {"nodes": affected_clusters}))
            estimated_downtime = 30.0
        elif scenario == "NETWORK_ISOLATION":
            steps.append(StrategicAction(f"act_isolate_{now}", "ISOLATE_CLUSTERS", "GLOBAL", {"clusters": affected_clusters}))
            estimated_downtime = 15.0
            
        return RecoveryPlan(recovery_id, scenario, steps, estimated_downtime, now)
