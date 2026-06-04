import time

class MetricsCollector:
    """Context manager for collecting execution metrics."""
    
    def __init__(self):
        self.start_time = 0.0
        self.end_time = 0.0
        self.execution_time_ms = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.execution_time_ms = (self.end_time - self.start_time) * 1000.0
