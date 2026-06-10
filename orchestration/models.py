from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class NodeOrchestrationMetrics:
    """Historical and current operational metrics for a single node."""
    node_id: str
    timestamp: float
    cpu_usage: float  # Percentage (0.0 to 100.0)
    memory_usage: float  # Percentage (0.0 to 100.0)
    load: float  # Average job capacity load
    job_count: int
    replication_lag: int
    term: int
    network_latency: float  # virtual seconds delay

@dataclass
class AnomalyRecord:
    """Representation of a detected system or node anomaly."""
    anomaly_id: str
    node_id: str
    type: str  # CPU_SPIKE, MEM_PRESSURE, ELECTION_STORM, REP_LAG, MEMB_CHURN, PARTITION_INSTABILITY
    severity: str  # LOW, MEDIUM, HIGH
    timestamp: float
    details: str

@dataclass
class CapacityForecast:
    """Deterministic forecasting indicators for capacity bottlenecks."""
    node_id: str
    timestamp: float
    predicted_cpu: float
    predicted_memory: float
    predicted_failure_risk: float  # Scale 0.0 to 1.0
    bottleneck_time: Optional[float] = None  # Future timestamp when bottleneck occurs

@dataclass
class OrchestrationPolicy:
    """Policy rules governing autonomous cluster rebalancing and self-healing triggers."""
    policy_id: str
    name: str
    rule_expr: str  # Rule representation (e.g. CPU > 85%)
    action_type: str  # REBALANCE, RESTART, REJOIN, etc.
    enabled: bool = True

@dataclass
class AutonomousAction:
    """An autonomous execution command scheduled by the Decision Engine."""
    action_id: str
    node_id: str
    action_type: str  # RESTART_NODE, RECOVER_REPLICA, RESTORE_SNAPSHOT, REBUILD_REPLICATION, REJOIN, REBALANCE
    status: str  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    timestamp: float
    explanation: str
    evidence: List[str] = field(default_factory=list)

@dataclass
class OrchestrationDecision:
    """Explainable consolidation of active issues and recommended recovery actions."""
    decision_id: str
    timestamp: float
    analysis: str
    confidence_score: float  # 0.0 to 1.0
    recommendations: List[AutonomousAction] = field(default_factory=list)
    evidence_chain: List[str] = field(default_factory=list)
