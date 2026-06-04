from dataclasses import dataclass
from typing import Optional

@dataclass
class CampaignConfig:
    """Configuration for running a benchmark campaign."""
    stop_on_failure: bool = False
    max_failures: Optional[int] = None
    record_failures: bool = True
