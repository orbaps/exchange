from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LeaderboardEntryResponse(BaseModel):
    contestant_id: str
    rank: int
    score: float
    average_correctness: float
    average_latency: float
    average_tps: float
    success_rate: float
    campaign_id: str
    rating_grade: str
    previous_rank: Optional[int] = None
    tournament_id: Optional[str] = None
    stage_id: Optional[str] = None

class LeaderboardSnapshotResponse(BaseModel):
    snapshot_id: str
    campaign_id: str
    timestamp: str
    entries: List[LeaderboardEntryResponse]
    tournament_id: Optional[str] = None
    stage_id: Optional[str] = None
    entry_count: int
    generated_at: str
    load_profile: str
    event_count: int
    campaign_size: int
    worker_count: int
    execution_tps: float

class TournamentStageResponse(BaseModel):
    stage_id: str
    stage_type: str
    campaign_id: str

class TournamentResponse(BaseModel):
    tournament_id: str
    name: str
    description: str
    status: str
    created_at: int
    start_time: int
    end_time: Optional[int] = None
    stages: List[TournamentStageResponse]

class DeploymentRecordResponse(BaseModel):
    deployment_id: str
    submission_id: str
    build_id: str
    container_id: str
    status: str
    created_at: int
    updated_at: int
    end_time: Optional[int] = None
    error: Optional[str] = None

class DeploymentHealthResponse(BaseModel):
    submission_id: str
    container_id: str
    status: str
    uptime_ns: int
    restart_count: int
    failure_count: int
    last_heartbeat: int

class AnalyticsSummaryResponse(BaseModel):
    total_scenarios_run: int
    successful_runs: int
    failed_runs: int
    avg_correctness: float
    avg_latency_ms: float
    avg_tps: float
    overall_success_rate: float

class ReplayEventResponse(BaseModel):
    event_type: str
    payload: Dict[str, Any]

class ReplayTimelineResponse(BaseModel):
    tournament_id: str
    events: List[ReplayEventResponse]
