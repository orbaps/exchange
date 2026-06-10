import os
import json
import logging
from typing import Optional, List, Dict, Any

from dashboard.services.state_cache import StateCache
from dashboard.models.schemas import (
    TournamentResponse,
    TournamentStageResponse,
    LeaderboardSnapshotResponse,
    LeaderboardEntryResponse,
    DeploymentRecordResponse
)
from tournament.journal import TournamentJournal
from tournament.replay import TournamentReplay

logger = logging.getLogger(__name__)

class DashboardAggregator:
    """Aggregates and rebuilds dashboard state from journal files."""
    
    def __init__(self, state_cache: StateCache):
        self.state_cache = state_cache

    def rebuild_from_tournament_journal(self, journal_path: str) -> bool:
        """Reads a tournament journal, verifies it, and updates the state cache."""
        if not os.path.exists(journal_path):
            logger.warning(f"Tournament journal not found at path: {journal_path}")
            return False
            
        try:
            journal = TournamentJournal(journal_path)
            entries = journal.read_all()
            if not entries:
                return False
                
            # Reconstruct tournament status, stages, and leaderboard snapshots
            tournament_id = "unknown"
            name = "Alpha Cup"
            description = "Reconstructed from journal"
            status = "DRAFT"
            created_at = int(os.path.getctime(journal_path) * 1e9)
            start_time = created_at
            end_time = None
            
            stages_map: Dict[str, Dict[str, Any]] = {}
            last_snapshot: Optional[LeaderboardSnapshotResponse] = None
            
            for entry in entries:
                event_type = entry.get("event_type")
                payload = entry.get("payload", {})
                
                if "tournament_id" in payload:
                    tournament_id = payload["tournament_id"]
                    
                if event_type == "TOURNAMENT_START":
                    status = "RUNNING"
                    start_time = payload.get("timestamp_ns", created_at)
                    
                elif event_type == "STAGE_START":
                    stage_id = payload.get("stage_id")
                    if stage_id:
                        stages_map[stage_id] = {
                            "stage_id": stage_id,
                            "stage_type": "QUALIFICATION", # fallback default
                            "campaign_id": f"camp_{stage_id}"
                        }
                        
                elif event_type == "SNAPSHOT":
                    stage_id = payload.get("stage_id")
                    raw_entries = payload.get("entries", [])
                    entries_list = []
                    for idx, e in enumerate(raw_entries):
                        entries_list.append(LeaderboardEntryResponse(
                            contestant_id=e["contestant_id"],
                            rank=e["rank"],
                            score=e["score"],
                            average_correctness=0.0,
                            average_latency=0.0,
                            average_tps=0.0,
                            success_rate=100.0,
                            campaign_id=f"camp_{stage_id}" if stage_id else "camp",
                            rating_grade="A",
                            tournament_id=tournament_id,
                            stage_id=stage_id
                        ))
                    last_snapshot = LeaderboardSnapshotResponse(
                        snapshot_id=f"snap_{stage_id}_{idx}" if stage_id else "snap",
                        campaign_id=f"camp_{stage_id}" if stage_id else "camp",
                        timestamp=str(created_at),
                        entries=entries_list,
                        tournament_id=tournament_id,
                        stage_id=stage_id,
                        entry_count=len(entries_list),
                        generated_at="Rebuilt from journal",
                        load_profile="N/A",
                        event_count=0,
                        campaign_size=len(entries_list),
                        worker_count=1,
                        execution_tps=0.0
                    )
                    
                elif event_type == "WINNER_DECLARATION":
                    status = "COMPLETED"
                    end_time = payload.get("timestamp_ns", created_at)
                    
            # Build final stages list
            stages = []
            for s_id, s_data in stages_map.items():
                stages.append(TournamentStageResponse(
                    stage_id=s_id,
                    stage_type=s_data["stage_type"],
                    campaign_id=s_data["campaign_id"]
                ))
                
            tournament_res = TournamentResponse(
                tournament_id=tournament_id,
                name=name,
                description=description,
                status=status,
                created_at=created_at,
                start_time=start_time,
                end_time=end_time,
                stages=stages
            )
            
            # Update cache
            self.state_cache.set_tournament(tournament_res)
            if last_snapshot:
                self.state_cache.set_leaderboard(last_snapshot)
                
            logger.info(f"Successfully rebuilt state for tournament {tournament_id} from journal.")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding state from tournament journal {journal_path}: {e}", exc_info=True)
            return False

    def rebuild_from_hosting_journal(self, journal_path: str) -> bool:
        """Reads a hosting lifecycle journal and updates the deployments cache."""
        if not os.path.exists(journal_path):
            logger.warning(f"Hosting journal not found at path: {journal_path}")
            return False
            
        try:
            with open(journal_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    event_type = record.get("event_type")
                    
                    # Hosting events have deployment_id, container_id, status, etc.
                    dep_id = record.get("deployment_id")
                    if dep_id:
                        # Construct a deployment record response
                        record_res = DeploymentRecordResponse(
                            deployment_id=dep_id,
                            submission_id=record.get("submission_id", ""),
                            build_id=record.get("build_id", ""),
                            container_id=record.get("container_id", ""),
                            status=record.get("status", "UNKNOWN"),
                            created_at=record.get("created_at", 0),
                            updated_at=record.get("updated_at", 0),
                            end_time=record.get("end_time"),
                            error=record.get("error")
                        )
                        self.state_cache.upsert_deployment(record_res)
            logger.info(f"Successfully rebuilt hosting state from journal.")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding state from hosting journal {journal_path}: {e}", exc_info=True)
            return False
