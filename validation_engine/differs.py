from __future__ import annotations

from typing import List

from validation_engine.models import (
    ExecutionReport,
    BookSnapshot,
    FieldDiff,
    LevelDiff,
)

# --- Diffing Subsystem ---

class ReplayDiffer:
    """Compares individual contestant execution reports against golden standard reference reports."""

    def diff(self, expected: ExecutionReport, actual: ExecutionReport) -> List[FieldDiff]:
        """Compares two ExecutionReport messages field-by-field and returns differences."""
        raise NotImplementedError


class SnapshotDiffer:
    """Compares order book state depth snapshots between actual and expected engines."""

    def diff(self, expected: BookSnapshot, actual: BookSnapshot) -> List[LevelDiff]:
        """Compares two BookSnapshot states level-by-level and returns differences."""
        raise NotImplementedError
