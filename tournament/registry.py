from typing import Dict, List, Optional
from tournament.models import Tournament

class TournamentRegistry:
    """In-memory store for Tournaments."""
    def __init__(self):
        self._tournaments: Dict[str, Tournament] = {}
        
    def create(self, tournament: Tournament) -> None:
        if tournament.tournament_id in self._tournaments:
            raise ValueError(f"Tournament {tournament.tournament_id} already exists")
        self._tournaments[tournament.tournament_id] = tournament
        
    def get(self, tournament_id: str) -> Optional[Tournament]:
        return self._tournaments.get(tournament_id)
        
    def list(self) -> List[Tournament]:
        return list(self._tournaments.values())
        
    def delete(self, tournament_id: str) -> None:
        if tournament_id in self._tournaments:
            del self._tournaments[tournament_id]
            
    def update(self, tournament: Tournament) -> None:
        if tournament.tournament_id not in self._tournaments:
            raise ValueError(f"Tournament {tournament.tournament_id} not found")
        self._tournaments[tournament.tournament_id] = tournament
        
    def latest(self) -> Optional[Tournament]:
        if not self._tournaments:
            return None
        return max(self._tournaments.values(), key=lambda t: t.created_at)
