from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from leaderboard.models import LeaderboardSnapshot
from tournament.stages import TournamentStage

class TournamentStatus(Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    LOCKED = "LOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ContestantStatus(Enum):
    ACTIVE = "ACTIVE"
    ADVANCED = "ADVANCED"
    ELIMINATED = "ELIMINATED"
    WINNER = "WINNER"

@dataclass
class StageResult:
    stage_id: str
    stage_type: str
    contestants_started: List[str]
    contestants_advanced: List[str]
    contestants_eliminated: List[str]
    leaderboard_snapshot: LeaderboardSnapshot
    winner: Optional[str] = None

@dataclass
class Tournament:
    tournament_id: str
    name: str
    description: str
    status: TournamentStatus
    created_at: int
    start_time: int
    end_time: Optional[int] = None
    stages: List[TournamentStage] = field(default_factory=list)

@dataclass
class TournamentResult:
    tournament_id: str
    winner: Optional[str]
    final_rankings: List[str]
    stage_results: List[StageResult] = field(default_factory=list)
    total_stages: int = 0
