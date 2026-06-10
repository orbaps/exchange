import json
import hashlib
from typing import List, Dict, Any, Optional

class ReplayStateMachine:
    """Consolidated state machine updated by journal event applications during replays."""

    def __init__(self):
        self.health_score: float = 100.0
        self.active_anomalies: List[str] = []
        self.completed_actions: List[str] = []
        self.rebalance_count: int = 0
        self.node_healths: Dict[str, str] = {}

    def apply_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Apply a single journal event to advance the state machine."""
        if event_type == "ANOMALY_DETECTED":
            aid = data.get("anomaly_id", "")
            if aid and aid not in self.active_anomalies:
                self.active_anomalies.append(aid)
        elif event_type == "ANOMALY_CLEARED":
            aid = data.get("anomaly_id", "")
            if aid in self.active_anomalies:
                self.active_anomalies.remove(aid)
        elif event_type in ("SELF_HEAL_TRIGGERED", "SELF_HEAL_COMPLETED", "AUTONOMOUS_ACTION_EXECUTED"):
            act_id = data.get("action_id", "")
            if act_id and act_id not in self.completed_actions:
                self.completed_actions.append(act_id)
        elif event_type == "WORKLOAD_REBALANCED":
            self.rebalance_count += 1
        elif event_type == "HEALTH_UPDATE":
            self.health_score = data.get("health_score", 100.0)
            self.node_healths = {k: str(v) for k, v in data.get("node_health_states", {}).items()}

    def get_signature_dict(self) -> Dict[str, Any]:
        """Returns sorted serialization dict for deterministic fingerprinting."""
        return {
            "health_score": round(self.health_score, 4),
            "active_anomalies": sorted(self.active_anomalies),
            "completed_actions": sorted(self.completed_actions),
            "rebalance_count": self.rebalance_count,
            "node_healths": {k: str(v) for k, v in sorted(self.node_healths.items())}
        }


class OrchestrationReplaySystem:
    """Manages stepping forward, backward, seeking, and fingerprinting of orchestration replay sessions."""

    def __init__(self, journal_entries: List[Dict[str, Any]]):
        self.journal_entries = journal_entries
        self.current_pointer: int = 0  # 1-based index (0 means start of time)
        self.state_machine = ReplayStateMachine()

    def step_forward(self) -> bool:
        """Advance the replay system by one journal entry."""
        if self.current_pointer >= len(self.journal_entries):
            return False
            
        entry = self.journal_entries[self.current_pointer]
        self.state_machine.apply_event(entry["event_type"], entry["data"])
        self.current_pointer += 1
        return True

    def step_backward(self) -> bool:
        """Rewind the replay system by one journal entry."""
        if self.current_pointer <= 0:
            return False
            
        # Reconstruct the state machine from scratch up to current_pointer - 1
        target_pointer = self.current_pointer - 1
        self.seek(target_pointer)
        return True

    def seek(self, index: int) -> bool:
        """Seek to the specified journal index position."""
        if index < 0 or index > len(self.journal_entries):
            return False
            
        # Re-initialize state machine
        self.state_machine = ReplayStateMachine()
        self.current_pointer = 0
        
        # Fast-forward to the target index
        for i in range(index):
            entry = self.journal_entries[i]
            self.state_machine.apply_event(entry["event_type"], entry["data"])
            self.current_pointer += 1
            
        return True

    def compute_fingerprint(self) -> str:
        """Calculate the cryptographic signature hash of the current replayed state."""
        signature_dict = self.state_machine.get_signature_dict()
        serialized = json.dumps(signature_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
