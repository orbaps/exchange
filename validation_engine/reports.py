from __future__ import annotations

import dataclasses
from typing import List

# --- Validation Reports & Errors ---

@dataclasses.dataclass(frozen=True)
class ValidationError:
    """Represents a validation warning or failure detected during single event checks."""
    layer: str
    message: str
    severity: str
    sequenceNo: int


@dataclasses.dataclass(frozen=True)
class Divergence:
    """Represents a divergence in the comparison between actual and expected runs."""
    sequenceNo: int
    field: str
    expected: str
    actual: str
    orderId: int
    severity: str


@dataclasses.dataclass(frozen=True)
class DiffReport:
    """The aggregate diff report comparing contestant and reference runs."""
    runId: str
    totalEvents: int
    matchedEvents: int
    divergentEvents: int
    firstDivergenceSeq: int
    divergences: List[Divergence]
    correctnessScore: float
