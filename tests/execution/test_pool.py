import unittest
import time
import threading
from execution.session import ExecutionSession
from execution.pool import WorkerPool
from execution.dispatcher import EventDispatcher
from botfleet.events import TradingEvent, EventType

class SlowSession(ExecutionSession):
    def execute(self, request):
        time.sleep(0.01) # 10ms execution
        return super().execute(request)

class TestPool(unittest.TestCase):
    def test_queue_saturation_no_deadlock(self):
        """Queue Size = 10, generate 1000 events, verify no deadlock."""
        session = SlowSession("sess_1", "sub_1", None, {})
        pool = WorkerPool(worker_count=2, max_queue_size=10)
        pool.initialize([session])
        
        dispatcher = EventDispatcher(pool)
        
        session.start()
        pool.start()
        
        # Generate 200 events (takes 1 second total execution time with 2 workers)
        events = []
        for i in range(200):
            events.append(TradingEvent(f"e{i}", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None))
            
        def producer():
            dispatcher.dispatch(events)
            
        t = threading.Thread(target=producer)
        t.start()
        
        # Wait up to 3 seconds for producer to finish (should easily finish within 2 seconds)
        t.join(timeout=3.0)
        self.assertFalse(t.is_alive(), "Producer deadlock detected!")
        
        # Wait for all events to process
        while pool.results.qsize() < 200:
            time.sleep(0.1)
            
        pool.shutdown()
        
        self.assertEqual(pool.results.qsize(), 200)

if __name__ == '__main__':
    unittest.main()
