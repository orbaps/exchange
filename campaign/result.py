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

@dataclass
class ContestantCampaignResult:
    """The aggregate results for a single contestant across the campaign."""
    contestant_id: str
    average_correctness: float = 0.0
    total_mismatches: int = 0
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
