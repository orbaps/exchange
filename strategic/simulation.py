import hashlib
import json
from federation.clock import DeterministicClock
from typing import Dict, Any, List
from strategic.models import StrategicAction

class FederationSimulationEngine:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def simulate_plan(self, actions: List[StrategicAction], initial_state: Dict[str, Any]) -> str:
        # We need a deterministic SHA256 fingerprint of the simulation state after applying actions
        
        # Make a copy of state to "simulate"
        state = dict(initial_state)
        
        for action in actions:
            # Simulate applying the action deterministically
            state[f"action_applied_{action.action_id}"] = True
            
        # Add clock timestamp for determinism
        state["sim_timestamp"] = self.clock.now()
        
        # Serialize state deterministically (sort_keys=True)
        serialized = json.dumps(state, sort_keys=True)
        
        # Generate fingerprint
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
