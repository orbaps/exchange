from __future__ import annotations

import time

# --- Monotonic Clock Subsystem ---
# This class provides nanosecond-granularity logical clock offsets for sequencing.

class MonotonicClock:
    """A monotonic clock for generating high-precision, logical timestamps."""

    def __init__(self, epoch_offset_ns: int = 0) -> None:
        """Initializes the MonotonicClock with an epoch offset.

        Args:
            epoch_offset_ns: The starting offset in nanoseconds.
        """
        raise NotImplementedError

    def now(self) -> int:
        """Returns the current logical timestamp in nanoseconds.

        Returns:
            int: The logical timestamp.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Resets the logical clock epoch offset."""
        raise NotImplementedError
