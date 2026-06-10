from typing import List, Dict

from tournament.models import StageResult

class TournamentRanking:
    """Merges multiple stages into overall rankings.
    Delegates the tie-breaking to the LeaderboardSnapshot's natural sorting order 
    (Score -> Correctness -> Reliability -> Latency).
    """
    
    @staticmethod
    def generate_final_rankings(stage_results: List[StageResult]) -> List[str]:
        """
        Produce a single ranked list of submission IDs from a list of sequential stages.
        Contestants eliminated in later stages rank higher than those eliminated earlier.
        Within the same elimination stage, the leaderboard order determines the rank.
        """
        rankings = []
        seen = set()
        
        # Traverse stages backwards (final -> semifinal -> qualification)
        # The top contestants of the final are the top overall.
        for stage in reversed(stage_results):
            snapshot = stage.leaderboard_snapshot
            for entry in snapshot.entries:
                # In final stage, we include both advanced and eliminated
                # In prior stages, we only append them if they haven't been ranked yet (i.e., eliminated in this stage)
                if entry.contestant_id not in seen:
                    rankings.append(entry.contestant_id)
                    seen.add(entry.contestant_id)
                    
        return rankings
