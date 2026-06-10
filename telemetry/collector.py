from typing import List
from telemetry.sample import MetricSample

class TelemetryCollector:
    """In-memory store for collecting MetricSamples during execution."""
    
    def __init__(self):
        self._samples: List[MetricSample] = []
        
    def record(self, sample: MetricSample) -> None:
        self._samples.append(sample)
        
    def clear(self) -> None:
        self._samples.clear()
        
    def samples(self) -> List[MetricSample]:
        return self._samples
        
    def count(self) -> int:
        return len(self._samples)
