from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class OptimizationAlgorithm(Enum):
    LEAST_LOADED = "LEAST_LOADED"
    CAPACITY_AWARE = "CAPACITY_AWARE"
    RISK_AWARE = "RISK_AWARE"

class PolicyPriority(Enum):
    CLUSTER = 1
    REGIONAL = 2
    GLOBAL = 3
    EMERGENCY = 4

@dataclass
class ClusterProfile:
    cluster_id: str
    region: str
    active_nodes: int
    cpu_utilization: float
    memory_utilization: float
    health_status: str

@dataclass
class FederationCapacityForecast:
    forecast_id: str
    cluster_forecasts: Dict[str, Dict[str, float]]
    timestamp: float

@dataclass
class StrategicAction:
    action_id: str
    action_type: str
    target_cluster: str
    parameters: Dict[str, Any]

@dataclass
class StrategicPlan:
    plan_id: str
    timeframe: str # +1h, +6h, +24h, +7d
    actions: List[StrategicAction]
    confidence_score: float
    evidence_chain: List[str]
    timestamp: float

@dataclass
class GlobalRiskAssessment:
    assessment_id: str
    overall_severity: str
    governance_risks: List[Dict[str, Any]]
    consensus_risks: List[Dict[str, Any]]
    replication_risks: List[Dict[str, Any]]
    capacity_risks: List[Dict[str, Any]]
    timestamp: float

@dataclass
class RecoveryPlan:
    recovery_id: str
    scenario: str
    steps: List[StrategicAction]
    estimated_downtime_s: float
    timestamp: float

@dataclass
class OptimizationScore:
    cluster_id: str
    score: float
    algorithm: OptimizationAlgorithm
    rationale: str
