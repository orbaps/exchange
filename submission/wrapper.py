from typing import Dict, Any
from benchmarking.contestant_adapter import ContestantEngine
from validation_engine.snapshots import EngineSnapshot

class ContestantSubmissionAdapter(ContestantEngine):
    """Wraps an untrusted contestant engine, normalizing outputs and catching exceptions."""
    
    def __init__(self, raw_engine: Any):
        self._engine = raw_engine
        
    def _safe_execute(self, method_name: str, *args, **kwargs) -> Any:
        """Safely executes a method on the contestant engine, converting exceptions."""
        try:
            method = getattr(self._engine, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            # Here we normalize all contestant-thrown exceptions to a standard format
            # In a real environment, this might be a specialized ContestantCrashException
            raise RuntimeError(f"Contestant engine crashed during {method_name}: {e}") from e

    def submit_order(self, payload: Dict[str, Any]) -> None:
        self._safe_execute("submit_order", payload)

    def cancel_order(self, payload: Dict[str, Any]) -> None:
        self._safe_execute("cancel_order", payload)

    def replace_order(self, payload: Dict[str, Any]) -> None:
        self._safe_execute("replace_order", payload)

    def snapshot(self) -> EngineSnapshot:
        # Snapshots must return our exact deterministic EngineSnapshot type.
        # If the contestant returns something else, or raises, it gets caught.
        result = self._safe_execute("snapshot")
        if not isinstance(result, EngineSnapshot):
            raise TypeError(f"Contestant snapshot returned {type(result)}, expected EngineSnapshot")
        return result

    def reset(self) -> None:
        self._safe_execute("reset")
