from dataclasses import dataclass
from typing import Optional
from validation_engine.snapshots import EngineSnapshot
from validation_engine.result import ValidationResult

@dataclass
class ScenarioResult:
    """The result of executing a scenario on a single engine."""
    scenario_id: str
    snapshot: EngineSnapshot
    execution_time_ms: float

@dataclass
class BenchmarkResult:
    """The final result of comparing reference and contestant executions."""
    scenario_id: str
    correctness_score: float
    validation_result: ValidationResult
    reference_execution_time_ms: float
    contestant_execution_time_ms: float
    snapshot_count: int
    mismatch_count: int
