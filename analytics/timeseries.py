from dataclasses import dataclass
from typing import List

@dataclass
class TimeSeriesPoint:
    timestamp_ns: int
    value: float

class TimeSeries:
    """Maintains a time-series of values with windowing and trailing averages."""
    
    def __init__(self, metric_name: str, max_points: int = 100000):
        self.metric_name = metric_name
        self.max_points = max_points
        self.points: List[TimeSeriesPoint] = []
        
    def append(self, timestamp_ns: int, value: float):
        self.points.append(TimeSeriesPoint(timestamp_ns, value))
        if len(self.points) > self.max_points:
            self.points.pop(0) # Inefficient for large lists, use deque in prod if needed
            
    def latest(self) -> float:
        if not self.points:
            return 0.0
        return self.points[-1].value
        
    def window(self, duration_ns: int, current_time_ns: int) -> List[TimeSeriesPoint]:
        cutoff = current_time_ns - duration_ns
        return [p for p in self.points if p.timestamp_ns >= cutoff]
        
    def trailing_average(self, duration_ns: int, current_time_ns: int) -> float:
        w = self.window(duration_ns, current_time_ns)
        if not w:
            return 0.0
        return sum(p.value for p in w) / len(w)
