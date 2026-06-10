from enum import Enum
from typing import List, Set

class ConfigState(str, Enum):
    STABLE = "STABLE"
    JOINT = "JOINT"
    STABLE_NEW = "STABLE_NEW"

class JointConsensusConfig:
    """Manages Raft two-phase joint consensus configurations for safe membership changes."""

    def __init__(self, initial_nodes: List[str]):
        self.state: ConfigState = ConfigState.STABLE
        self.old_nodes: Set[str] = set(initial_nodes)
        self.new_nodes: Set[str] = set()

    def enter_joint(self, new_nodes: List[str]) -> None:
        """Transition from STABLE to JOINT configuration (C_old,new)."""
        self.state = ConfigState.JOINT
        self.new_nodes = set(new_nodes)

    def enter_stable_new(self) -> None:
        """Transition from JOINT to STABLE_NEW configuration (C_new)."""
        self.state = ConfigState.STABLE_NEW
        self.old_nodes = self.new_nodes.copy()
        self.new_nodes.clear()
        self.state = ConfigState.STABLE  # Reset state back to stable using the new node set

    def get_current_nodes(self) -> List[str]:
        """Return the list of all nodes involved in decision making."""
        if self.state == ConfigState.JOINT:
            return sorted(list(self.old_nodes.union(self.new_nodes)))
        return sorted(list(self.old_nodes))

    def calculate_quorum_reached(self, active_responses: List[str]) -> bool:
        """
        Evaluate if a majority agreement is reached.
        In JOINT state, this requires independent majorities from both C_old and C_new.
        """
        active_set = set(active_responses)
        
        # Helper to check majority
        def has_majority(node_set: Set[str]) -> bool:
            if not node_set:
                return True
            matched = len(node_set.intersection(active_set))
            required = (len(node_set) // 2) + 1
            return matched >= required

        if self.state == ConfigState.STABLE:
            return has_majority(self.old_nodes)
        elif self.state == ConfigState.JOINT:
            # Must satisfy both majorities independently
            return has_majority(self.old_nodes) and has_majority(self.new_nodes)
        elif self.state == ConfigState.STABLE_NEW:
            return has_majority(self.old_nodes)  # old_nodes was updated to new_nodes
            
        return False
