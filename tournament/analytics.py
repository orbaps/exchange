from dataclasses import dataclass
from typing import List

from tournament.models import TournamentResult

@dataclass
class TournamentAnalytics:
    active_contestants: int
    eliminated_contestants: int
    average_score: float
    best_score: float
    worst_score: float
    stage_completion_rate: float
    
    @staticmethod
    def compute(result: TournamentResult) -> 'TournamentAnalytics':
        if not result.stage_results:
            return TournamentAnalytics(0, 0, 0.0, 0.0, 0.0, 0.0)
            
        initial_started = len(result.stage_results[0].contestants_started)
        if initial_started == 0:
            return TournamentAnalytics(0, 0, 0.0, 0.0, 0.0, 0.0)
            
        final_stage = result.stage_results[-1]
        active = len(final_stage.contestants_advanced)
        eliminated = initial_started - active
        
        all_scores = []
        for stage in result.stage_results:
            for entry in stage.leaderboard_snapshot.entries:
                all_scores.append(entry.score)
                
        if not all_scores:
            avg_s, best_s, worst_s = 0.0, 0.0, 0.0
        else:
            avg_s = sum(all_scores) / len(all_scores)
            best_s = max(all_scores)
            worst_s = min(all_scores)
            
        completion_rate = len(result.stage_results) / max(1, result.total_stages)
            
        return TournamentAnalytics(
            active_contestants=active,
            eliminated_contestants=eliminated,
            average_score=avg_s,
            best_score=best_s,
            worst_score=worst_s,
            stage_completion_rate=completion_rate
        )
