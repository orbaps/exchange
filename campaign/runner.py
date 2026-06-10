import logging
import traceback
import uuid
from typing import Dict, Optional

from campaign.config import CampaignConfig
from campaign.campaign import BenchmarkCampaign
from campaign.result import CampaignResult, ContestantCampaignResult, CampaignRunResult, RunStatus

from benchmarking.runner import BenchmarkRunner
from campaign.metrics import CampaignMetrics
from benchmarking.factory import EngineFactory
from submission.loader import SubmissionLoader
from submission.wrapper import ContestantSubmissionAdapter
from submission.metadata import SubmissionMetadata

from sandbox.adapter import SandboxedContestantAdapter
from sandbox.config import SandboxConfig

logger = logging.getLogger(__name__)


class CampaignRunner:
    """Executes a benchmark campaign strictly sequentially, isolating failures.

    Execution modes (mutually exclusive, in priority order):
        1. use_hosting=True  → Build → Deploy → HostedExecutionSession → Destroy
        2. use_sandbox=True  → SandboxedContestantAdapter (Phase 3.x path)
        3. default           → Direct SubmissionLoader path (legacy)
    """

    def __init__(
        self,
        config:           Optional[CampaignConfig] = None,
        use_sandbox:      bool = False,
        sandbox_config:   Optional[SandboxConfig]  = None,
        # ── Hosting layer (Phase 4.4.1+) ────────────────────────────────────
        use_hosting:      bool = False,
        router=None,            # hosting.router.EndpointRouter | None
        container_manager=None, # hosting.manager.ContainerManager | None
        build_manager=None,     # hosting.build.BuildManager | None
    ):
        self.config            = config or CampaignConfig()
        self.use_sandbox       = use_sandbox
        self.sandbox_config    = sandbox_config or SandboxConfig()
        self.use_hosting       = use_hosting
        self._router           = router
        self._container_manager = container_manager
        self._build_manager    = build_manager
        self.benchmark_runner  = BenchmarkRunner()
        
    def run(self, campaign: BenchmarkCampaign) -> CampaignResult:
        campaign_result = CampaignResult(campaign_id=campaign.campaign_id)
        
        for manifest in campaign.contestants:
            # We don't have the full SubmissionMetadata inside the manifest directly in the same class,
            # but we can reconstruct it, or assume SubmissionLoader takes a path and team/class names.
            # Let's build a compatible SubmissionMetadata object for the loader.
            metadata = SubmissionMetadata(
                team_name=manifest.team_name,
                engine_class=getattr(manifest, "engine_class", "HostedEngine"),
                version=manifest.version
            )
            
            contestant_result = ContestantCampaignResult(contestant_id=manifest.submission_id)
            
            # ── Hosting path (Phase 4.4.1+) ──────────────────────────────────
            if self.use_hosting and self._router and self._container_manager:
                from execution.hosted_session import HostedExecutionSession
                from hosting.manifest import SubmissionManifest as HostingManifest
                from hosting.runtime import RuntimeType
                from hosting.resources import MEDIUM

                # Build the submission if a build_manager is provided
                build_id = ""
                if self._build_manager:
                    h_manifest = HostingManifest(
                        submission_id=manifest.submission_id,
                        team_name=manifest.team_name,
                        version=manifest.version,
                        language=RuntimeType.PYTHON,
                        entrypoint=getattr(manifest, "entrypoint", "main.py"),
                        build_command=getattr(manifest, "build_command", "echo skip"),
                        run_command=getattr(manifest, "run_command", "python main.py"),
                        resource_profile=MEDIUM,
                    )
                    build_result = self._build_manager.build(h_manifest)
                    build_id = build_result.build_id
                    if build_result.status.value != "SUCCESS":
                        logger.error(f"Build failed for {manifest.submission_id}: {build_result.error}")
                        for scenario in campaign.scenarios:
                            campaign_result.total_runs += 1
                            campaign_result.failed_runs += 1
                            contestant_result.failed_runs += 1
                        campaign_result.results[manifest.submission_id] = contestant_result
                        continue

                # Deploy container
                h_manifest = HostingManifest(
                    submission_id=manifest.submission_id,
                    team_name=manifest.team_name,
                    version=manifest.version,
                    language=RuntimeType.PYTHON,
                    entrypoint=getattr(manifest, "entrypoint", "main.py"),
                    build_command=getattr(manifest, "build_command", "echo skip"),
                    run_command=getattr(manifest, "run_command", "python main.py"),
                    resource_profile=MEDIUM,
                )
                container = self._container_manager.deploy(h_manifest, build_id=build_id)

                session = HostedExecutionSession(
                    session_id=f"sess_{uuid.uuid4().hex[:8]}",
                    submission_id=manifest.submission_id,
                    router=self._router,
                    container_manager=self._container_manager,
                )
                session.start()
                adapter = session   # duck-typed: has reset(), execute()

            # ── Sandbox path ──────────────────────────────────────────────────
            elif self.use_sandbox:
                # adapter will spawn the subprocess on snapshot()
                adapter = SandboxedContestantAdapter(manifest, self.sandbox_config)
            else:
                # Current behavior (load once per contestant)
                load_result = SubmissionLoader.load(manifest.submission_path, metadata)
                
                if not load_result.success:
                    logger.error(f"Failed to load contestant {manifest.submission_id}: {load_result.errors}")
                    for scenario in campaign.scenarios:
                        campaign_result.total_runs += 1
                        campaign_result.failed_runs += 1
                        contestant_result.failed_runs += 1
                        
                        if self.config.record_failures:
                            contestant_result.scenario_results.append(
                                CampaignRunResult(
                                    contestant_id=manifest.submission_id,
                                    scenario_id=scenario.scenario_id,
                                    status=RunStatus.FAILURE,
                                    error=f"Load failure: {load_result.errors}"
                                )
                            )
                    campaign_result.results[manifest.submission_id] = contestant_result
                    continue
                    
                raw_engine = load_result.engine
                adapter = ContestantSubmissionAdapter(raw_engine)
            
            for scenario in campaign.scenarios:
                campaign_result.total_runs += 1
                
                try:
                    # Reset the contestant engine for the new scenario
                    adapter.reset()
                    
                    # Create a fresh reference engine
                    ref_engine = EngineFactory.create_reference()
                    
                    # Run the benchmark
                    bench_result = self.benchmark_runner.run(scenario, ref_engine, adapter)
                    
                    # Record success
                    campaign_result.successful_runs += 1
                    from telemetry.failures import FailureStatistics
                    from scoring.calculator import ScoreCalculator
                    
                    run_failures = FailureStatistics(1, 0, 0, 0, 100.0, 0.0)
                    score_res = ScoreCalculator.calculate(
                        manifest.submission_id,
                        scenario.scenario_id,
                        bench_result,
                        run_failures
                    )
                    
                    contestant_result.scenario_results.append(
                        CampaignRunResult(
                            contestant_id=manifest.submission_id,
                            scenario_id=scenario.scenario_id,
                            status=RunStatus.SUCCESS,
                            benchmark_result=bench_result,
                            score_result=score_res
                        )
                    )
                    
                except Exception as e:
                    # Failure Isolation
                    logger.error(f"Contestant {manifest.submission_id} failed on scenario {scenario.scenario_id}: {e}")
                    campaign_result.failed_runs += 1
                    contestant_result.failed_runs += 1
                    
                    if self.config.record_failures:
                        contestant_result.scenario_results.append(
                            CampaignRunResult(
                                contestant_id=manifest.submission_id,
                                scenario_id=scenario.scenario_id,
                                status=RunStatus.FAILURE,
                                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                            )
                        )
                    
                    if self.config.stop_on_failure:
                        raise RuntimeError(f"Campaign stopped due to failure in {manifest.submission_id}") from e
                        
                    if self.config.max_failures is not None and campaign_result.failed_runs >= self.config.max_failures:
                        logger.warning(f"Campaign reached max failures ({self.config.max_failures}). Halting.")
                        break
                        
            # ── Teardown hosted container (if deployed) ───────────────────────
            if self.use_hosting and self._container_manager and "container" in dir():
                try:
                    self._container_manager.destroy(container.container_id)
                except Exception as teardown_err:
                    logger.warning(f"Container teardown error for {manifest.submission_id}: {teardown_err}")

            # Calculate metrics
            from campaign.metrics import CampaignMetrics
            metrics = CampaignMetrics.calculate(contestant_result.scenario_results)
            contestant_result.average_correctness = metrics["average_correctness"]
            contestant_result.maximum_correctness = metrics["maximum_correctness"]
            contestant_result.minimum_correctness = metrics["minimum_correctness"]
            contestant_result.average_execution_time = metrics["average_execution_time"]
            
            contestant_result.average_latency_ms = metrics["average_latency_ms"]
            contestant_result.best_latency_ms = metrics["best_latency_ms"]
            contestant_result.worst_latency_ms = metrics["worst_latency_ms"]
            contestant_result.average_tps = metrics["average_tps"]
            contestant_result.best_tps = metrics["best_tps"]
            contestant_result.worst_tps = metrics["worst_tps"]
            contestant_result.success_rate = metrics["success_rate"]
            
            contestant_result.average_score = metrics["average_score"]
            contestant_result.best_score = metrics["best_score"]
            contestant_result.worst_score = metrics["worst_score"]
            contestant_result.score_stddev = metrics["score_stddev"]
            
            campaign_result.results[manifest.submission_id] = contestant_result
            
            if self.config.max_failures is not None and campaign_result.failed_runs >= self.config.max_failures:
                break
                
        return campaign_result
