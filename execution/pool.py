import queue
import threading
from typing import List

from execution.session import ExecutionSession
from execution.queue import DispatchQueue
from execution.worker import BenchmarkWorker
from execution.events import ExecutionEvent

class WorkerPool:
    """Manages creation and teardown of BenchmarkWorkers tied to specific sessions."""
    
    def __init__(self, worker_count: int, max_queue_size: int = 10000):
        self.worker_count = worker_count
        self.max_queue_size = max_queue_size
        self.workers: List[BenchmarkWorker] = []
        self.queues: List[DispatchQueue] = []
        self.results = queue.Queue()
        
    def initialize(self, sessions: List[ExecutionSession]):
        if not sessions:
            return
            
        # Round-robin assign sessions to workers
        for i in range(self.worker_count):
            session = sessions[i % len(sessions)]
            q = DispatchQueue(max_size=self.max_queue_size)
            worker = BenchmarkWorker(f"w{i}", session, q, self.results)
            self.queues.append(q)
            self.workers.append(worker)
            
    def start(self):
        for w in self.workers:
            w.start()
            
    def shutdown(self):
        for w in self.workers:
            w.shutdown()
        for w in self.workers:
            w.join()
