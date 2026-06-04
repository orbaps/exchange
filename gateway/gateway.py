from __future__ import annotations

from sequencer.journal import JournalReader
from sequencer.dispatch import Consumer
from gateway.ipc import RingBuffer
from gateway.loader import EngineLoader

# --- Gateway Top-Level Subsystem ---
# Bridge coordinating journal playback, SPSC ring buffers, and dynamically loaded engine libraries.

class Gateway:
    """The central Gateway bridging the sequenced journal stream to the contestant matching engine via IPC."""

    def __init__(
        self,
        journal_reader: JournalReader,
        inbound_ring: RingBuffer,
        outbound_ring: RingBuffer,
        loader: EngineLoader
    ) -> None:
        """Initializes the Gateway.

        Args:
            journal_reader: Reader for sequenced records.
            inbound_ring: Inbound command SPSC ring buffer.
            outbound_ring: Outbound report SPSC ring buffer.
            loader: Loader for the engine shared library.
        """
        raise NotImplementedError

    def start(self, journal_path: str, engine_so_path: str) -> None:
        """Starts the gateway pumping events to the contestant engine.

        Args:
            journal_path: Path to the sequencer's journal file.
            engine_so_path: Path to the contestant matching engine .so/.dll.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Gracefully stops the gateway loop and cleans up loaded engine resources."""
        raise NotImplementedError

    def _pump_inbound(self) -> None:
        """Internal worker loop pumping records from the journal reader into the inbound ring buffer."""
        raise NotImplementedError

    def _drain_outbound(self) -> None:
        """Internal worker loop draining execution reports from the outbound ring buffer."""
        raise NotImplementedError
