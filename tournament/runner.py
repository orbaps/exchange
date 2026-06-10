import time
from typing import List, Optional, Tuple

from tournament.models import Tournament, TournamentStatus, StageResult, TournamentResult
from tournament.journal import TournamentJournal
from tournament.ranking import TournamentRanking
from tournament.version_freeze import VersionFreeze
from tournament.snapshot import TournamentSnapshot
from tournament.stages import TournamentStage
from hosting.manifest import SubmissionManifest

from campaign.runner import CampaignRunner
from leaderboard.ranking import RankingEngine
from leaderboard.models import LeaderboardSnapshot
from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEventType, AnalyticsEvent

class TournamentRunner:
    def __init__(
        self,
        journal: TournamentJournal,
        version_freeze: VersionFreeze,
        campaign_runner: CampaignRunner,
        analytics_bus: AnalyticsEventBus
    ):
        self.journal = journal
        self.version_freeze = version_freeze
        self.campaign_runner = campaign_runner
        self.analytics_bus = analytics_bus
        
    def _publish_event(self, event_type: AnalyticsEventType, payload: dict):
        event = AnalyticsEvent(
            event_id=f"evt_{time.time_ns()}",
            timestamp_ns=time.time_ns(),
            event_type=event_type,
            source="TournamentRunner",
            payload=payload
        )
        self.analytics_bus.publish(event)
        
    def run(self, tournament: Tournament, initial_manifests: List[SubmissionManifest]) -> TournamentResult:
        # 1. Freeze versions and lock submission
        self.version_freeze.freeze(tournament.tournament_id, initial_manifests)
        frozen_manifests = self.version_freeze.get_frozen_manifests(
            tournament.tournament_id, 
            [m.submission_id for m in initial_manifests]
        )
        tournament.status = TournamentStatus.LOCKED
        
        # 2. Start
        tournament.status = TournamentStatus.RUNNING
        active_pool = [m.submission_id for m in frozen_manifests]
        self.journal.record_tournament_start(tournament.tournament_id, active_pool)
        self._publish_event(AnalyticsEventType.TOURNAMENT_STARTED, {
            "tournament_id": tournament.tournament_id,
            "contestants_count": len(active_pool)
        })
        
        stage_results = []
        snapshots = []
        
        # 3. Stages
        for stage in tournament.stages:
            result, snapshot = self._run_stage(tournament.tournament_id, stage, frozen_manifests, active_pool)
            stage_results.append(result)
            snapshots.append(snapshot)
            
            if result.winner:
                active_pool = [result.winner]
            else:
                active_pool = result.contestants_advanced
                
            if not active_pool:
                break
                
        # 4. Final Rankings & Winner
        final_rankings = TournamentRanking.generate_final_rankings(stage_results)
        winner = final_rankings[0] if final_rankings else None
        
        if winner:
            self.journal.record_winner_declaration(tournament.tournament_id, winner)
            self._publish_event(AnalyticsEventType.WINNER_DECLARED, {
                "tournament_id": tournament.tournament_id,
                "winner": winner
            })
            
        tournament.status = TournamentStatus.COMPLETED
        
        return TournamentResult(
            tournament_id=tournament.tournament_id,
            winner=winner,
            final_rankings=final_rankings,
            stage_results=stage_results,
            total_stages=len(tournament.stages)
        )
        
    def _run_stage(
        self, 
        tournament_id: str, 
        stage: TournamentStage, 
        frozen_manifests: List[SubmissionManifest],
        active_pool: List[str]
    ) -> Tuple[StageResult, LeaderboardSnapshot]:
        self.journal.record_stage_start(tournament_id, stage.stage_id, active_pool)
        self._publish_event(AnalyticsEventType.STAGE_STARTED, {
            "tournament_id": tournament_id,
            "stage_id": stage.stage_id,
            "active_pool": active_pool
        })
        
        # Reconstruct campaign.contestants using only the active frozen manifests
        active_manifests = [m for m in frozen_manifests if m.submission_id in active_pool]
        stage.campaign.contestants = active_manifests
        
        # Execute Campaign
        try:
            campaign_result = self.campaign_runner.run(stage.campaign)
        except Exception as e:
            # Stage failure
            stage_result = StageResult(
                stage_id=stage.stage_id,
                stage_type=stage.stage_type.value,
                contestants_started=list(active_pool),
                contestants_advanced=[],
                contestants_eliminated=list(active_pool),
                leaderboard_snapshot=LeaderboardSnapshot("", stage.campaign.campaign_id, time.time_ns()),
                winner=None
            )
            return stage_result, stage_result.leaderboard_snapshot
            
        # Leaderboard Snapshot
        snapshot = RankingEngine.calculate(campaign_result)
        snapshot.tournament_id = tournament_id
        snapshot.stage_id = stage.stage_id
        
        # Propagate tournament_id to entries for clean tracking
        for entry in snapshot.entries:
            entry.tournament_id = tournament_id
            entry.stage_id = stage.stage_id
            
        # Record Snapshot into Journal (Nice Enhancement #2)
        self.journal.record_snapshot(tournament_id, stage.stage_id, snapshot)
            
        # Apply Advancement
        advanced = stage.advancement_rule.advance(snapshot, active_pool)
        eliminated = [sid for sid in active_pool if sid not in advanced]
        
        self.journal.record_advancement(tournament_id, stage.stage_id, advanced)
        self.journal.record_elimination(tournament_id, stage.stage_id, eliminated)
        
        self._publish_event(AnalyticsEventType.ADVANCEMENT, {
            "tournament_id": tournament_id,
            "stage_id": stage.stage_id,
            "advanced": advanced
        })
        if eliminated:
            self._publish_event(AnalyticsEventType.ELIMINATION, {
                "tournament_id": tournament_id,
                "stage_id": stage.stage_id,
                "eliminated": eliminated
            })
        
        winner = None
        if stage.stage_type.value == "FINAL" and len(advanced) > 0:
            winner = advanced[0]
            advanced = [winner] # Leave winner in advanced list for analytics
            
        stage_result = StageResult(
            stage_id=stage.stage_id,
            stage_type=stage.stage_type.value,
            contestants_started=list(active_pool),
            contestants_advanced=advanced,
            contestants_eliminated=eliminated,
            leaderboard_snapshot=snapshot,
            winner=winner
        )
        
        self.journal.record_stage_end(tournament_id, stage.stage_id, [e.contestant_id for e in snapshot.entries])
        self._publish_event(AnalyticsEventType.STAGE_COMPLETED, {
            "tournament_id": tournament_id,
            "stage_id": stage.stage_id
        })
        
        return stage_result, snapshot
