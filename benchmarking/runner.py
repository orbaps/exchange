from benchmarking.scenario import BenchmarkScenario
from benchmarking.contestant_adapter import ContestantEngine
from benchmarking.metrics import MetricsCollector
from benchmarking.result import ScenarioResult, BenchmarkResult
from validation_engine.comparator import StateComparator

from telemetry.collector import TelemetryCollector
from telemetry.sample import FrameworkMetricSample
from telemetry.latency import LatencyCalculator
from telemetry.tps import TPSCalculator
from telemetry.report import TelemetryReport

import time

class BenchmarkRunner:
    """Executes a scenario against engines and compares the results."""
    
    def _execute_engine(self, engine: ContestantEngine, scenario: BenchmarkScenario, collector: TelemetryCollector = None) -> ScenarioResult:
        """Executes a scenario against a single engine instance and captures the result."""
        engine.reset()
        
        with MetricsCollector() as metrics:
            for event in scenario.events:
                t0 = time.perf_counter_ns()
                
                if event.event_type == "NewOrderRequest":
                    engine.submit_order(event.payload)
                elif event.event_type == "CancelOrderRequest":
                    engine.cancel_order(event.payload)
                elif event.event_type == "ReplaceOrderRequest":
                    engine.replace_order(event.payload)
                    
                t1 = time.perf_counter_ns()
                if collector:
                    collector.record(FrameworkMetricSample(
                        timestamp_ns=t0,
                        event_name=event.event_type,
                        duration_ns=t1 - t0,
                        success=True
                    ))
                    
        t0 = time.perf_counter_ns()
        snapshot = engine.snapshot()
        t1 = time.perf_counter_ns()
        if collector:
            collector.record(FrameworkMetricSample(
                timestamp_ns=t0,
                event_name="snapshot",
                duration_ns=t1 - t0,
                success=True
            ))
        
        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            snapshot=snapshot,
            execution_time_ms=metrics.execution_time_ms
        )

    def run(self, scenario: BenchmarkScenario, reference: ContestantEngine, contestant: ContestantEngine) -> BenchmarkResult:
        """Runs the benchmark against both engines and returns the compared result."""
        
        # 1. Execute Reference
        ref_result = self._execute_engine(reference, scenario)
        
        # 2. Execute Contestant
        collector = TelemetryCollector()
        con_result = self._execute_engine(contestant, scenario, collector)
        
        # 3. Compare Snapshots
        comparator = StateComparator()
        val_result = comparator.compare_snapshots(ref_result.snapshot, con_result.snapshot)
        
        # 4. Count snapshots
        # TODO: Phase 3.X: Change `snapshot_count` to mean Validation Snapshots Produced instead of object count.
        snapshot_count = (
            len(ref_result.snapshot.book_snapshots) +
            sum(len(orders) for orders in ref_result.snapshot.order_snapshots.values()) +
            sum(len(trades) for trades in ref_result.snapshot.trade_snapshots.values())
        )
        
        # 5. Build TelemetryReport
        samples = collector.samples()
        framework_latency = LatencyCalculator.calculate(samples)
        framework_tps = TPSCalculator.calculate(collector.count(), con_result.execution_time_ms / 1000.0)
        
        sandbox_execution = None
        if hasattr(contestant, 'last_execution_stats'):
            sandbox_execution = getattr(contestant, 'last_execution_stats')
            
        telemetry_report = TelemetryReport(
            framework_latency=framework_latency,
            framework_tps=framework_tps,
            sandbox_execution=sandbox_execution,
            correctness_score=val_result.correctness_score
        )
        
        # 6. Return BenchmarkResult
        return BenchmarkResult(
            scenario_id=scenario.scenario_id,
            correctness_score=val_result.correctness_score,
            validation_result=val_result,
            reference_execution_time_ms=ref_result.execution_time_ms,
            contestant_execution_time_ms=con_result.execution_time_ms,
            snapshot_count=snapshot_count,
            mismatch_count=val_result.failed_checks,
            telemetry_report=telemetry_report
        )
