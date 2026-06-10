from dataclasses import dataclass
from enum import Enum
from typing import Optional

from campaign.campaign import BenchmarkCampaign

class StageType(Enum):
    QUALIFICATION = "QUALIFICATION"
    GROUP_STAGE = "GROUP_STAGE"
    SEMIFINAL = "SEMIFINAL"
    FINAL = "FINAL"

@dataclass
class TournamentStage:
    stage_id: str
    name: str
    stage_type: StageType
    campaign: BenchmarkCampaign
    advancement_rule: 'AdvancementRule'  # Forward declaration to avoid circular import
