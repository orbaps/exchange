import logging
import traceback
from typing import Dict
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
    """Executes a benchmark campaign strictly sequentially, isolating failures."""
    
    def __init__(self, config: Optional[CampaignConfig] = None, use_sandbox: bool = False, sandbox_config: Optional[SandboxConfig] = None):
        self.config = config or CampaignConfig()
        self.use_sandbox = use_sandbox
        self.sandbox_config = sandbox_config or SandboxConfig()
        self.benchmark_runner = BenchmarkRunner()
        
    def run(self, campaign: BenchmarkCampaign) -> CampaignResult:
        campaign_result = CampaignResult(campaign_id=campaign.campaign_id)
        
        for manifest in campaign.contestants:
            # We don't have the full SubmissionMetadata inside the manifest directly in the same class,
            # but we can reconstruct it, or assume SubmissionLoader takes a path and team/class names.
            # Let's build a compatible SubmissionMetadata object for the loader.
            metadata = SubmissionMetadata(
                team_name=manifest.team_name,
                engine_class=manifest.engine_class,
                version=manifest.version
            )
            
            contestant_result = ContestantCampaignResult(contestant_id=manifest.submission_id)
            
            # TODO(Phase 3.3): Load engine per scenario (load -> run -> destroy) for sandboxing
            if self.use_sandbox:
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
                    contestant_result.scenario_results.append(
                        CampaignRunResult(
                            contestant_id=manifest.submission_id,
                            scenario_id=scenario.scenario_id,
                            status=RunStatus.SUCCESS,
                            benchmark_result=bench_result
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
                        
            # Calculate metrics
            from campaign.metrics import CampaignMetrics
            metrics = CampaignMetrics.calculate(contestant_result.scenario_results)
            contestant_result.average_correctness = metrics["average_correctness"]
            contestant_result.maximum_correctness = metrics["maximum_correctness"]
            contestant_result.minimum_correctness = metrics["minimum_correctness"]
            contestant_result.average_execution_time = metrics["average_execution_time"]
            
            campaign_result.results[manifest.submission_id] = contestant_result
            
            if self.config.max_failures is not None and campaign_result.failed_runs >= self.config.max_failures:
                break
                
        return campaign_result
