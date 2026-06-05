from dataclasses import dataclass
from enum import Enum

class SandboxEventType(Enum):
    STARTED = "STARTED"
    FINISHED = "FINISHED"
    CRASHED = "CRASHED"
    TIMED_OUT = "TIMED_OUT"
    KILLED = "KILLED"

@dataclass
class SandboxEvent:
    timestamp: float
    submission_id: str
    event_type: SandboxEventType
    message: str
