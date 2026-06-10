from dataclasses import dataclass

@dataclass
class TPSStatistics:
    total_events: int
    runtime_seconds: float
    tps: float

class TPSCalculator:
    """Calculates Throughput (TPS) from event counts and runtime."""
    
    @staticmethod
    def calculate(total_events: int, runtime_seconds: float) -> TPSStatistics:
        if runtime_seconds <= 0.0:
            return TPSStatistics(total_events, runtime_seconds, 0.0)
            
        return TPSStatistics(
            total_events=total_events,
            runtime_seconds=runtime_seconds,
            tps=total_events / runtime_seconds
        )
