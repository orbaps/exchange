from typing import Optional
from telemetry.execution import ExecutionStatistics
from telemetry.tps import TPSStatistics

class ThroughputScorer:
    """Computes a 0-100 score based on throughput/EPS statistics."""
    
    @staticmethod
    def calculate(sandbox_stats: Optional[ExecutionStatistics], framework_stats: TPSStatistics) -> float:
        # Prioritize ExecutionStatistics.eps over TPSStatistics.tps
        eps = 0.0
        if sandbox_stats and sandbox_stats.runtime_ms > 0:
            eps = sandbox_stats.eps
        else:
            eps = framework_stats.tps
            
        if eps >= 100000.0:
            return 100.0
        elif eps >= 50000.0:
            return ThroughputScorer._interpolate(eps, 50000.0, 100000.0, 90.0, 100.0)
        elif eps >= 25000.0:
            return ThroughputScorer._interpolate(eps, 25000.0, 50000.0, 80.0, 90.0)
        elif eps >= 10000.0:
            return ThroughputScorer._interpolate(eps, 10000.0, 25000.0, 60.0, 80.0)
        elif eps >= 5000.0:
            return ThroughputScorer._interpolate(eps, 5000.0, 10000.0, 40.0, 60.0)
        else:
            return 20.0
            
    @staticmethod
    def _interpolate(x: float, a: float, b: float, y_bot: float, y_top: float) -> float:
        """
        Linearly interpolates x in [a, b] to a score in [y_bot, y_top].
        y_bot corresponds to 'a' (lower EPS = lower score).
        y_top corresponds to 'b' (higher EPS = higher score).
        """
        return y_bot + (y_top - y_bot) * (x - a) / (b - a)
