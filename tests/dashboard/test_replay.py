import os
import shutil
import unittest
from fastapi.testclient import TestClient
from dashboard.app import app
from tournament.journal import TournamentJournal

class TestDashboardReplay(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_dir = "test_replay_artifacts"
        self.journal_path = f"{self.test_dir}/tour_test_journal.jsonl"
        
        # Clean up and recreate test dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_replay_not_found(self):
        response = self.client.get("/api/public/replay/non_existent_id")
        self.assertEqual(response.status_code, 404)

    def test_reconstruct_timeline_and_snapshots(self):
        # 1. Write some mock entries into the journal
        journal = TournamentJournal(self.journal_path)
        journal.record_tournament_start("tour_test", ["tA", "tB"])
        
        from leaderboard.models import LeaderboardSnapshot, LeaderboardEntry
        from leaderboard.rating import RatingGrade
        from datetime import datetime
        
        snapshot = LeaderboardSnapshot(
            snapshot_id="s1", campaign_id="c1", timestamp=datetime.now(),
            entries=[
                LeaderboardEntry(contestant_id="tA", rank=1, score=98.0, average_correctness=100.0, average_latency=1.2, average_tps=1000.0, success_rate=100.0, campaign_id="c1", rating_grade=RatingGrade.S_PLUS)
            ]
        )
        journal.record_stage_start("tour_test", "stage_qual", ["tA", "tB"])
        journal.record_snapshot("tour_test", "stage_qual", snapshot)
        journal.record_advancement("tour_test", "stage_qual", ["tA"])
        journal.record_elimination("tour_test", "stage_qual", ["tB"])
        journal.record_winner_declaration("tour_test", "tA")

        # Copy this journal to the expected path in get_journal_path, or mock get_journal_path
        # The API method get_journal_path will scan '.' so it will find our journal under test_replay_artifacts!
        
        # 2. Call Timeline endpoint
        response = self.client.get("/api/public/replay/tour_test")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tournament_id"], "tour_test")
        self.assertEqual(len(data["events"]), 6)

        # 3. Call Snapshot at index 0 (TOURNAMENT_START)
        resp_snap_0 = self.client.get("/api/public/replay/tour_test/snapshot/0")
        self.assertEqual(resp_snap_0.status_code, 200)
        state_0 = resp_snap_0.json()
        self.assertEqual(state_0["status"], "RUNNING")
        self.assertEqual(state_0["active_pool"], ["tA", "tB"])
        self.assertIsNone(state_0["winner"])

        # 4. Call Snapshot at index 5 (WINNER_DECLARATION)
        resp_snap_5 = self.client.get("/api/public/replay/tour_test/snapshot/5")
        self.assertEqual(resp_snap_5.status_code, 200)
        state_5 = resp_snap_5.json()
        self.assertEqual(state_5["status"], "COMPLETED")
        self.assertEqual(state_5["active_pool"], ["tA"])
        self.assertEqual(state_5["winner"], "tA")
