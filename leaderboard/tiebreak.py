from typing import Tuple, Any
from leaderboard.models import LeaderboardEntry

class TieBreaker:
    """Generates deterministic sorting keys for leaderboard entries."""
    
    @staticmethod
    def get_sort_key(entry: LeaderboardEntry) -> Tuple[Any, ...]:
        """
        Returns a tuple used for Python's sort().
        Sorting priorities:
        1. Final Score (Descending)
        2. Correctness (Descending)
        3. Reliability (Descending)
        4. Latency (Ascending)
        5. Contestant ID (Ascending)
        """
        return (
            -entry.score,
            -entry.average_correctness,
            -entry.success_rate,
            entry.average_latency,
            entry.contestant_id
        )
