import os
import time

from campaign.campaign import BenchmarkCampaign
from submission.metadata import SubmissionManifest
from benchmarking.scenarios.library import get_simple_fill_scenario, get_cancel_scenario

def create_small_campaign() -> BenchmarkCampaign:
    # Use the example submission from Phase 3.1
    example_sub_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples", "contestant_submission")
    
    # Contestant 1: The Phase 3.1 mock
    contestant_1 = SubmissionManifest(
        submission_id="sub-001",
        team_name="Example Team 1",
        version="1.0",
        engine_class="ContestantMatchingEngine",
        submission_path=example_sub_path,
        loaded_at=time.time()
    )
    
    # Contestant 2: Same codebase, but maybe a different team ID for testing aggregation
    contestant_2 = SubmissionManifest(
        submission_id="sub-002",
        team_name="Example Team 2",
        version="1.0",
        engine_class="ContestantMatchingEngine",
        submission_path=example_sub_path,
        loaded_at=time.time()
    )
    
    scenarios = [
        get_simple_fill_scenario(),
        get_cancel_scenario(),
        get_simple_fill_scenario(), # Just duplicating to reach 5
        get_cancel_scenario(),
        get_simple_fill_scenario()
    ]
    
    # We rename IDs slightly so they are unique
    for i, s in enumerate(scenarios):
        s.scenario_id = f"scenario-{i+1}"
    
    return BenchmarkCampaign(
        campaign_id="camp-small-01",
        name="Small Test Campaign",
        description="A 5x2 campaign.",
        scenarios=scenarios,
        contestants=[contestant_1, contestant_2]
    )

if __name__ == '__main__':
    from campaign.runner import CampaignRunner
    from campaign.report import CampaignReport
    
    campaign = create_small_campaign()
    runner = CampaignRunner()
    result = runner.run(campaign)
    
    report_md = CampaignReport.generate_markdown(result)
    print(report_md)
