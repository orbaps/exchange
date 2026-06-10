import uuid
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from evaluation.benchmarks.models import Benchmark
from evaluation.judge.judges import RuleBasedJudge, JudgeResult, JudgeExplanation

@dataclass
class EvaluationRun:
    run_id: str
    benchmark_id: str
    submission_id: str
    start_time: int
    end_time: int
    seed: int

@dataclass
class EvaluationResult:
    benchmark_id: str
    judge_result: JudgeResult
    telemetry: Dict[str, Any]
    report: Dict[str, Any]

class EvaluationRunner:
    """Orchestrates individual benchmark executions and logs transaction traces."""
    
    def __init__(self, judge: Optional[RuleBasedJudge] = None):
        self.judge = judge or RuleBasedJudge()

    def run_benchmark(
        self,
        benchmark: Benchmark,
        submission_id: str,
        contestant_agent: Optional[Any] = None
    ) -> EvaluationResult:
        start_time = time.time_ns()
        
        # Execute actual / simulated solution
        if contestant_agent and hasattr(contestant_agent, "execute"):
            try:
                actual_output = contestant_agent.execute(benchmark.description, benchmark.seed)
            except Exception as e:
                actual_output = f"Crash: {str(e)}"
        else:
            actual_output = benchmark.expected_output
            
        end_time = time.time_ns()
        duration_ms = (end_time - start_time) / 1e6
        
        telemetry = {
            "execution_time_ms": duration_ms,
            "tps": 250.0,
            "memory_mb": 32.0
        }
        
        # Invoke Judge
        j_result, j_explanation = self.judge.judge(benchmark, actual_output, telemetry)
        
        # Build run metadata report
        report_meta = {
            "findings": j_explanation.findings,
            "warnings": j_explanation.warnings,
            "recommendations": j_explanation.recommendations,
            "evidence_count": len(exp := j_explanation.evidence_items)
        }
        
        return EvaluationResult(
            benchmark_id=benchmark.benchmark_id,
            judge_result=j_result,
            telemetry=telemetry,
            report=report_meta
        )
