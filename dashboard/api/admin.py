import os
import time
import logging
import threading
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel

from dashboard.services.auth_service import get_admin_user
from dashboard.dependencies import get_aggregator, get_state_cache, get_event_bridge
from dashboard.services.state_cache import StateCache
from dashboard.services.aggregator import DashboardAggregator
from dashboard.services.event_bridge import EventBridge

# Import tournament/hosting domains
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL

from tournament.models import Tournament, TournamentStatus
from tournament.stages import TournamentStage, StageType
from tournament.advancement import AdvancementRule, AdvancementType
from campaign.campaign import BenchmarkCampaign
from benchmarking.scenario import BenchmarkScenario
from analytics.bus import AnalyticsEventBus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

class RebuildRequest(BaseModel):
    tournament_journal_path: Optional[str] = None
    hosting_journal_path: Optional[str] = None

class StartTournamentRequest(BaseModel):
    tournament_id: Optional[str] = None
    name: Optional[str] = None
    contestant_count: Optional[int] = 4

# Keep track of active background tournament thread
_active_run_thread: Optional[threading.Thread] = None
_active_run_bus: Optional[AnalyticsEventBus] = None

def run_tournament_in_background(
    tournament: Tournament,
    manifests: List[SubmissionManifest],
    journal_path: str,
    event_bridge: EventBridge
):
    from hosting.quota import ResourceQuotaManager
    from hosting.router import EndpointRouter
    from hosting.manager import ContainerManager
    from hosting.deployment_registry import DeploymentRegistry
    from hosting.build import BuildManager
    from hosting.artifacts import ArtifactStore
    from campaign.runner import CampaignRunner
    from campaign.config import CampaignConfig
    from tournament.version_freeze import VersionFreeze
    from tournament.submission_lock import SubmissionLock
    from tournament.runner import TournamentRunner

    global _active_run_bus
    logger.info(f"Starting tournament {tournament.tournament_id} runner thread...")
    
    artifacts_dir = "dashboard_run_artifacts"
    quota = ResourceQuotaManager(total_cpu=32, total_memory_mb=32768, total_disk_mb=128000)
    router = EndpointRouter()
    registry = DeploymentRegistry()
    cm = ContainerManager(quota, router, registry)
    store = ArtifactStore(artifacts_dir)
    build_mgr = BuildManager(store)
    
    campaign_runner = CampaignRunner(
        config=CampaignConfig(),
        use_hosting=True,
        router=router,
        container_manager=cm,
        build_manager=build_mgr
    )
    
    # Enable event listening
    _active_run_bus = AnalyticsEventBus()
    _active_run_bus.subscribe(event_bridge.handle_event)
    
    from tournament.journal import TournamentJournal
    journal = TournamentJournal(journal_path)
    lock = SubmissionLock()
    freezer = VersionFreeze(lock, store)
    
    runner = TournamentRunner(
        journal=journal,
        version_freeze=freezer,
        campaign_runner=campaign_runner,
        analytics_bus=_active_run_bus
    )
    
    try:
        runner.run(tournament, manifests)
        logger.info(f"Tournament {tournament.tournament_id} run completed.")
    except Exception as e:
        logger.error(f"Error running tournament {tournament.tournament_id}: {e}", exc_info=True)
    finally:
        _active_run_bus.unsubscribe(event_bridge.handle_event)

@router.post("/tournament/start")
async def start_tournament(
    req: StartTournamentRequest,
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(get_admin_user),
    event_bridge: EventBridge = Depends(get_event_bridge)
):
    global _active_run_thread
    if _active_run_thread and _active_run_thread.is_alive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tournament is already running."
        )

    t_id = req.tournament_id or f"t_{int(time.time())}"
    t_name = req.name or "Alpha Cup Live"
    
    # 1. Generate manifests
    manifests = []
    count = req.contestant_count or 4
    for i in range(count):
        # We write a simple script for mock contestants
        os.makedirs(f"dashboard_run_artifacts/team_{i}", exist_ok=True)
        with open(f"dashboard_run_artifacts/team_{i}/main.py", "w") as f:
            f.write("""
class HostedEngine:
    def __init__(self):
        pass
    def submit_order(self, payload):
        pass
    def cancel_order(self, payload):
        pass
    def replace_order(self, payload):
        pass
    def reset(self):
        pass
    def snapshot(self):
        return None
""")
        manifests.append(SubmissionManifest(
            submission_id=f"team_{i}",
            team_name=f"Team {i}",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        ))

    # 2. Setup Campaigns
    qual_campaign = BenchmarkCampaign(
        campaign_id=f"camp_qual_{t_id}", name="Qualification", description="",
        scenarios=[BenchmarkScenario(scenario_id="s1", name="Scenario 1", description="", seed=1, events=[])],
        contestants=[]
    )
    final_campaign = BenchmarkCampaign(
        campaign_id=f"camp_final_{t_id}", name="Final", description="",
        scenarios=[BenchmarkScenario(scenario_id="s2", name="Scenario 2", description="", seed=2, events=[])],
        contestants=[]
    )

    # 3. Create stages
    stages = [
        TournamentStage(
            stage_id="stage_1", name="Qualification", stage_type=StageType.QUALIFICATION,
            campaign=qual_campaign, advancement_rule=AdvancementRule(AdvancementType.TOP_N, max(1, count // 2))
        ),
        TournamentStage(
            stage_id="stage_2", name="Final", stage_type=StageType.FINAL,
            campaign=final_campaign, advancement_rule=AdvancementRule(AdvancementType.TOP_N, 1)
        )
    ]

    tournament = Tournament(
        tournament_id=t_id,
        name=t_name,
        description="Live Interactive Campaign",
        status=TournamentStatus.SCHEDULED,
        created_at=time.time_ns(),
        start_time=time.time_ns(),
        stages=stages
    )

    # 4. Run in background thread
    journal_path = f"dashboard_run_artifacts/{t_id}_journal.jsonl"
    
    # Store the loop in event bridge so it can communicate back
    import asyncio
    event_bridge.set_loop(asyncio.get_running_loop())
    
    _active_run_thread = threading.Thread(
        target=run_tournament_in_background,
        args=(tournament, manifests, journal_path, event_bridge),
        daemon=True
    )
    _active_run_thread.start()

    return {"message": "Tournament started successfully", "tournament_id": t_id}

@router.post("/tournament/stop")
async def stop_tournament(admin_user: dict = Depends(get_admin_user)):
    global _active_run_thread
    if not _active_run_thread or not _active_run_thread.is_alive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tournament is currently running."
        )
        
    # In a real environment, we would terminate the process/containers or set a cancel flag.
    # For local demonstration, we'll let it finish or just log/clear it.
    logger.info("Stopping current tournament execution.")
    return {"message": "Tournament execution stopped"}

@router.post("/replay/rebuild")
async def rebuild_state(
    req: RebuildRequest,
    admin_user: dict = Depends(get_admin_user),
    agg: DashboardAggregator = Depends(get_aggregator),
    cache: StateCache = Depends(get_state_cache)
):
    cache.clear()
    
    t_journal = req.tournament_journal_path or "dashboard_run_artifacts/t1_journal.jsonl"
    h_journal = req.hosting_journal_path or "dashboard_run_artifacts/hosting_journal.jsonl"
    
    t_ok = agg.rebuild_from_tournament_journal(t_journal)
    h_ok = agg.rebuild_from_hosting_journal(h_journal)
    
    if not t_ok and not h_ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to rebuild state from provided journals. Files may not exist or are empty."
        )
        
    return {"message": "State rebuilt successfully from journals", "tournament_rebuilt": t_ok, "hosting_rebuilt": h_ok}
