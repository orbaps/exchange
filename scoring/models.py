from dataclasses import dataclass

@dataclass
class ScoreBreakdown:
    correctness_score: float
    latency_score: float
    throughput_score: float
    reliability_score: float
    final_score: float
    
    # Raw metrics for transparency
    raw_correctness: float
    raw_p99_latency_ms: float
    raw_eps: float
    raw_success_rate: float
    
    scoring_version: int = 1

@dataclass
class ScoreResult:
    contestant_id: str
    scenario_id: str
    breakdown: ScoreBreakdown
