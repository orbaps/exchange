import unittest
import os
from analytics.events import AnalyticsEvent, AnalyticsEventType
from analytics.journal import AnalyticsJournal
from analytics.replay import AnalyticsReplay

class TestAnalyticsJournal(unittest.TestCase):
    def test_journal_write_and_replay(self):
        filepath = "test_analytics_journal.jsonl"
        if os.path.exists(filepath):
            os.remove(filepath)
            
        journal = AnalyticsJournal(filepath)
        e1 = AnalyticsEvent("1", 1000, AnalyticsEventType.SCORE_UPDATE, "src1", {"score": 100})
        e2 = AnalyticsEvent("2", 2000, AnalyticsEventType.EXECUTION_UPDATE, "src2", {"success": True})
        
        # Write
        h1 = journal.write_events([e1])
        h2 = journal.write_events([e2])
        self.assertNotEqual(h1, h2)
        
        # Replay
        loaded = AnalyticsReplay.load_events(filepath)
        self.assertEqual(len(loaded), 2)
        
        self.assertEqual(loaded[0].event_id, "1")
        self.assertEqual(loaded[0].event_type, AnalyticsEventType.SCORE_UPDATE)
        self.assertEqual(loaded[0].payload["score"], 100)
        
        self.assertEqual(loaded[1].event_id, "2")
        self.assertEqual(loaded[1].event_type, AnalyticsEventType.EXECUTION_UPDATE)
        self.assertEqual(loaded[1].payload["success"], True)
        
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    unittest.main()
