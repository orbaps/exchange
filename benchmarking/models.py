"""Benchmark data models for deterministic profiling and certification."""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class BenchmarkProfile:
    """Defines the parameters for a benchmark execution run.

    Attributes:
        profile_id: Unique identifier for this profile.
        target_qps: Target queries-per-second to simulate.
        duration_s: Duration of the benchmark in seconds.
        expected_latency_p99: Expected 99th percentile latency ceiling.
    """
    profile_id: str
    target_qps: int
    duration_s: int
    expected_latency_p99: float


@dataclass
class ScenarioDefinition:
    """Defines a deterministic benchmark scenario.

    Attributes:
        scenario_id: Unique identifier for this scenario.
        description: Human-readable description.
        steps: Ordered list of action dicts to execute.
    """
    scenario_id: str
    description: str
    steps: List[Dict[str, Any]]


@dataclass
class CertificationResult:
    """Result of evaluating a benchmark for platform certification.

    Attributes:
        cert_id: Deterministic ID derived from timestamp and hash prefix.
        passed: Whether the benchmark met certification thresholds.
        score: Computed as qps_achieved / latency_p99.
        hash_fingerprint: SHA-256 of the certification data payload.
        timestamp: Virtual clock timestamp at evaluation time.
    """
    cert_id: str
    passed: bool
    score: float
    hash_fingerprint: str
    timestamp: float
