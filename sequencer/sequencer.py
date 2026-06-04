from __future__ import annotations

from sequencer.clock import MonotonicClock
from sequencer.journal import JournalWriter, JournalRecord
from sequencer.dispatch import Consumer

# --- Sequencer Core Subsystem ---
# Coordinates clock, journaling, and dispatching for incoming raw messages.

class Sequencer:
    """Core sequencer that stamps, journals, and dispatches incoming messages."""

    def __init__(self, clock: MonotonicClock, journal: JournalWriter) -> None:
        """Initializes the Sequencer.

        Args:
            clock: The MonotonicClock instance.
            journal: The JournalWriter instance.
        """
        raise NotImplementedError

    def start(self, run_id: str) -> None:
        """Starts the sequencer session for the given run ID.

        Args:
            run_id: Unique identifier for the run.
        """
        raise NotImplementedError

    def on_raw_message(self, raw: bytes) -> JournalRecord:
        """Processes a raw message, stamps it, journals it, and dispatches it.

        Args:
            raw: The raw inbound message payload.

        Returns:
            JournalRecord: The generated journal record.
        """
        raise NotImplementedError

    def add_consumer(self, consumer: Consumer) -> None:
        """Registers a consumer to receive dispatched records.

        Args:
            consumer: The Consumer instance.
        """
        raise NotImplementedError

    def shutdown(self) -> None:
        """Gracefully shuts down the sequencer, flushing and closing resources."""
        raise NotImplementedError

    def _stamp(self, payload: bytes) -> JournalRecord:
        """Internal helper to stamp a payload with global sequence and logical timestamp.

        Args:
            payload: The message payload to stamp.

        Returns:
            JournalRecord: Stamped record.
        """
        raise NotImplementedError
