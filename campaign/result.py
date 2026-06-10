from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from benchmarking.result import BenchmarkResult

class RunStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

@dataclass
class CampaignRunResult:
    """The result of executing one scenario against one contestant."""
    contestant_id: str
    scenario_id: str
    status: RunStatus
    benchmark_result: Optional[BenchmarkResult] = None
    error: Optional[str] = None
    
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from scoring.models import ScoreResult
    score_result: Optional['ScoreResult'] = None

@dataclass
class ContestantCampaignResult:
    """The aggregate results for a single contestant across the campaign."""
    contestant_id: str
    average_correctness: float = 0.0
    maximum_correctness: float = 0.0
    minimum_correctness: float = 0.0
    average_execution_time: float = 0.0
    total_mismatches: int = 0
    
    # Telemetry
    average_latency_ms: float = 0.0
    best_latency_ms: float = 0.0
    worst_latency_ms: float = 0.0
    average_tps: float = 0.0
    best_tps: float = 0.0
    worst_tps: float = 0.0
    success_rate: float = 0.0
    
    # Scoring
    average_score: float = 0.0
    best_score: float = 0.0
    worst_score: float = 0.0
    score_stddev: float = 0.0
    
    scenario_results: List[CampaignRunResult] = field(default_factory=list)
    failed_runs: int = 0

@dataclass
class CampaignResult:
    """The overall results of the entire campaign."""
    campaign_id: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    results: Dict[str, ContestantCampaignResult] = field(default_factory=dict)
    
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from execution.metrics import ExecutionStatistics
    execution_statistics: Optional['ExecutionStatistics'] = None
    load_profile: str = "N/A"
    event_count: int = 0
    worker_count: int = 0
