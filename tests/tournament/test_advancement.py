import unittest
from datetime import datetime

from leaderboard.models import LeaderboardSnapshot, LeaderboardEntry
from leaderboard.rating import RatingGrade
from tournament.advancement import AdvancementRule, AdvancementType

class TestAdvancement(unittest.TestCase):
    def setUp(self):
        # Create a mock snapshot with 11 contestants
        self.entries = []
        for i in range(11):
            self.entries.append(LeaderboardEntry(
                contestant_id=f"team_{i}",
                rank=i+1,
                score=100.0 - i * 5,
                average_correctness=1.0,
                average_latency=10.0,
                average_tps=100.0,
                success_rate=1.0,
                campaign_id="camp1",
                rating_grade=RatingGrade.A
            ))
            
        self.snapshot = LeaderboardSnapshot(
            snapshot_id="snap1",
            campaign_id="camp1",
            timestamp=datetime.now(),
            entries=self.entries
        )
        self.current_pool = [f"team_{i}" for i in range(11)]

    def test_top_n_exact_boundary(self):
        # 11 contestants, top 10 advance
        rule = AdvancementRule(AdvancementType.TOP_N, 10)
        advanced = rule.advance(self.snapshot, self.current_pool)
        self.assertEqual(len(advanced), 10)
        self.assertNotIn("team_10", advanced) # The 11th rank (index 10) is eliminated

    def test_top_n_under_boundary(self):
        # 11 contestants, top 20 advance
        rule = AdvancementRule(AdvancementType.TOP_N, 20)
        advanced = rule.advance(self.snapshot, self.current_pool)
        self.assertEqual(len(advanced), 11)

    def test_top_percent(self):
        # Top 50% of 11 is 5
        rule = AdvancementRule(AdvancementType.TOP_PERCENT, 50)
        advanced = rule.advance(self.snapshot, self.current_pool)
        self.assertEqual(len(advanced), 6)
        self.assertEqual(advanced[-1], "team_5")

    def test_min_score(self):
        # Scores go 100, 95, 90, 85, 80...
        # 85+ should be index 0, 1, 2, 3
        rule = AdvancementRule(AdvancementType.MIN_SCORE, 85.0)
        advanced = rule.advance(self.snapshot, self.current_pool)
        self.assertEqual(len(advanced), 4)

if __name__ == "__main__":
    unittest.main()
