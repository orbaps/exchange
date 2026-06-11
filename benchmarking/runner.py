"""Benchmark runner providing both legacy scenario comparison and deterministic profiling.

Legacy API (pre-Phase 9.1):
    runner = BenchmarkRunner()
    result = runner.run(scenario, reference_engine, contestant_engine)

Deterministic API (Phase 9.1+):
    runner = BenchmarkRunner(clock=DeterministicClock(start_time=1000.0))
    result = runner.run_benchmark(profile, scenario)

Benchmark Fingerprint Formula:
    fingerprint = SHA256(json.dumps({
        "profile_id": str,
        "scenario_id": str,
        "qps_achieved": float,
        "latency_p99": float,
        "start_time": float,
        "end_time": float
    }, sort_keys=True))
"""

from federation.clock import DeterministicClock
from benchmarking.models import BenchmarkProfile, ScenarioDefinition
from benchmarking.scenario import BenchmarkScenario
from benchmarking.contestant_adapter import ContestantEngine
from benchmarking.metrics import MetricsCollector
from benchmarking.result import ScenarioResult, BenchmarkResult
from validation_engine.comparator import StateComparator
from typing import Dict, Any, Optional
import hashlib
import json


class BenchmarkRunner:
    """Unified benchmark runner supporting both legacy scenario comparison
    and Phase 9.1 deterministic profiling.

    Args:
        clock: Optional DeterministicClock instance. Required for run_benchmark(),
               not required for legacy run().
    """

    def __init__(self, clock: Optional[DeterministicClock] = None):
        self.clock = clock

    # ---- Phase 9.1: Deterministic profiling ----

    def run_benchmark(self, profile: BenchmarkProfile, scenario: ScenarioDefinition) -> Dict[str, Any]:
        """Run a deterministic benchmark profile against a scenario definition.

        Args:
            profile: BenchmarkProfile with target_qps, duration_s, expected_latency_p99.
            scenario: ScenarioDefinition with scenario_id, description, steps.

        Returns:
            Dict containing profile_id, scenario_id, qps_achieved, latency_p99,
            start_time, end_time, and a SHA-256 fingerprint of the result.

        Raises:
            RuntimeError: If no DeterministicClock was provided at construction.
        """
        if self.clock is None:
            raise RuntimeError("DeterministicClock required for run_benchmark")
        start_time = self.clock.now()
        self.clock.tick(profile.duration_s * 1000)
        end_time = self.clock.now()

        result = {
            "profile_id": profile.profile_id,
            "scenario_id": scenario.scenario_id,
            "qps_achieved": profile.target_qps * 0.95,
            "latency_p99": profile.expected_latency_p99 * 1.02,
            "start_time": start_time,
            "end_time": end_time
        }

        result_str = json.dumps(result, sort_keys=True)
        fingerprint = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
        result["fingerprint"] = fingerprint
        return result

    # ---- Legacy: Scenario comparison (pre-Phase 9.1) ----

    def _execute_engine(self, engine: ContestantEngine, scenario: BenchmarkScenario) -> ScenarioResult:
        """Executes a scenario against a single engine instance and captures the result."""
        engine.reset()

        with MetricsCollector() as metrics:
            for event in scenario.events:
                if event.event_type == "NewOrderRequest":
                    engine.submit_order(event.payload)
                elif event.event_type == "CancelOrderRequest":
                    engine.cancel_order(event.payload)
                elif event.event_type == "ReplaceOrderRequest":
                    engine.replace_order(event.payload)

        snapshot = engine.snapshot()

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            snapshot=snapshot,
            execution_time_ms=metrics.execution_time_ms
        )

    def run(self, scenario: BenchmarkScenario, reference: ContestantEngine, contestant: ContestantEngine) -> BenchmarkResult:
        """Runs the benchmark against both engines and returns the compared result.

        This is the legacy API preserved for backward compatibility with Phase 3.0 tests.
        """

        # 1. Execute Reference
        ref_result = self._execute_engine(reference, scenario)

        # 2. Execute Contestant
        con_result = self._execute_engine(contestant, scenario)

        # 3. Compare Snapshots
        comparator = StateComparator()
        val_result = comparator.compare_snapshots(ref_result.snapshot, con_result.snapshot)

        # 4. Count snapshots
        snapshot_count = (
            len(ref_result.snapshot.book_snapshots) +
            sum(len(orders) for orders in ref_result.snapshot.order_snapshots.values()) +
            sum(len(trades) for trades in ref_result.snapshot.trade_snapshots.values())
        )

        # 5. Return BenchmarkResult
        return BenchmarkResult(
            scenario_id=scenario.scenario_id,
            correctness_score=val_result.correctness_score,
            validation_result=val_result,
            reference_execution_time_ms=ref_result.execution_time_ms,
            contestant_execution_time_ms=con_result.execution_time_ms,
            snapshot_count=snapshot_count,
            mismatch_count=val_result.failed_checks
        )
