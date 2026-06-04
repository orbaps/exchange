from dataclasses import dataclass
from typing import List

from benchmarking.scenario import BenchmarkScenario
from submission.metadata import SubmissionManifest

@dataclass
class BenchmarkCampaign:
    """Defines a grid of scenarios to execute across multiple registered contestants."""
    campaign_id: str
    name: str
    description: str
    scenarios: List[BenchmarkScenario]
    contestants: List[SubmissionManifest]
