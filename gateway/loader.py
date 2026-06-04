from __future__ import annotations

from typing import Any

# --- Engine Loader Subsystem ---
# Loads contestant compiled shared library engines and executes C ABI functions.

class EngineHandle:
    """Opaque pointer container representing the loaded engine instance state."""

    def __init__(self, engine_state: Any) -> None:
        """Initializes the EngineHandle.

        Args:
            engine_state: The pointer or reference to the engine state.
        """
        raise NotImplementedError


class EngineLoader:
    """Dynamically loads engine shared libraries and handles binary function bindings."""

    def __init__(self) -> None:
        """Initializes the EngineLoader."""
        raise NotImplementedError

    def load(self, so_path: str) -> None:
        """Loads a contestant's matching engine shared library (.so or .dll).

        Args:
            so_path: The absolute path to the library.
        """
        raise NotImplementedError

    def call_init(self, instruments: list[Any]) -> EngineHandle:
        """Calls the engine_init C symbol with instrument definitions.

        Args:
            instruments: List of instrument definitions to initialize the engine with.

        Returns:
            EngineHandle: The handle to the initialized engine.
        """
        raise NotImplementedError

    def call_on_message(self, handle: EngineHandle, record: Any, outbound: Any) -> None:
        """Calls the engine_on_message C symbol to process an inbound message.

        Args:
            handle: The EngineHandle of the engine.
            record: The inbound sequenced record.
            outbound: The RingBufferWriter for outbound reports.
        """
        raise NotImplementedError

    def call_destroy(self, handle: EngineHandle) -> None:
        """Calls the engine_destroy C symbol to clean up resources.

        Args:
            handle: The EngineHandle to destroy.
        """
        raise NotImplementedError

    def unload(self) -> None:
        """Unloads the shared library from the process memory space."""
        raise NotImplementedError
