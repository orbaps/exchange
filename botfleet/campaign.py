from dataclasses import dataclass
from typing import List
import uuid

from botfleet.config import FleetConfig
from botfleet.events import TradingEvent
from botfleet.orchestrator import BotOrchestrator

@dataclass
class BotCampaignResult:
    total_events: int
    duration_seconds: float
    generation_runtime_ms: float
    generated_events: List[TradingEvent]

class BotCampaign:
    """Represents a discrete load generation pass."""
    
    def __init__(self, profile_name: str, fleet_config: FleetConfig):
        self.campaign_id = str(uuid.uuid4())
        self.profile_name = profile_name
        self.fleet_config = fleet_config
        self.orchestrator = BotOrchestrator(fleet_config)
        
    def execute(self) -> BotCampaignResult:
        """Runs the orchestrator and returns the result."""
        events, runtime_ms = self.orchestrator.generate_fleet_events()
        
        return BotCampaignResult(
            total_events=len(events),
            duration_seconds=self.fleet_config.duration_seconds,
            generation_runtime_ms=runtime_ms,
            generated_events=events
        )
