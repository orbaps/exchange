from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from contracts.instruments import InstrumentDefinition
from contracts.events import JournalRecord
from sdk.engine import EngineHandle
from sdk.ringbuffer import RingBufferWriter

# ---
# Engine FFI loader wrappers matching dlopen/LoadLibrary logic
# ---

class IEngineLoader(ABC):
    """Abstract FFI loader for dynamically loading matching engine shared libraries."""

    @abstractmethod
    def load(self, so_path: str) -> None:
        """Loads the shared library at the given file path into the address space.

        Uses dlopen or LoadLibrary equivalents internally.
        """
        raise NotImplementedError

    @abstractmethod
    def call_init(self, instruments: List[InstrumentDefinition]) -> EngineHandle:
        """Invokes the init function of the loaded engine with instrument definitions."""
        raise NotImplementedError

    @abstractmethod
    def call_on_message(
        self,
        handle: EngineHandle,
        record: JournalRecord,
        outbound: RingBufferWriter,
    ) -> None:
        """Invokes the on_message event callback handler in the engine library."""
        raise NotImplementedError

    @abstractmethod
    def call_destroy(self, handle: EngineHandle) -> None:
        """Invokes the destroy cleanup function in the engine library."""
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Unloads the shared library from current process memory using dlclose."""
        raise NotImplementedError
