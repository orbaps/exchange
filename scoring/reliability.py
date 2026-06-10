from telemetry.failures import FailureStatistics

class ReliabilityScorer:
    """Computes a 0-100 score based on reliability/success rate."""
    
    @staticmethod
    def calculate(stats: FailureStatistics) -> float:
        # Pass through the success rate directly as requested.
        return stats.success_rate
