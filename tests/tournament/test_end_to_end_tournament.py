import os
import shutil
import unittest
import time

from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.deployment_registry import DeploymentRegistry
from hosting.build import BuildManager
from hosting.artifacts import ArtifactStore
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL

from campaign.runner import CampaignRunner
from campaign.config import CampaignConfig
from campaign.campaign import BenchmarkCampaign
from benchmarking.scenario import BenchmarkScenario
from leaderboard.ranking import RankingEngine
from leaderboard.history import RankingHistory
from analytics.bus import AnalyticsEventBus

from tournament.models import Tournament, TournamentStatus
from tournament.stages import TournamentStage, StageType
from tournament.advancement import AdvancementRule, AdvancementType
from tournament.journal import TournamentJournal
from tournament.version_freeze import VersionFreeze
from tournament.submission_lock import SubmissionLock
from tournament.runner import TournamentRunner
from tournament.report import TournamentReportGenerator
from tournament.replay import TournamentReplay


class TestEndToEndTournament(unittest.TestCase):
    def setUp(self):
        self.artifacts_dir = "test_tournament_artifacts"
        self.journal_path = "test_tournament_artifacts/journal.jsonl"
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)

    def tearDown(self):
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)

    def test_full_tournament_lifecycle(self):
        # 1. Platform Setup
        quota = ResourceQuotaManager(total_cpu=32, total_memory_mb=32768, total_disk_mb=128000)
        router = EndpointRouter()
        registry = DeploymentRegistry()
        cm = ContainerManager(quota, router, registry)
        store = ArtifactStore(self.artifacts_dir)
        build_mgr = BuildManager(store)
        
        campaign_runner = CampaignRunner(
            config=CampaignConfig(),
            use_hosting=True,
            router=router,
            container_manager=cm,
            build_manager=build_mgr
        )
        
        history = RankingHistory()
        analytics_bus = AnalyticsEventBus()
        
        journal = TournamentJournal(self.journal_path)
        lock = SubmissionLock()
        freezer = VersionFreeze(lock, store)
        
        tournament_runner = TournamentRunner(
            journal=journal,
            version_freeze=freezer,
            campaign_runner=campaign_runner,
            analytics_bus=analytics_bus
        )

        # 2. Register 20 contestants
        manifests = []
        for i in range(20):
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

        # 3. Create Tournament with 3 Stages
        qual_campaign = BenchmarkCampaign(
            campaign_id="camp_qual", name="Qual", description="",
            scenarios=[BenchmarkScenario(scenario_id="s1", name="S1", description="", seed=1, events=[])],
            contestants=[]
        )
        semi_campaign = BenchmarkCampaign(
            campaign_id="camp_semi", name="Semi", description="",
            scenarios=[BenchmarkScenario(scenario_id="s2", name="S2", description="", seed=2, events=[])],
            contestants=[]
        )
        final_campaign = BenchmarkCampaign(
            campaign_id="camp_final", name="Final", description="",
            scenarios=[BenchmarkScenario(scenario_id="s3", name="S3", description="", seed=3, events=[])],
            contestants=[]
        )

        stages = [
            TournamentStage(
                stage_id="stage_1", name="Qualification", stage_type=StageType.QUALIFICATION,
                campaign=qual_campaign, advancement_rule=AdvancementRule(AdvancementType.TOP_N, 10)
            ),
            TournamentStage(
                stage_id="stage_2", name="Semi Final", stage_type=StageType.SEMIFINAL,
                campaign=semi_campaign, advancement_rule=AdvancementRule(AdvancementType.TOP_N, 3)
            ),
            TournamentStage(
                stage_id="stage_3", name="Final", stage_type=StageType.FINAL,
                campaign=final_campaign, advancement_rule=AdvancementRule(AdvancementType.TOP_N, 1)
            )
        ]

        tournament = Tournament(
            tournament_id="t1",
            name="Alpha Cup",
            description="",
            status=TournamentStatus.SCHEDULED,
            created_at=time.time_ns(),
            start_time=time.time_ns(),
            stages=stages
        )

        # 4. Run Tournament
        result = tournament_runner.run(tournament, manifests)

        # 5. Assertions
        self.assertEqual(tournament.status, TournamentStatus.COMPLETED)
        self.assertEqual(len(result.stage_results), 3)
        
        r1 = result.stage_results[0]
        self.assertEqual(len(r1.contestants_started), 20)
        self.assertEqual(len(r1.contestants_advanced), 10)

        r2 = result.stage_results[1]
        self.assertEqual(len(r2.contestants_started), 10)
        self.assertEqual(len(r2.contestants_advanced), 3)

        r3 = result.stage_results[2]
        self.assertEqual(len(r3.contestants_started), 3)
        # Winner must be one of the top 3
        self.assertIn(result.winner, r2.contestants_advanced)

        # 6. Report Generation
        report = TournamentReportGenerator.generate(result)
        self.assertIn("Tournament Results: t1", report)
        self.assertIn("QUALIFICATION:", report)
        self.assertIn("20 -> 10", report)
        self.assertIn("SEMIFINAL:", report)
        self.assertIn("10 -> 3", report)
        self.assertIn("FINAL:", report)
        self.assertIn("3 -> 1", report)

        # 7. Replay Determinism Test
        timeline = TournamentReplay.load_timeline(journal)
        self.assertEqual(timeline.tournament_id, "t1")
        self.assertGreater(len(timeline.events), 0)

if __name__ == "__main__":
    unittest.main()
