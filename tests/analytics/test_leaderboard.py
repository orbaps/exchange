import unittest
from analytics.bus import AnalyticsEventBus
from analytics.leaderboard import LiveLeaderboard
from leaderboard.models import LeaderboardSnapshot, LeaderboardEntry

import datetime

class TestLeaderboardDelta(unittest.TestCase):
    def test_rank_deltas(self):
        bus = AnalyticsEventBus()
        events = []
        bus.subscribe(events.append)
        
        ldr = LiveLeaderboard(bus)
        
        # Initial snapshot
        s1 = LeaderboardSnapshot("snap1", "camp1", datetime.datetime.now(), [
            LeaderboardEntry("A", rank=1, score=100, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade=""),
            LeaderboardEntry("B", rank=2, score=90, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade=""),
            LeaderboardEntry("C", rank=3, score=80, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade="")
        ])
        ldr.process_snapshot(s1)
        
        # No deltas for first snapshot usually, but wait, the implementation 
        # doesn't emit if old_rank is None. Let's check events.
        self.assertEqual(len(events), 0)
        
        # Second snapshot, B overtakes A
        s2 = LeaderboardSnapshot("snap2", "camp1", datetime.datetime.now(), [
            LeaderboardEntry("B", rank=1, score=110, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade=""),
            LeaderboardEntry("A", rank=2, score=100, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade=""),
            LeaderboardEntry("C", rank=3, score=80, average_correctness=0, average_latency=0, average_tps=0, success_rate=0, campaign_id="", rating_grade="")
        ])
        ldr.process_snapshot(s2)
        
        self.assertEqual(len(events), 1)
        payload = events[0].payload
        deltas = payload["deltas"]
        
        self.assertEqual(len(deltas), 2)
        
        delta_B = next(d for d in deltas if d["contestant_id"] == "B")
        self.assertEqual(delta_B["old_rank"], 2)
        self.assertEqual(delta_B["new_rank"], 1)
        self.assertEqual(delta_B["delta"], +1)
        
        delta_A = next(d for d in deltas if d["contestant_id"] == "A")
        self.assertEqual(delta_A["old_rank"], 1)
        self.assertEqual(delta_A["new_rank"], 2)
        self.assertEqual(delta_A["delta"], -1)

if __name__ == '__main__':
    unittest.main()
