from typing import List, Dict, Any
from campaign.result import CampaignRunResult, RunStatus

class CampaignMetrics:
    """Calculates statistics for a contestant's campaign run."""
    
    @staticmethod
    def calculate(results: List[CampaignRunResult]) -> Dict[str, Any]:
        successful_runs = [r for r in results if r.status == RunStatus.SUCCESS and r.benchmark_result is not None]
        
        if not successful_runs:
            return {
                "average_correctness": 0.0,
                "maximum_correctness": 0.0,
                "minimum_correctness": 0.0,
                "average_execution_time": 0.0,
                "average_latency_ms": 0.0,
                "best_latency_ms": 0.0,
                "worst_latency_ms": 0.0,
                "average_tps": 0.0,
                "best_tps": 0.0,
                "worst_tps": 0.0,
                "success_rate": 0.0,
                "average_score": 0.0,
                "best_score": 0.0,
                "worst_score": 0.0,
                "score_stddev": 0.0
            }
            
        correctness_scores = [r.benchmark_result.correctness_score for r in successful_runs]
        execution_times = [r.benchmark_result.contestant_execution_time_ms for r in successful_runs]
        
        # Telemetry
        latencies = []
        tps_list = []
        for r in successful_runs:
            if r.benchmark_result.telemetry_report and r.benchmark_result.telemetry_report.sandbox_execution:
                exec_stats = r.benchmark_result.telemetry_report.sandbox_execution
                latencies.append(exec_stats.runtime_ms)
                tps_list.append(exec_stats.eps)
                
        # Fallback to framework latency if no sandbox
        if not latencies:
            for r in successful_runs:
                if r.benchmark_result.telemetry_report:
                    latencies.append(r.benchmark_result.telemetry_report.framework_latency.avg_ms)
                    tps_list.append(r.benchmark_result.telemetry_report.framework_tps.tps)
        
        from telemetry.failures import FailureCalculator
        failure_stats = FailureCalculator.calculate_from_campaign_runs(results)
        
        scores = []
        for r in successful_runs:
            if r.score_result:
                scores.append(r.score_result.breakdown.final_score)
                
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        import math
        score_stddev = 0.0
        if len(scores) > 1:
            variance = sum((s - average_score) ** 2 for s in scores) / len(scores)
            score_stddev = math.sqrt(variance)
        
        return {
            "average_correctness": sum(correctness_scores) / len(correctness_scores),
            "maximum_correctness": max(correctness_scores),
            "minimum_correctness": min(correctness_scores),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "average_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            "best_latency_ms": min(latencies) if latencies else 0.0,
            "worst_latency_ms": max(latencies) if latencies else 0.0,
            "average_tps": sum(tps_list) / len(tps_list) if tps_list else 0.0,
            "best_tps": max(tps_list) if tps_list else 0.0,
            "worst_tps": min(tps_list) if tps_list else 0.0,
            "success_rate": failure_stats.success_rate,
            "average_score": average_score,
            "best_score": max(scores) if scores else 0.0,
            "worst_score": min(scores) if scores else 0.0,
            "score_stddev": score_stddev
        }
