import hashlib
from typing import Dict, Any
from federation.clock import DeterministicClock
from governance.models import SimulationConfig, SimulationResult, SimulationType

class SimulationEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def run_simulation(self, config: SimulationConfig, current_state: Dict[str, Any]) -> SimulationResult:
        now = self.clock.now()
        success = True
        quorum_maintained = True
        metrics_impact = {"cpu": 0.0, "memory": 0.0}
        
        active_nodes = current_state.get("active_nodes", 5)
        quorum_size = (active_nodes // 2) + 1
        
        if config.sim_type == SimulationType.NODE_FAILURE:
            target_count = len(config.target_nodes)
            remaining = active_nodes - target_count
            if remaining < quorum_size:
                quorum_maintained = False
            
            # Simulated load shift: surviving nodes take on load of dead nodes
            if remaining > 0:
                metrics_impact["cpu"] = (target_count * 20.0) / remaining
                metrics_impact["memory"] = (target_count * 15.0) / remaining
            
        elif config.sim_type == SimulationType.PARTITION:
            target_count = len(config.target_nodes)
            if target_count >= quorum_size:
                quorum_maintained = False
            metrics_impact["cpu"] = 5.0 # mild overhead from retries
            
        elif config.sim_type == SimulationType.CAPACITY:
            # Simulate adding load
            metrics_impact["cpu"] = config.parameters.get("cpu_increase", 0.0)
            metrics_impact["memory"] = config.parameters.get("memory_increase", 0.0)
            if metrics_impact["cpu"] > 100.0:
                success = False

        fingerprint = hashlib.sha256(
            f"{config.sim_type.name}_{quorum_maintained}_{metrics_impact['cpu']}_{metrics_impact['memory']}".encode()
        ).hexdigest()
        
        return SimulationResult(config, success, quorum_maintained, metrics_impact, fingerprint, now)
