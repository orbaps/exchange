from dataclasses import dataclass
from typing import Dict

@dataclass
class ContestantReportData:
    contestant_id: str
    average_correctness: float
    average_execution_time: float
    total_mismatches: int
    successful_runs: int
    failed_runs: int
    average_latency_ms: float = 0.0
    best_latency_ms: float = 0.0
    worst_latency_ms: float = 0.0
    average_tps: float = 0.0
    best_tps: float = 0.0
    worst_tps: float = 0.0
    success_rate: float = 0.0
    average_score: float = 0.0
    best_score: float = 0.0
    worst_score: float = 0.0
    score_stddev: float = 0.0

@dataclass
class ReportData:
    campaign_id: str
    total_runs: int
    overall_success_rate: float
    contestants: Dict[str, ContestantReportData]
