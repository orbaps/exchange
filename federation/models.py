from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class NodeRole(str, Enum):
    COORDINATOR = "COORDINATOR"
    WORKER = "WORKER"
    JUDGE = "JUDGE"
    ANALYTICS = "ANALYTICS"
    OBSERVER = "OBSERVER"

@dataclass
class NodeCapabilities:
    supported_domains: List[str] = field(default_factory=list)  # e.g., ["CODING", "REASONING"]
    max_concurrent_jobs: int = 4
    memory_mb: float = 8192.0
    cpu_cores: int = 4

@dataclass
class NodeInfo:
    node_id: str
    hostname: str
    version: str
    public_key: str
    roles: List[NodeRole]
    capabilities: NodeCapabilities
    registered_at: int
    last_seen: int
    load: float = 0.0  # current cpu/jobs load percentage
    status: str = "ACTIVE"  # ACTIVE, OFFLINE, EXPIRED

@dataclass
class FederationMember:
    node_id: str
    node_info: NodeInfo
    status: str = "ACTIVE"

@dataclass
class FederationConfig:
    heartbeat_interval: float = 5.0
    timeout_seconds: float = 30.0

@dataclass
class FederationHeartbeat:
    node_id: str
    timestamp: int

@dataclass
class FederationSnapshot:
    snapshot_id: str
    timestamp: int
    members: List[NodeInfo] = field(default_factory=list)
    active_jobs_count: int = 0
