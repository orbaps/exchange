import unittest
from datetime import datetime
from leaderboard.models import LeaderboardEntry, LeaderboardSnapshot
from leaderboard.tiebreak import TieBreaker
from leaderboard.ranking import RankingEngine
from leaderboard.history import RankingHistory
from leaderboard.analytics import LeaderboardAnalytics
from leaderboard.rating import RatingGrade
from campaign.result import CampaignResult, ContestantCampaignResult

class TestLeaderboard(unittest.TestCase):
    
    def _create_mock_entry(self, cid, score, correctness, success, latency):
        return LeaderboardEntry(
            contestant_id=cid,
            rank=0,
            score=score,
            average_correctness=correctness,
            average_latency=latency,
            average_tps=1000.0,
            success_rate=success,
            campaign_id="c1",
            rating_grade=RatingGrade.S
        )
        
    def test_tiebreak_rules(self):
        """Tests the priority cascade: Score -> Correctness -> Reliability -> Latency -> ID"""
        e1 = self._create_mock_entry("A", 90, 100, 100, 5)
        e2 = self._create_mock_entry("B", 80, 100, 100, 5) # Lower score
        e3 = self._create_mock_entry("C", 90, 90, 100, 5)  # Lower correctness
        e4 = self._create_mock_entry("D", 90, 100, 90, 5)  # Lower success
        e5 = self._create_mock_entry("E", 90, 100, 100, 10) # Higher latency
        
        entries = [e5, e4, e3, e2, e1]
        entries.sort(key=TieBreaker.get_sort_key)
        
        # Sorted order should be A, E, D, C, B
        self.assertEqual(entries[0].contestant_id, "A")
        self.assertEqual(entries[1].contestant_id, "E") # E beats D on success rate
        self.assertEqual(entries[2].contestant_id, "D")
        self.assertEqual(entries[3].contestant_id, "C")
        self.assertEqual(entries[4].contestant_id, "B")

    def test_exact_tie(self):
        """Test exact metrics fallback to alphabetical ID."""
        a = self._create_mock_entry("Contestant_A", 100, 100, 100, 1.0)
        b = self._create_mock_entry("Contestant_B", 100, 100, 100, 1.0)
        
        entries = [b, a]
        entries.sort(key=TieBreaker.get_sort_key)
        
        self.assertEqual(entries[0].contestant_id, "Contestant_A")
        self.assertEqual(entries[1].contestant_id, "Contestant_B")

    def _create_contestant_result(self, score):
        res = ContestantCampaignResult("mock")
        res.average_score = score
        res.average_correctness = 100
        res.success_rate = 100
        res.average_latency_ms = 1.0
        return res

    def test_rank_assignment_dense(self):
        """Tests that ranks are dense (1,2,3,4) instead of skipped (1,2,2,4)."""
        c1 = self._create_contestant_result(100)
        c2 = self._create_contestant_result(90)
        c3 = self._create_contestant_result(90)
        c4 = self._create_contestant_result(80)
        
        camp = CampaignResult("camp1", 4, 4, 0, {
            "C1": c1, "C2": c2, "C3": c3, "C4": c4
        })
        
        snapshot = RankingEngine.calculate(camp)
        
        ranks = [e.rank for e in snapshot.entries]
        self.assertEqual(ranks, [1, 2, 3, 4])
        
    def test_deterministic_ranking(self):
        """100 identical runs should produce 100 identical snapshots."""
        camp = CampaignResult("camp1", 2, 2, 0, {
            "A": self._create_contestant_result(80),
            "B": self._create_contestant_result(90)
        })
        
        first = RankingEngine.calculate(camp)
        for _ in range(100):
            snap = RankingEngine.calculate(camp)
            self.assertEqual(snap.entries[0].contestant_id, first.entries[0].contestant_id)
            self.assertEqual(snap.entries[1].contestant_id, first.entries[1].contestant_id)

    def test_history_storage(self):
        hist = RankingHistory()
        self.assertIsNone(hist.latest())
        
        snap = LeaderboardSnapshot("s1", "c1", datetime.now())
        hist.add_snapshot(snap)
        
        self.assertEqual(hist.latest(), snap)
        self.assertEqual(hist.get_snapshot("s1"), snap)
        self.assertIsNone(hist.get_snapshot("s2"))
        
    def test_analytics_computation(self):
        snap = LeaderboardSnapshot("s1", "c1", datetime.now(), entries=[
            self._create_mock_entry("A", 100, 100, 100, 1),
            self._create_mock_entry("B", 80, 100, 100, 1),
            self._create_mock_entry("C", 60, 100, 100, 1)
        ])
        
        report = LeaderboardAnalytics.calculate(snap)
        
        self.assertEqual(report.best_score, 100.0)
        self.assertEqual(report.worst_score, 60.0)
        self.assertEqual(report.average_score, 80.0)
        self.assertEqual(report.median_score, 80.0)
        self.assertEqual(report.score_spread, 40.0)

if __name__ == '__main__':
    unittest.main()
