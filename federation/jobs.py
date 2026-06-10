from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

class JobStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"

@dataclass
class DistributedJob:
    job_id: str
    task_type: str  # e.g., "BENCHMARK_EXECUTION", "EVALUATION"
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    assigned_node_id: Optional[str] = None
    created_at: int = 0
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None

@dataclass
class JobAssignment:
    job_id: str
    node_id: str
    assigned_at: int

@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    result_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    completed_at: int = 0
