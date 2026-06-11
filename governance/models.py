from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from uuid import uuid4

class RiskSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskCategory(Enum):
    CAPACITY_CPU = "CAPACITY_CPU"
    CAPACITY_MEMORY = "CAPACITY_MEMORY"
    NODE_FAILURE = "NODE_FAILURE"
    QUORUM_LOSS = "QUORUM_LOSS"
    NETWORK_PARTITION = "NETWORK_PARTITION"
    REPLICATION_LAG = "REPLICATION_LAG"

class PolicyType(Enum):
    THRESHOLD = "THRESHOLD"
    COMPOSITE = "COMPOSITE"
    TIME_WINDOW = "TIME_WINDOW"

class SimulationType(Enum):
    NODE_FAILURE = "NODE_FAILURE"
    PARTITION = "PARTITION"
    CAPACITY = "CAPACITY"
    MEMBERSHIP = "MEMBERSHIP"

class ApprovalState(Enum):
    PENDING = "PENDING"
    AUTO_APPROVED = "AUTO_APPROVED"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    FEDERATION_REVIEW = "FEDERATION_REVIEW"
    EMERGENCY_ONLY = "EMERGENCY_ONLY"
    APPROVED = "APPROVED"
    DENIED = "DENIED"

@dataclass
class CapacityForecast:
    node_id: str
    metric: str  # "cpu" or "memory"
    projected_value_1h: float
    projected_value_24h: float
    time_to_bottleneck_s: Optional[float]
    timestamp: int

@dataclass
class FailureForecast:
    node_id: str
    failure_probability: float
    time_to_failure_s: Optional[float]
    timestamp: int

@dataclass
class PartitionForecast:
    affected_nodes: List[str]
    probability: float
    timestamp: int

@dataclass
class EvidenceChain:
    chain_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    correlation_reason: str = ""

@dataclass
class ConfidenceScore:
    score: float # 0.0 to 1.0
    rationale: str

@dataclass
class RiskAssessment:
    risk_id: str
    category: RiskCategory
    severity: RiskSeverity
    evidence: EvidenceChain
    confidence: ConfidenceScore
    timestamp: int

@dataclass
class SimulationConfig:
    sim_type: SimulationType
    target_nodes: List[str]
    parameters: Dict[str, Any]

@dataclass
class SimulationResult:
    config: SimulationConfig
    success: bool
    quorum_maintained: bool
    metrics_impact: Dict[str, float]
    state_fingerprint: str
    timestamp: int

@dataclass
class VersionedPolicy:
    policy_id: str
    version: int
    policy_type: PolicyType
    rules: Dict[str, Any]
    enabled: bool

@dataclass
class ApprovalRequest:
    request_id: str
    decision_id: str
    required_state: ApprovalState
    current_state: ApprovalState
    timestamp: int

@dataclass
class GovernanceDecision:
    decision_id: str
    action_type: str
    target: str
    parameters: Dict[str, Any]
    risk_assessment: Optional[RiskAssessment]
    simulation_result: Optional[SimulationResult]
    approval_request: Optional[ApprovalRequest]
    timestamp: int
    executed: bool = False

@dataclass
class DecisionGraph:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

@dataclass
class AuditRecord:
    record_id: str
    previous_hash: str
    timestamp: int
    decision: GovernanceDecision
    hash: str
