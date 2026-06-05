from dataclasses import dataclass
from typing import Optional

@dataclass
class WorkerRequest:
    submission_path: str
    events_path: str
    output_path: str

@dataclass
class WorkerResponse:
    success: bool
    snapshot_path: Optional[str] = None
    error: Optional[str] = None
