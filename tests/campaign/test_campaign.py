import unittest
import os
import json
import tempfile
import shutil

from campaign.campaign import BenchmarkCampaign
from campaign.config import CampaignConfig
from campaign.runner import CampaignRunner
from campaign.result import RunStatus
from campaign.report import CampaignReport
from submission.metadata import SubmissionManifest
from benchmarking.scenarios.library import get_simple_fill_scenario

class TestCampaignFramework(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # We need a proper submission path. The examples/contestant_submission works well.
        self.example_sub_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "examples", "contestant_submission"
        )
        
        # Create a broken submission that raises an exception on instantiation
        self.broken_sub_path = os.path.join(self.test_dir, "broken_sub")
        os.makedirs(self.broken_sub_path)
        with open(os.path.join(self.broken_sub_path, "metadata.json"), "w") as f:
            json.dump({"team_name": "Broken", "engine_class": "BrokenEngine", "version": "1"}, f)
        with open(os.path.join(self.broken_sub_path, "engine.py"), "w") as f:
            f.write("class BrokenEngine:\n    def __init__(self):\n        raise RuntimeError('Fail')\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_campaign_creation_and_execution(self):
        manifest1 = SubmissionManifest(
            submission_id="sub-1",
            team_name="Team A",
            version="1.0",
            engine_class="ContestantMatchingEngine",
            submission_path=self.example_sub_path,
            loaded_at=0.0
        )
        manifest2 = SubmissionManifest(
            submission_id="sub-2",
            team_name="Team A",
            version="1.0",
            engine_class="ContestantMatchingEngine",
            submission_path=self.example_sub_path,
            loaded_at=0.0
        )
        
        scenarios = [get_simple_fill_scenario(), get_simple_fill_scenario()]
        scenarios[0].scenario_id = "scen-1"
        scenarios[1].scenario_id = "scen-2"
        
        campaign = BenchmarkCampaign(
            campaign_id="test-camp",
            name="Test",
            description="Test",
            scenarios=scenarios,
            contestants=[manifest1, manifest2]
        )
        
        runner = CampaignRunner()
        result = runner.run(campaign)
        
        self.assertEqual(result.total_runs, 4) # 2 scenarios * 2 contestants
        self.assertEqual(result.successful_runs, 4)
        self.assertEqual(result.failed_runs, 0)
        
        self.assertIn("sub-1", result.results)
        
        report = CampaignReport.generate_markdown(result)
        self.assertIn("Total Runs**: 4", report)

    def test_failure_isolation(self):
        # Good contestant
        manifest_good = SubmissionManifest(
            submission_id="good-sub",
            team_name="Team A",
            version="1.0",
            engine_class="ContestantMatchingEngine",
            submission_path=self.example_sub_path,
            loaded_at=0.0
        )
        # Broken contestant
        manifest_broken = SubmissionManifest(
            submission_id="broken-sub",
            team_name="Team B",
            version="1.0",
            engine_class="BrokenEngine",
            submission_path=self.broken_sub_path,
            loaded_at=0.0
        )
        
        campaign = BenchmarkCampaign(
            campaign_id="fail-camp",
            name="Fail",
            description="Fail",
            scenarios=[get_simple_fill_scenario()],
            contestants=[manifest_good, manifest_broken]
        )
        
        config = CampaignConfig(stop_on_failure=False, record_failures=True)
        runner = CampaignRunner(config)
        
        result = runner.run(campaign)
        
        # 2 total runs, 1 success, 1 failure (the broken one)
        self.assertEqual(result.total_runs, 2)
        self.assertEqual(result.successful_runs, 1)
        self.assertEqual(result.failed_runs, 1)
        
        broken_res = result.results["broken-sub"]
        self.assertEqual(broken_res.failed_runs, 1)
        self.assertEqual(broken_res.scenario_results[0].status, RunStatus.FAILURE)
        self.assertIn("Fail", broken_res.scenario_results[0].error)

if __name__ == '__main__':
    unittest.main()
