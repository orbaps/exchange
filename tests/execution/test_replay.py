import unittest
import os
from botfleet.events import TradingEvent, EventType
from execution.events import ExecutionEvent
from execution.replay import ExecutionReplayExporter

class TestExecutionReplay(unittest.TestCase):
    def test_replay_exporter(self):
        te = TradingEvent("e1", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)
        ee1 = ExecutionEvent("e1", 0, "w1", "sess1", 1000, 2000, True, None, te)
        ee2 = ExecutionEvent("e2", 1, "w1", "sess1", 3000, 4000, False, "Timeout", te)
        
        filepath = "test_execution_replay.jsonl"
        res = ExecutionReplayExporter.save_events([ee1, ee2], filepath)
        
        self.assertEqual(res.event_count, 2)
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 1)
        self.assertIsNotNone(res.sha256)
        
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    unittest.main()
