from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from contracts.instruments import InstrumentDefinition
from contracts.events import JournalRecord
from sdk.ringbuffer import RingBufferWriter

# ---
# Engine C ABI equivalent interfaces and handles for contestant matching engine core
# ---

@dataclass
class EngineHandle:
    """Python representation wrapping a C-style pointer/reference to engine state."""
    engine_state_address: int


class IEngine(ABC):
    """Abstract interface matching the C ABI of the matching engine library."""

    @abstractmethod
    def engine_init(
        self,
        instruments: List[InstrumentDefinition],
        instrument_count: int,
    ) -> EngineHandle:
        """Called once at startup with instrument definitions to initialize the engine core.

        Equivalent to: EngineHandle* engine_init(const InstrumentDefinition*, uint32_t)
        """
        raise NotImplementedError

    @abstractmethod
    def engine_on_message(
        self,
        handle: EngineHandle,
        record: JournalRecord,
        outbound: RingBufferWriter,
    ) -> None:
        """Called for each inbound message to match and write ExecutionReports.

        Equivalent to: void engine_on_message(EngineHandle*, const JournalRecord*, RingBufferWriter*)
        """
        raise NotImplementedError

    @abstractmethod
    def engine_destroy(self, handle: EngineHandle) -> None:
        """Called at shutdown for cleanup and resource deallocation.

        Equivalent to: void engine_destroy(EngineHandle*)
        """
        raise NotImplementedError
