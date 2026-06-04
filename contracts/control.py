from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import List, Optional

from contracts.messages import SessionTransition

# ---
# Control structures managing run setup and orchestration lifecycle
# ---

class RunState(enum.IntEnum):
    """Represents the execution lifecycle phases of a sandbox run."""
    QUEUED = 0
    PROVISIONING = 1
    INITIALIZING = 2
    RUNNING = 3
    DRAINING = 4
    VALIDATING = 5
    SCORING = 6
    COMPLETE = 7
    FAILED = 8


@dataclass
class RunConfig:
    """Resource constraints, sandbox parameters, and scenario descriptors for a run."""
    run_id: str
    image_ref: str
    scenario_id: str
    cpu_cores: List[int]
    memory_limit_bytes: int
    io_read_bps: int
    io_write_bps: int
    timeout_seconds: int


@dataclass
class RunStatus:
    """The dynamic running status of an active sandbox run."""
    run_id: str
    state: RunState
    error_message: Optional[str] = None
