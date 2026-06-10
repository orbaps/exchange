from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from leaderboard.rating import RatingGrade

@dataclass
class LeaderboardEntry:
    """A single row representing a contestant's ranking in a snapshot."""
    contestant_id: str
    rank: int
    score: float
    average_correctness: float
    average_latency: float
    average_tps: float
    success_rate: float
    campaign_id: str
    
    rating_grade: RatingGrade
    previous_rank: Optional[int] = None
    tournament_id: Optional[str] = None
    stage_id: Optional[str] = None
    evaluation_score: Optional[float] = 0.0
    skill_grade: Optional[str] = "D"
    benchmark_count: Optional[int] = 0

@dataclass
class LeaderboardSnapshot:
    """An immutable snapshot of the leaderboard at a specific point in time."""
    snapshot_id: str
    campaign_id: str
    timestamp: datetime
    entries: List[LeaderboardEntry] = field(default_factory=list)
    tournament_id: Optional[str] = None
    stage_id: Optional[str] = None
    entry_count: int = 0
    generated_at: str = ""
    load_profile: str = "N/A"
    event_count: int = 0
    campaign_size: int = 0
    worker_count: int = 0
    execution_tps: float = 0.0
