from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from dashboard.dependencies import get_state_cache
from dashboard.services.state_cache import StateCache
from dashboard.models.schemas import (
    LeaderboardSnapshotResponse,
    TournamentResponse,
    DeploymentRecordResponse,
    AnalyticsSummaryResponse
)

router = APIRouter(prefix="/api/public", tags=["Public Data"])

@router.get("/leaderboard", response_model=LeaderboardSnapshotResponse)
async def get_leaderboard(cache: StateCache = Depends(get_state_cache)):
    snapshot = cache.get_leaderboard()
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leaderboard snapshot available yet"
        )
    return snapshot

@router.get("/tournament", response_model=TournamentResponse)
async def get_tournament(cache: StateCache = Depends(get_state_cache)):
    tournament = cache.get_tournament()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active tournament schedule found"
        )
    return tournament

@router.get("/deployments", response_model=List[DeploymentRecordResponse])
async def get_deployments(cache: StateCache = Depends(get_state_cache)):
    return cache.get_deployments()

@router.get("/analytics", response_model=AnalyticsSummaryResponse)
async def get_analytics(cache: StateCache = Depends(get_state_cache)):
    analytics = cache.get_analytics()
    if not analytics:
        # Return default empty metrics instead of 404 to avoid frontend errors
        return AnalyticsSummaryResponse(
            total_scenarios_run=0,
            successful_runs=0,
            failed_runs=0,
            avg_correctness=0.0,
            avg_latency_ms=0.0,
            avg_tps=0.0,
            overall_success_rate=0.0
        )
    return analytics
