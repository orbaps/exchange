import unittest
from analytics.health import SessionHealthHistory, SessionHealthStatus

class TestSessionHealth(unittest.TestCase):
    def test_health_transitions(self):
        history = SessionHealthHistory()
        
        history.update("s1", SessionHealthStatus.RUNNING, 1000)
        h = history.get_health("s1")
        self.assertEqual(h.status, SessionHealthStatus.RUNNING)
        self.assertEqual(h.crash_count, 0)
        
        # Crash
        history.update("s1", SessionHealthStatus.CRASHED, 2000)
        h = history.get_health("s1")
        self.assertEqual(h.status, SessionHealthStatus.CRASHED)
        self.assertEqual(h.crash_count, 1)
        
        # Another crash shouldn't increment if it's already crashed (no transition)
        history.update("s1", SessionHealthStatus.CRASHED, 3000)
        h = history.get_health("s1")
        self.assertEqual(h.crash_count, 1)
        
        # Recover
        history.update("s1", SessionHealthStatus.RUNNING, 4000)
        # Crash again
        history.update("s1", SessionHealthStatus.CRASHED, 5000)
        h = history.get_health("s1")
        self.assertEqual(h.crash_count, 2)
        
        hist = history.get_history("s1")
        self.assertEqual(len(hist), 6) # STARTING, RUNNING, CRASHED, CRASHED, RUNNING, CRASHED

if __name__ == '__main__':
    unittest.main()
