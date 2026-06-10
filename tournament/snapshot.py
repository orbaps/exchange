import time
from dataclasses import dataclass, field
from typing import List

from leaderboard.models import LeaderboardSnapshot

@dataclass
class TournamentSnapshot:
    """Immutable state capture of a tournament at a specific point in time."""
    timestamp: int
    tournament_id: str
    stage_id: str
    leaderboard: LeaderboardSnapshot
    qualified: List[str] = field(default_factory=list)
    eliminated: List[str] = field(default_factory=list)
