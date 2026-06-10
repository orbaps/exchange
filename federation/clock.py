import threading

class DeterministicClock:
    """Thread-safe virtual clock to enforce absolute determinism across executions."""
    
    def __init__(self, start_time: float = 0.0):
        self._time: float = start_time
        self._lock = threading.Lock()

    def now(self) -> float:
        """Get the current virtual time in seconds."""
        with self._lock:
            return self._time

    def tick(self, amount: float) -> float:
        """Advance the virtual clock by a specific number of seconds."""
        with self._lock:
            if amount < 0:
                raise ValueError("Clock cannot move backwards.")
            self._time += amount
            return self._time

    def reset(self, start_time: float = 0.0) -> None:
        """Reset the clock to a specific virtual starting time."""
        with self._lock:
            self._time = start_time

# Global clock instance for shared virtual time across nodes and tests
global_clock = DeterministicClock(1600000000.0)
