import unittest
from fastapi.testclient import TestClient
from dashboard.app import app
from dashboard.dependencies import state_cache
from dashboard.models.schemas import LeaderboardSnapshotResponse, TournamentResponse

class TestDashboardEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        state_cache.clear()

    def test_leaderboard_empty_and_populated(self):
        # Empty cache -> 404
        response = self.client.get("/api/public/leaderboard")
        self.assertEqual(response.status_code, 404)

        # Set leaderboard snapshot in cache
        snap = LeaderboardSnapshotResponse(
            snapshot_id="snap1", campaign_id="camp1", timestamp="12345",
            entries=[], entry_count=0, generated_at="now", load_profile="N/A",
            event_count=0, campaign_size=0, worker_count=1, execution_tps=0.0
        )
        state_cache.set_leaderboard(snap)

        response = self.client.get("/api/public/leaderboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["snapshot_id"], "snap1")

    def test_tournament_empty_and_populated(self):
        response = self.client.get("/api/public/tournament")
        self.assertEqual(response.status_code, 404)

        t = TournamentResponse(
            tournament_id="t1", name="Beta Cup", description="", status="RUNNING",
            created_at=1000, start_time=1005, end_time=None, stages=[]
        )
        state_cache.set_tournament(t)

        response = self.client.get("/api/public/tournament")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tournament_id"], "t1")

    def test_deployments_empty(self):
        response = self.client.get("/api/public/deployments")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_analytics_empty(self):
        response = self.client.get("/api/public/analytics")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_scenarios_run"], 0)
