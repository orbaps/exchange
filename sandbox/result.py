from dataclasses import dataclass
from typing import Optional

@dataclass
class SandboxResult:
    success: bool
    exit_code: Optional[int]
    runtime_ms: float
    timed_out: bool
    crashed: bool
    stdout: str
    stderr: str
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    
    from telemetry.execution import ExecutionStatistics
    execution_stats: Optional[ExecutionStatistics] = None
