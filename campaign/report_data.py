from dataclasses import dataclass
from typing import Dict

@dataclass
class ContestantReportData:
    contestant_id: str
    average_correctness: float
    total_mismatches: int
    successful_runs: int
    failed_runs: int

@dataclass
class ReportData:
    campaign_id: str
    total_runs: int
    overall_success_rate: float
    contestants: Dict[str, ContestantReportData]
