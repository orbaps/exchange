from abc import ABC, abstractmethod
from typing import Dict, Any
from validation_engine.snapshots import EngineSnapshot

class ContestantEngine(ABC):
    """Normalized interface for benchmarking contestant implementations."""
    
    @abstractmethod
    def submit_order(self, payload: Dict[str, Any]) -> None:
        """Submits a new order to the engine."""
        pass

    @abstractmethod
    def cancel_order(self, payload: Dict[str, Any]) -> None:
        """Cancels an existing order in the engine."""
        pass

    @abstractmethod
    def replace_order(self, payload: Dict[str, Any]) -> None:
        """Replaces an existing order in the engine."""
        pass

    @abstractmethod
    def snapshot(self) -> EngineSnapshot:
        """Extracts the deterministic snapshot of the engine state."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Resets the engine to a clean state."""
        pass
