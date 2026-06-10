from dataclasses import dataclass, field
from typing import List, Dict, Any
from tournament.journal import TournamentJournal

@dataclass
class TimelineEvent:
    event_type: str
    payload: Dict[str, Any]

@dataclass
class TournamentTimeline:
    tournament_id: str
    events: List[TimelineEvent] = field(default_factory=list)

class TournamentReplay:
    """Reconstructs the timeline of a tournament from its journal."""
    
    @staticmethod
    def load_timeline(journal: TournamentJournal) -> TournamentTimeline:
        entries = journal.read_all()
        if not entries:
            return TournamentTimeline(tournament_id="unknown")
            
        # Find the tournament ID from the first event (usually TOURNAMENT_START)
        tournament_id = "unknown"
        for entry in entries:
            if "tournament_id" in entry["payload"]:
                tournament_id = entry["payload"]["tournament_id"]
                break
                
        timeline = TournamentTimeline(tournament_id=tournament_id)
        for entry in entries:
            timeline.events.append(TimelineEvent(
                event_type=entry["event_type"],
                payload=entry["payload"]
            ))
            
        return timeline
