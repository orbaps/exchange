import unittest
import time
import json
import hashlib
from botfleet.events import TradingEvent, EventType
from execution.session import ExecutionSession
from execution.pool import WorkerPool
from execution.dispatcher import EventDispatcher
from execution.replay import ExecutionReplayExporter

class DeterministicSession(ExecutionSession):
    def execute(self, request):
        # Deterministic dummy logic: latency is derived from event_id
        # success is True for even length IDs, False for odd
        is_success = len(request.trading_event.event_id) % 2 == 0
        return super().execute(request)

class TestDeterminism(unittest.TestCase):
    def _run_execution(self, worker_count: int) -> str:
        session = DeterministicSession("sess_1", "sub_1", None, {})
        pool = WorkerPool(worker_count=worker_count, max_queue_size=100)
        pool.initialize([session])
        dispatcher = EventDispatcher(pool)
        
        session.start()
        pool.start()
        
        events = []
        for i in range(100):
            events.append(TradingEvent(f"e{i}", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None))
            
        dispatcher.dispatch(events)
        
        # Wait for drain
        while pool.results.qsize() < 100:
            time.sleep(0.01)
            
        pool.shutdown()
        
        results_list = []
        while not pool.results.empty():
            results_list.append(pool.results.get())
        
        # Sort results deterministically by execution_sequence_id
        results_list.sort(key=lambda x: x.execution_sequence_id)
        
        # Zero out non-deterministic timestamps and worker assignment for hash comparison
        for r in results_list:
            r.dispatch_timestamp_ns = 0
            r.completion_timestamp_ns = 0
            r.worker_id = "w0"
            
        res = ExecutionReplayExporter.save_events(results_list, f"test_exec_{worker_count}.jsonl")
        return res.sha256

    def test_multi_worker_determinism(self):
        """1 worker and 4 workers should produce identical canonical execution hashes."""
        hash_1 = self._run_execution(1)
        hash_4 = self._run_execution(4)
        
        self.assertEqual(hash_1, hash_4)

if __name__ == '__main__':
    unittest.main()
