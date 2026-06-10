import statistics
from dataclasses import dataclass
from leaderboard.models import LeaderboardSnapshot

@dataclass
class AnalyticsReport:
    best_score: float
    worst_score: float
    average_score: float
    median_score: float
    score_spread: float

class LeaderboardAnalytics:
    """Computes analytics over a LeaderboardSnapshot."""
    
    @staticmethod
    def calculate(snapshot: LeaderboardSnapshot) -> AnalyticsReport:
        if not snapshot.entries:
            return AnalyticsReport(0.0, 0.0, 0.0, 0.0, 0.0)
            
        scores = [e.score for e in snapshot.entries]
        
        best = max(scores)
        worst = min(scores)
        avg = sum(scores) / len(scores)
        median = statistics.median(scores)
        spread = best - worst
        
        return AnalyticsReport(
            best_score=best,
            worst_score=worst,
            average_score=avg,
            median_score=median,
            score_spread=spread
        )
