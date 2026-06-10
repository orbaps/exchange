from typing import List
from botfleet.events import TradingEvent
from execution.pool import WorkerPool

class EventDispatcher:
    """Takes BotCampaignEvents and distributes them across the WorkerPool's DispatchQueues."""
    
    def __init__(self, pool: WorkerPool):
        self.pool = pool
        self._next_sequence_id = 0
        
    def dispatch(self, events: List[TradingEvent]):
        if not self.pool.queues:
            return
            
        queue_count = len(self.pool.queues)
        
        for i, event in enumerate(events):
            # Round Robin distribution
            target_q = self.pool.queues[i % queue_count]
            # Blocking enqueue provides backpressure
            target_q.enqueue(self._next_sequence_id, event, timeout=None)
            self._next_sequence_id += 1
