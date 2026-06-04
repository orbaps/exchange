from __future__ import annotations

from typing import Iterable, List

from validation_engine.models import ExecutionReport
from validation_engine.reports import DiffReport, ValidationError
from validation_engine.validators import (
    SchemaValidator,
    SequenceValidator,
    InvariantChecker,
    StateMachineChecker,
    PriorityChecker,
    QuantityConservationChecker,
)
from validation_engine.differs import ReplayDiffer, SnapshotDiffer

# --- Top-Level Validation Orchestrator ---

class ValidationEngine:
    """Orchestrates schema, sequence, invariant, priority and diff checks across execution runs."""

    def __init__(
        self,
        schema_validator: SchemaValidator,
        sequence_validator: SequenceValidator,
        invariant_checker: InvariantChecker,
        state_checker: StateMachineChecker,
        priority_checker: PriorityChecker,
        qty_checker: QuantityConservationChecker,
        replay_differ: ReplayDiffer,
        snapshot_differ: SnapshotDiffer,
    ) -> None:
        """Initializes the ValidationEngine with all required validation components."""
        raise NotImplementedError

    def validateRun(
        self,
        contestant: Iterable[ExecutionReport],
        reference: Iterable[ExecutionReport],
    ) -> DiffReport:
        """Compares contestant execution stream against golden-standard reference stream."""
        raise NotImplementedError

    def validateSingle(self, report: ExecutionReport) -> List[ValidationError]:
        """Runs single-report checks (schema, sequence, invariants) on a single ExecutionReport."""
        raise NotImplementedError
