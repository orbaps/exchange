import queue
from typing import Optional, Tuple
from botfleet.events import TradingEvent

class DispatchQueue:
    """Thread-safe queue for buffering events to workers.
    Policy: Blocks producer if max_size is reached.
    """
    
    def __init__(self, max_size: int = 10000):
        self._q = queue.Queue(maxsize=max_size)
        
    def enqueue(self, sequence_id: int, event: TradingEvent, timeout: Optional[float] = None) -> bool:
        """Puts an event on the queue, blocking until space is available or timeout."""
        try:
            self._q.put((sequence_id, event), block=True, timeout=timeout)
            return True
        except queue.Full:
            return False
            
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Tuple[int, TradingEvent]]:
        """Gets an event from the queue, blocking until available or timeout."""
        try:
            return self._q.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
            
    def size(self) -> int:
        return self._q.qsize()
