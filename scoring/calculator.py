from benchmarking.result import BenchmarkResult
from telemetry.failures import FailureStatistics

from scoring.models import ScoreBreakdown, ScoreResult
from scoring.latency import LatencyScorer
from scoring.throughput import ThroughputScorer
from scoring.reliability import ReliabilityScorer

class ScoreCalculator:
    """Calculates final scores from validation and telemetry results."""
    
    SCORING_VERSION = 1
    
    @staticmethod
    def calculate(contestant_id: str, scenario_id: str, benchmark_result: BenchmarkResult, failure_stats: FailureStatistics) -> ScoreResult:
        
        # 1. Component Raw Values
        raw_c = benchmark_result.correctness_score
        
        raw_l = 0.0
        raw_eps = 0.0
        
        if benchmark_result.telemetry_report:
            if benchmark_result.telemetry_report.sandbox_execution:
                raw_eps = benchmark_result.telemetry_report.sandbox_execution.eps
                raw_l = benchmark_result.telemetry_report.sandbox_execution.runtime_ms  # We fallback to runtime since we don't have per-event latency inside sandbox yet
            else:
                raw_eps = benchmark_result.telemetry_report.framework_tps.tps
                raw_l = benchmark_result.telemetry_report.framework_latency.p99_ms
        
        raw_r = failure_stats.success_rate
        
        # 2. Component Scores
        c_score = raw_c
        
        l_score = 0.0
        t_score = 0.0
        
        if benchmark_result.telemetry_report:
            l_score = LatencyScorer.calculate(benchmark_result.telemetry_report.framework_latency)
            t_score = ThroughputScorer.calculate(
                benchmark_result.telemetry_report.sandbox_execution, 
                benchmark_result.telemetry_report.framework_tps
            )
            
        r_score = ReliabilityScorer.calculate(failure_stats)
        
        # 3. Base Formula
        base_final = (0.70 * c_score) + (0.15 * l_score) + (0.10 * t_score) + (0.05 * r_score)
        
        # 4. Correctness Gates (Penalty for incorrect engines)
        final_score = base_final
        if c_score < 50.0:
            final_score = c_score
        elif c_score < 80.0:
            final_score *= 0.75
            
        breakdown = ScoreBreakdown(
            correctness_score=c_score,
            latency_score=l_score,
            throughput_score=t_score,
            reliability_score=r_score,
            final_score=final_score,
            raw_correctness=raw_c,
            raw_p99_latency_ms=raw_l,
            raw_eps=raw_eps,
            raw_success_rate=raw_r,
            scoring_version=ScoreCalculator.SCORING_VERSION
        )
        
        return ScoreResult(
            contestant_id=contestant_id,
            scenario_id=scenario_id,
            breakdown=breakdown
        )
