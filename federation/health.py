from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class ReplicaState(str, Enum):
    HEALTHY = "HEALTHY"
    LAGGING = "LAGGING"
    SYNCING = "SYNCING"
    PARTITIONED = "PARTITIONED"
    RECOVERING = "RECOVERING"
    UPGRADING = "UPGRADING"

@dataclass
class ClusterHealth:
    """Dataclass holding all High-Availability and Consensus health metrics."""
    active_nodes: List[str] = field(default_factory=list)
    quorum_size: int = 0
    current_leader: Optional[str] = None
    election_count: int = 0
    replication_lag: Dict[str, int] = field(default_factory=dict)
    commit_index: int = 0
    snapshot_age: float = 0.0
    recovery_events: List[Dict[str, Any]] = field(default_factory=list)
    lock_contention: int = 0
    
    # Replica status dictionary (node_id -> ReplicaState)
    replica_states: Dict[str, ReplicaState] = field(default_factory=dict)

    # Phase 8.0 Orchestration extensions
    cpu_pressure_score: float = 0.0
    memory_pressure_score: float = 0.0
    health_score: float = 100.0
    anomaly_count: int = 0
    predicted_failure_risk: float = 0.0
    node_health_states: Dict[str, str] = field(default_factory=dict)
