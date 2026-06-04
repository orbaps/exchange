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
                "average_execution_time": 0.0
            }
            
        correctness_scores = [r.benchmark_result.correctness_score for r in successful_runs]
        execution_times = [r.benchmark_result.contestant_execution_time_ms for r in successful_runs]
        
        return {
            "average_correctness": sum(correctness_scores) / len(correctness_scores),
            "maximum_correctness": max(correctness_scores),
            "minimum_correctness": min(correctness_scores),
            "average_execution_time": sum(execution_times) / len(execution_times)
        }
