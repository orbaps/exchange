import os
import shutil
import unittest

from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.deployment_registry import DeploymentRegistry
from hosting.build import BuildManager
from hosting.artifacts import ArtifactStore

from campaign.runner import CampaignRunner
from campaign.config import CampaignConfig
from campaign.campaign import BenchmarkCampaign
from benchmarking.scenario import BenchmarkScenario

from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL


class TestEndToEndPlatformIntegration(unittest.TestCase):

    def setUp(self):
        self.artifacts_dir = "test_e2e_artifacts"
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)

    def tearDown(self):
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)

    def test_full_campaign_execution_with_hosting(self):
        # 1. Platform Setup
        quota = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        registry = DeploymentRegistry()
        cm = ContainerManager(quota, router, registry)
        
        store = ArtifactStore(self.artifacts_dir)
        build_mgr = BuildManager(store)

        runner = CampaignRunner(
            config=CampaignConfig(),
            use_hosting=True,
            router=router,
            container_manager=cm,
            build_manager=build_mgr
        )

        # 2. Submission Manifest
        manifest = SubmissionManifest(
            submission_id="sub_e2e",
            team_name="E2ETeam",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        )
        
        # 3. Benchmark Scenario
        scenario = BenchmarkScenario(
            scenario_id="scen_1",
            name="Test Scenario",
            description="Short E2E test scenario",
            seed=42,
            events=[]
        )

        campaign = BenchmarkCampaign(
            campaign_id="camp_e2e",
            name="E2E Integration",
            description="Verifies the hosting path",
            scenarios=[scenario],
            contestants=[manifest]
        )

        # 4. Execute full flow
        # This will: build -> deploy -> session.start -> benchmark -> destroy
        result = runner.run(campaign)

        # 5. Assertions
        self.assertEqual(result.campaign_id, "camp_e2e")
        self.assertEqual(result.total_runs, 1)
        self.assertEqual(result.failed_runs, 0)
        self.assertEqual(result.successful_runs, 1)

        # Verify deployment was registered
        history = registry.list_by_submission("sub_e2e")
        self.assertEqual(len(history), 1)
        
        # Verify it ended up TERMINATED due to proper teardown
        latest = registry.latest_deployment("sub_e2e")
        self.assertEqual(latest.status.value, "TERMINATED")


if __name__ == "__main__":
    unittest.main()
