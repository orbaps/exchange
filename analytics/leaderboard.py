import time
from typing import List, Dict, Optional
from leaderboard.models import LeaderboardSnapshot
from analytics.delta import RankDelta
from analytics.events import AnalyticsEvent, AnalyticsEventType
from analytics.bus import AnalyticsEventBus

class LiveLeaderboard:
    """Detects leaderboard modifications natively and emits LeaderboardChangeEvent payloads."""
    
    def __init__(self, bus: AnalyticsEventBus):
        self.bus = bus
        self.current_rankings: Dict[str, int] = {}
        
    def process_snapshot(self, snapshot: LeaderboardSnapshot):
        timestamp_ns = time.time_ns()
        deltas: List[RankDelta] = []
        
        for rank_idx, entry in enumerate(snapshot.entries):
            new_rank = rank_idx + 1 # 1-based index
            contestant_id = entry.contestant_id
            
            old_rank = self.current_rankings.get(contestant_id)
            if old_rank is not None and old_rank != new_rank:
                delta = old_rank - new_rank # e.g. 5 -> 2 gives +3
                deltas.append(RankDelta(contestant_id, old_rank, new_rank, delta))
                
            self.current_rankings[contestant_id] = new_rank
            
        if deltas:
            event = AnalyticsEvent(
                event_id=f"ldr_{timestamp_ns}",
                timestamp_ns=timestamp_ns,
                event_type=AnalyticsEventType.LEADERBOARD_UPDATE,
                source="LiveLeaderboard",
                payload={"snapshot_id": snapshot.snapshot_id, "deltas": [vars(d) for d in deltas]}
            )
            self.bus.publish(event)
