from telemetry.latency import LatencyStatistics

class LatencyScorer:
    """Computes a 0-100 score based on latency statistics (p99)."""
    
    @staticmethod
    def calculate(stats: LatencyStatistics) -> float:
        p99 = stats.p99_ms
        
        if p99 <= 1.0:
            return 100.0
        elif p99 <= 5.0:
            return LatencyScorer._interpolate(p99, 1.0, 5.0, 100.0, 90.0)
        elif p99 <= 10.0:
            return LatencyScorer._interpolate(p99, 5.0, 10.0, 90.0, 80.0)
        elif p99 <= 20.0:
            return LatencyScorer._interpolate(p99, 10.0, 20.0, 80.0, 60.0)
        elif p99 <= 50.0:
            return LatencyScorer._interpolate(p99, 20.0, 50.0, 60.0, 40.0)
        else:
            return 20.0
            
    @staticmethod
    def _interpolate(x: float, a: float, b: float, y_top: float, y_bot: float) -> float:
        """
        Linearly interpolates x in [a, b] to a score in [y_bot, y_top].
        y_top corresponds to 'a' (better/lower latency = higher score).
        y_bot corresponds to 'b' (worse/higher latency = lower score).
        """
        return y_bot + (y_top - y_bot) * (b - x) / (b - a)
