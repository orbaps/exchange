import unittest

from telemetry.sample import MetricSample
from telemetry.latency import LatencyCalculator
from telemetry.tps import TPSCalculator
from telemetry.failures import FailureCalculator
from sandbox.result import SandboxResult
from campaign.result import CampaignRunResult, RunStatus

class TestTelemetry(unittest.TestCase):

    def test_single_sample_percentile(self):
        """Test Single Sample Percentile as requested."""
        samples = [
            MetricSample(timestamp_ns=0, event_name="e1", duration_ns=100 * 1_000_000, success=True)
        ]
        
        stats = LatencyCalculator.calculate(samples)
        
        self.assertEqual(stats.p50_ms, 100.0)
        self.assertEqual(stats.p90_ms, 100.0)
        self.assertEqual(stats.p95_ms, 100.0)
        self.assertEqual(stats.p99_ms, 100.0)

    def test_multiple_samples_percentile(self):
        samples = [
            MetricSample(timestamp_ns=0, event_name="e", duration_ns=i * 1_000_000, success=True)
            for i in range(1, 101)  # 1 to 100
        ]
        
        stats = LatencyCalculator.calculate(samples)
        self.assertEqual(stats.min_ms, 1.0)
        self.assertEqual(stats.max_ms, 100.0)
        
        # rank = ceil(p * N)
        # p50 -> 50th -> index 49 -> value 50
        self.assertEqual(stats.p50_ms, 50.0)
        
        # p90 -> 90th -> index 89 -> value 90
        self.assertEqual(stats.p90_ms, 90.0)
        
        # p95 -> 95th -> index 94 -> value 95
        self.assertEqual(stats.p95_ms, 95.0)
        
        # p99 -> 99th -> index 98 -> value 99
        self.assertEqual(stats.p99_ms, 99.0)

    def test_empty_samples(self):
        stats = LatencyCalculator.calculate([])
        self.assertEqual(stats.avg_ms, 0.0)
        self.assertEqual(stats.p99_ms, 0.0)
        self.assertEqual(stats.sample_count, 0)
        
    def test_tps_calculator(self):
        stats = TPSCalculator.calculate(total_events=1000, runtime_seconds=2.0)
        self.assertEqual(stats.tps, 500.0)
        
    def test_tps_calculator_zero_runtime(self):
        stats = TPSCalculator.calculate(total_events=1000, runtime_seconds=0.0)
        self.assertEqual(stats.tps, 0.0)
        
    def test_failure_calculator_sandbox(self):
        results = [
            SandboxResult(success=True, exit_code=0, runtime_ms=10.0, timed_out=False, crashed=False, stdout="", stderr=""),
            SandboxResult(success=False, exit_code=1, runtime_ms=10.0, timed_out=False, crashed=True, stdout="", stderr=""),
            SandboxResult(success=False, exit_code=None, runtime_ms=10.0, timed_out=True, crashed=False, stdout="", stderr="")
        ]
        
        stats = FailureCalculator.calculate_from_sandbox_results(results)
        self.assertEqual(stats.success_count, 1)
        self.assertEqual(stats.failure_count, 2)
        self.assertEqual(stats.timeout_count, 1)
        self.assertEqual(stats.crash_count, 1)
        self.assertAlmostEqual(stats.success_rate, 33.333, places=2)
        self.assertAlmostEqual(stats.failure_rate, 66.666, places=2)

if __name__ == '__main__':
    unittest.main()
