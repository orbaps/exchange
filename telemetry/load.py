from dataclasses import dataclass, field
from typing import Dict

@dataclass
class LoadGenerationStatistics:
    """Metrics regarding the generation of a bot fleet campaign."""
    generated_events: int = 0
    events_per_second: float = 0.0
    bot_count: int = 0
    worker_count: int = 0
    generation_runtime_ms: float = 0.0
    event_mix: Dict[str, float] = field(default_factory=dict)
