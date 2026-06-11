from typing import Dict, Any, Optional
import copy
from governance.models import VersionedPolicy, PolicyType, SimulationConfig, SimulationType
from governance.simulation import SimulationEngine

class PolicyEvolutionEngine:
    def __init__(self, simulation_engine: SimulationEngine):
        self.simulation_engine = simulation_engine

    def evolve_policy(self, policy: VersionedPolicy, current_state: Dict[str, Any]) -> Optional[VersionedPolicy]:
        if policy.policy_type != PolicyType.THRESHOLD:
            return None # Only evolve simple thresholds for now
            
        current_val = policy.rules.get("value", 80.0)
        
        # Propose a 5% tighter threshold
        proposed_val = current_val * 0.95
        
        # Simulate with proposed stricter policy to see if it causes false positive violations
        # We simulate a normal capacity increase
        sim_config = SimulationConfig(
            sim_type=SimulationType.CAPACITY,
            target_nodes=[],
            parameters={"cpu_increase": proposed_val * 0.9} # Simulate load just under new threshold
        )
        
        result = self.simulation_engine.run_simulation(sim_config, current_state)
        
        # If the simulation remains healthy under the new threshold, we can adopt it
        if result.success and result.quorum_maintained:
            new_policy = copy.deepcopy(policy)
            new_policy.version += 1
            new_policy.rules["value"] = proposed_val
            return new_policy
            
        return None
