from __future__ import annotations

from reference_engine.models import Order, SmpResult, SmpMode

# ---
# Self-Match Prevention Handler
# ---

class SmpHandler:
    """Handles self-match prevention checks between incoming and resting orders."""

    def __init__(self, mode: SmpMode) -> None:
        """Initializes the SmpHandler with the configured SMP mode."""
        self._mode = mode

    @property
    def mode(self) -> SmpMode:
        """Returns the current SmpMode."""
        return self._mode

    def check(self, incoming: Order, resting: Order) -> SmpResult:
        """Checks if there is a self-match between incoming and resting orders, and determines action."""
        if incoming.party_id != resting.party_id:
            return SmpResult.ALLOW_MATCH
        if self._mode == SmpMode.SMP_DISABLED:
            return SmpResult.ALLOW_MATCH
        elif self._mode == SmpMode.SMP_CANCEL_NEWEST:
            return SmpResult.CANCEL_INCOMING
        elif self._mode == SmpMode.SMP_CANCEL_OLDEST:
            return SmpResult.CANCEL_RESTING
        elif self._mode == SmpMode.SMP_CANCEL_BOTH:
            return SmpResult.CANCEL_BOTH
        return SmpResult.ALLOW_MATCH

