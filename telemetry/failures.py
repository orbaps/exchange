from dataclasses import dataclass
from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from campaign.result import CampaignRunResult
    from sandbox.result import SandboxResult

@dataclass
class FailureStatistics:
    success_count: int
    failure_count: int
    timeout_count: int
    crash_count: int
    success_rate: float
    failure_rate: float

class FailureCalculator:
    """Calculates success/failure rates from run results."""
    
    @staticmethod
    def calculate_from_campaign_runs(runs: List['CampaignRunResult']) -> FailureStatistics:
        from campaign.result import RunStatus
        if not runs:
            return FailureStatistics(0, 0, 0, 0, 0.0, 0.0)
            
        success_count = 0
        failure_count = 0
        
        for run in runs:
            if run.status == RunStatus.SUCCESS:
                success_count += 1
            else:
                failure_count += 1
                
        total = success_count + failure_count
        return FailureStatistics(
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=0, # Detail not natively available in base CampaignRunResult without parsing error strings, but we will rely on SandboxResult if detailed.
            crash_count=failure_count, # Assume failed equals crash for raw campaign unless SandboxResult is provided
            success_rate=(success_count / total) * 100.0,
            failure_rate=(failure_count / total) * 100.0
        )
        
    @staticmethod
    def calculate_from_sandbox_results(results: List['SandboxResult']) -> FailureStatistics:
        if not results:
            return FailureStatistics(0, 0, 0, 0, 0.0, 0.0)
            
        success_count = sum(1 for r in results if r.success)
        timeout_count = sum(1 for r in results if r.timed_out)
        crash_count = sum(1 for r in results if r.crashed)
        
        failure_count = len(results) - success_count
        total = len(results)
        
        return FailureStatistics(
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
            crash_count=crash_count,
            success_rate=(success_count / total) * 100.0,
            failure_rate=(failure_count / total) * 100.0
        )
