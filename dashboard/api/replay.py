import os
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from dashboard.models.schemas import ReplayTimelineResponse, ReplayEventResponse
from tournament.journal import TournamentJournal
from tournament.replay import TournamentReplay

router = APIRouter(prefix="/api/public/replay", tags=["Replay Viewer"])

def get_journal_path(tournament_id: str) -> str:
    # Resolve the journal path under dashboard_run_artifacts
    # Or fallback to test_tournament_artifacts if needed
    path = f"dashboard_run_artifacts/{tournament_id}_journal.jsonl"
    if not os.path.exists(path):
        path = f"test_tournament_artifacts/{tournament_id}_journal.jsonl"
    if not os.path.exists(path):
        # Scan current workspace directories for any journal file matching this ID
        for root, dirs, files in os.walk("."):
            for f in files:
                if f == f"{tournament_id}_journal.jsonl" or f == "journal.jsonl" and tournament_id in root:
                    return os.path.join(root, f)
    return path

@router.get("/{tournament_id}", response_model=ReplayTimelineResponse)
async def get_replay_timeline(tournament_id: str):
    path = get_journal_path(tournament_id)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay journal for tournament {tournament_id} not found."
        )
        
    try:
        journal = TournamentJournal(path)
        timeline = TournamentReplay.load_timeline(journal)
        
        events_res = [
            ReplayEventResponse(event_type=e.event_type, payload=e.payload)
            for e in timeline.events
        ]
        
        return ReplayTimelineResponse(
            tournament_id=timeline.tournament_id,
            events=events_res
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading replay timeline: {str(e)}"
        )

@router.get("/{tournament_id}/snapshot/{index}")
async def get_replay_snapshot(tournament_id: str, index: int):
    path = get_journal_path(tournament_id)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay journal for tournament {tournament_id} not found."
        )
        
    try:
        journal = TournamentJournal(path)
        timeline = TournamentReplay.load_timeline(journal)
        
        if index < 0 or index >= len(timeline.events):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event index {index}. Timeline has {len(timeline.events)} events."
            )
            
        # Reconstruct the state up to 'index'
        reconstructed_state = {
            "tournament_id": tournament_id,
            "status": "DRAFT",
            "active_pool": [],
            "eliminated": [],
            "advanced": [],
            "stages": {},
            "current_stage_id": None,
            "leaderboard": None,
            "winner": None
        }
        
        for i in range(index + 1):
            event = timeline.events[i]
            payload = event.payload
            e_type = event.event_type
            
            if e_type == "TOURNAMENT_START":
                reconstructed_state["status"] = "RUNNING"
                reconstructed_state["active_pool"] = payload.get("locked_contestants", [])
                
            elif e_type == "STAGE_START":
                stage_id = payload.get("stage_id")
                reconstructed_state["current_stage_id"] = stage_id
                reconstructed_state["stages"][stage_id] = {
                    "stage_id": stage_id,
                    "status": "RUNNING",
                    "contestants": payload.get("contestants", []),
                    "advanced": [],
                    "eliminated": [],
                    "leaderboard": None
                }
                
            elif e_type == "SNAPSHOT":
                stage_id = payload.get("stage_id")
                entries = payload.get("entries", [])
                if stage_id in reconstructed_state["stages"]:
                    reconstructed_state["stages"][stage_id]["leaderboard"] = entries
                reconstructed_state["leaderboard"] = entries
                
            elif e_type == "ADVANCEMENT":
                stage_id = payload.get("stage_id")
                advanced = payload.get("advanced", [])
                if stage_id in reconstructed_state["stages"]:
                    reconstructed_state["stages"][stage_id]["advanced"] = advanced
                reconstructed_state["advanced"] = advanced
                
            elif e_type == "ELIMINATION":
                stage_id = payload.get("stage_id")
                eliminated = payload.get("eliminated", [])
                if stage_id in reconstructed_state["stages"]:
                    reconstructed_state["stages"][stage_id]["eliminated"] = eliminated
                reconstructed_state["eliminated"].extend(eliminated)
                # Remove from active pool
                active = reconstructed_state["active_pool"]
                reconstructed_state["active_pool"] = [c for c in active if c not in eliminated]
                
            elif e_type == "STAGE_END":
                stage_id = payload.get("stage_id")
                if stage_id in reconstructed_state["stages"]:
                    reconstructed_state["stages"][stage_id]["status"] = "COMPLETED"
                    
            elif e_type == "WINNER_DECLARATION":
                reconstructed_state["status"] = "COMPLETED"
                reconstructed_state["winner"] = payload.get("winner")
                reconstructed_state["active_pool"] = [payload.get("winner")]
                
        return reconstructed_state
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reconstructing replay state: {str(e)}"
        )
