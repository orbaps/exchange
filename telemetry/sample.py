from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MetricSample:
    """Raw telemetry point representing any benchmark event duration."""
    timestamp_ns: int
    event_name: str
    duration_ns: int
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FrameworkMetricSample(MetricSample):
    """Telemetry point specifically for framework-level operations (e.g. submit_order adapter latency)."""
    pass
