from dataclasses import dataclass

@dataclass
class ExecutionStatistics:
    """Stream B: Sandbox execution metrics capturing actual contestant execution behavior."""
    runtime_ms: float
    event_count: int
    eps: float
    sandbox_overhead_ms: float = 0.0
