from datetime import datetime, timezone
import uuid
from typing import Dict

from campaign.result import CampaignResult, ContestantCampaignResult
from leaderboard.models import LeaderboardEntry, LeaderboardSnapshot
from leaderboard.tiebreak import TieBreaker
from leaderboard.rating import RatingCalculator

class RankingEngine:
    """Converts CampaignResult into a ranked LeaderboardSnapshot."""
    
    @staticmethod
    def calculate(campaign_result: CampaignResult) -> LeaderboardSnapshot:
        entries = []
        
        for contestant_id, contestant_result in campaign_result.results.items():
            rating = RatingCalculator.calculate(contestant_result.average_score)
            
            entry = LeaderboardEntry(
                contestant_id=contestant_id,
                rank=0,  # Will be assigned after sorting
                score=contestant_result.average_score,
                average_correctness=contestant_result.average_correctness,
                average_latency=contestant_result.average_latency_ms,
                average_tps=contestant_result.average_tps,
                success_rate=contestant_result.success_rate,
                campaign_id=campaign_result.campaign_id,
                rating_grade=rating,
                previous_rank=None
            )
            entries.append(entry)
            
        # Sort using the deterministic TieBreaker keys
        entries.sort(key=TieBreaker.get_sort_key)
        
        # Dense deterministic ranking: 1, 2, 3, 4 without skips
        for i, entry in enumerate(entries):
            entry.rank = i + 1
            
        now = datetime.now(timezone.utc)
        
        return LeaderboardSnapshot(
            snapshot_id=str(uuid.uuid4()),
            campaign_id=campaign_result.campaign_id,
            timestamp=now,
            entries=entries,
            entry_count=len(entries),
            generated_at=now.isoformat()
        )
