import time
import queue
import threading
from typing import Optional

from execution.queue import DispatchQueue
from execution.session import ExecutionSession
from execution.events import ExecutionEvent
from execution.protocol import ExecutionRequest

class BenchmarkWorker(threading.Thread):
    """Worker thread that pulls events from a DispatchQueue and executes them."""
    
    def __init__(self, worker_id: str, session: ExecutionSession, dispatch_queue: DispatchQueue, results: queue.Queue):
        super().__init__(name=f"Worker-{worker_id}")
        self.worker_id = worker_id
        self.session = session
        self.dispatch_queue = dispatch_queue
        self.results = results
        self._shutdown_flag = threading.Event()
        
    def run(self):
        while not self._shutdown_flag.is_set():
            dequeued = self.dispatch_queue.dequeue(timeout=0.1)
            if not dequeued:
                continue
                
            sequence_id, event = dequeued
                
            dispatch_ts = time.time_ns()
            request = ExecutionRequest(session_id=self.session.session_id, trading_event=event)
            
            response = self.session.execute(request)
            
            completion_ts = time.time_ns()
            
            exec_event = ExecutionEvent(
                event_id=event.event_id,
                execution_sequence_id=sequence_id,
                worker_id=self.worker_id,
                session_id=self.session.session_id,
                dispatch_timestamp_ns=dispatch_ts,
                completion_timestamp_ns=completion_ts,
                success=response.success,
                error=response.error,
                trading_event=event
            )
            
            self.results.put(exec_event)
            
    def shutdown(self):
        self._shutdown_flag.set()
