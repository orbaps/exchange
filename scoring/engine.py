from __future__ import annotations

import dataclasses

from validation_engine.reports import DiffReport

# --- Scoring Engine Structures & Logic ---

@dataclasses.dataclass(frozen=True)
class WeightConfig:
    """Weight configuration values for computing composite score components."""
    w_correctness: float
    w_latency: float
    w_throughput: float
    w_stability: float
    w_resilience: float


@dataclasses.dataclass(frozen=True)
class TelemetryAggregates:
    """Consolidated performance metrics from Flink/ClickHouse for a validation run."""
    p50LatencyNs: int
    p90LatencyNs: int
    p99LatencyNs: int
    p999LatencyNs: int
    sustainedTps: float
    peakTps: float
    latencyStddev: float
    latencyMean: float
    errorRate: float
    chaosEventsHandled: int
    chaosEventsTotal: int


@dataclasses.dataclass(frozen=True)
class CompositeScore:
    """The final calculated score breakdown for a matching engine run."""
    runId: str
    submissionId: str
    totalScore: float
    correctnessScore: float
    latencyScore: float
    throughputScore: float
    stabilityScore: float
    resilienceScore: float
    gated: bool


class Normalizer:
    """Normalizes raw metric values using min-max scaling."""

    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Scales a given value to a [0, 1] range based on specified min and max bounds."""
        raise NotImplementedError


class CorrectnessGate:
    """Ensures a minimum correctness score threshold is achieved to qualify for scoring."""

    def __init__(self, threshold: float) -> None:
        """Initializes the gate with a minimum correctness threshold (e.g. 0.95)."""
        raise NotImplementedError

    def passes(self, correctnessScore: float) -> bool:
        """Determines if the given correctness score passes the threshold."""
        raise NotImplementedError


class ScoringEngine:
    """Computes composite scores combining validation and performance telemetry."""

    def __init__(
        self,
        normalizer: Normalizer,
        gate: CorrectnessGate,
        weights: WeightConfig,
    ) -> None:
        """Initializes the ScoringEngine with necessary processing blocks and weights."""
        raise NotImplementedError

    def computeScore(
        self,
        diffs: DiffReport,
        telemetry: TelemetryAggregates,
    ) -> CompositeScore:
        """Executes full scoring formula based on correctness report and telemetry metrics."""
        raise NotImplementedError
