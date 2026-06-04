from benchmarking.contestant_adapter import ContestantEngine
from benchmarking.reference_adapter import ReferenceEngineAdapter

class EngineFactory:
    """Creates instances of ContestantEngine interfaces for benchmarking."""
    
    @staticmethod
    def create_reference() -> ContestantEngine:
        """Returns a clean instance of the Reference Engine."""
        return ReferenceEngineAdapter()
        
    @staticmethod
    def create_contestant() -> ContestantEngine:
        """Returns a clean instance of the Contestant Engine.
        Currently, this just returns the Reference Adapter until a real contestant is provided.
        # TODO: Phase 3.1: Sandbox Adapter
        """
        return ReferenceEngineAdapter()
