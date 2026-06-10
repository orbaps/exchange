from dataclasses import dataclass

@dataclass
class ExecutionStatistics:
    total_events: int = 0
    successful_events: int = 0
    failed_events: int = 0
    timeout_events: int = 0
    crashed_events: int = 0
    queue_overflow_events: int = 0
    
    events_per_second: float = 0.0
    average_execution_time_ms: float = 0.0
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p99_ms: float = 0.0
