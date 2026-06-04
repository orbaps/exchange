from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ScenarioEvent:
    """Represents a discrete event (e.g., place_order, cancel_order) to inject into an engine."""
    timestamp: int
    event_type: str
    payload: Dict[str, Any]

@dataclass
class BenchmarkScenario:
    """Represents deterministic test input for an exchange benchmark."""
    scenario_id: str
    name: str
    description: str
    seed: int
    events: List[ScenarioEvent] = field(default_factory=list)
