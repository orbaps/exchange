import unittest
from execution.session import ExecutionSession
from execution.protocol import ExecutionRequest
from botfleet.events import TradingEvent, EventType

class TestSession(unittest.TestCase):
    def test_session_lifecycle(self):
        session = ExecutionSession("sess_1", "sub_1", None, {})
        event = TradingEvent("e1", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)
        request = ExecutionRequest("sess_1", event)
        
        # Not started
        resp = session.execute(request)
        self.assertFalse(resp.success)
        self.assertEqual(resp.error, "Session not running")
        
        # Started
        session.start()
        resp = session.execute(request)
        self.assertTrue(resp.success)
        self.assertIsNone(resp.error)
        self.assertTrue(resp.latency_ns >= 0)
        
        # Stopped
        session.stop()
        resp = session.execute(request)
        self.assertFalse(resp.success)

if __name__ == '__main__':
    unittest.main()
