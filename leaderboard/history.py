from typing import List, Optional
from leaderboard.models import LeaderboardSnapshot

class RankingHistory:
    """Stores historical ranking snapshots."""
    
    def __init__(self):
        self._snapshots: List[LeaderboardSnapshot] = []
        
    def add_snapshot(self, snapshot: LeaderboardSnapshot) -> None:
        """Adds a new snapshot to the history."""
        self._snapshots.append(snapshot)
        
    def latest(self) -> Optional[LeaderboardSnapshot]:
        """Returns the most recent snapshot."""
        if not self._snapshots:
            return None
        return self._snapshots[-1]
        
    def get_snapshot(self, snapshot_id: str) -> Optional[LeaderboardSnapshot]:
        """Fetches a specific snapshot by ID."""
        for s in self._snapshots:
            if s.snapshot_id == snapshot_id:
                return s
        return None
