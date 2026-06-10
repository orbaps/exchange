import math
from dataclasses import dataclass
from typing import List

from telemetry.sample import MetricSample

@dataclass
class LatencyStatistics:
    min_ms: float
    max_ms: float
    avg_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    sample_count: int

class LatencyCalculator:
    """Computes latency percentiles using the nearest-rank method (sorted_samples[index])."""
    
    @staticmethod
    def calculate(samples: List[MetricSample]) -> LatencyStatistics:
        if not samples:
            return LatencyStatistics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)
            
        durations_ms = [s.duration_ns / 1_000_000.0 for s in samples]
        durations_ms.sort()
        
        count = len(durations_ms)
        total = sum(durations_ms)
        
        avg_ms = total / count
        min_ms = durations_ms[0]
        max_ms = durations_ms[-1]
        
        # Nearest-rank method for percentiles
        def get_percentile(p: float) -> float:
            # p is expected to be between 0 and 1 (e.g. 0.99 for p99)
            # Nearest rank: index = ceil(p * N) - 1
            # We use math.ceil to match standard nearest-rank formulation
            # For a single element, p=0.5 -> ceil(0.5 * 1) - 1 = 1 - 1 = 0
            rank = math.ceil(p * count)
            # Ensure it's within bounds
            idx = max(0, min(rank - 1, count - 1))
            return durations_ms[idx]
            
        return LatencyStatistics(
            min_ms=min_ms,
            max_ms=max_ms,
            avg_ms=avg_ms,
            p50_ms=get_percentile(0.50),
            p90_ms=get_percentile(0.90),
            p95_ms=get_percentile(0.95),
            p99_ms=get_percentile(0.99),
            sample_count=count
        )
