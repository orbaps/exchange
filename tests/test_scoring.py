import unittest

from scoring.latency import LatencyScorer
from scoring.throughput import ThroughputScorer
from scoring.reliability import ReliabilityScorer
from scoring.calculator import ScoreCalculator

from telemetry.latency import LatencyStatistics
from telemetry.execution import ExecutionStatistics
from telemetry.tps import TPSStatistics
from telemetry.failures import FailureStatistics
from telemetry.report import TelemetryReport
from benchmarking.result import BenchmarkResult
from validation_engine.result import ValidationResult

class TestScoring(unittest.TestCase):
    
    def test_latency_scorer_bounds(self):
        # Excellent
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 1.0, 1)), 100.0)
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 0.5, 1)), 100.0)
        
        # Interpolations
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 3.0, 1)), 95.0)
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 15.0, 1)), 70.0)
        
        # Poor
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 50.0, 1)), 40.0)
        self.assertEqual(LatencyScorer.calculate(LatencyStatistics(0, 0, 0, 0, 0, 0, 100.0, 1)), 20.0)

    def test_throughput_scorer_bounds(self):
        # Excellent
        self.assertEqual(ThroughputScorer.calculate(ExecutionStatistics(100, 1000, 100000.0, 0), TPSStatistics(0, 0.0, 0.0)), 100.0)
        
        # Interpolations
        self.assertEqual(ThroughputScorer.calculate(ExecutionStatistics(100, 1000, 75000.0, 0), TPSStatistics(0, 0.0, 0.0)), 95.0)
        
        # Poor
        self.assertEqual(ThroughputScorer.calculate(ExecutionStatistics(100, 1000, 5000.0, 0), TPSStatistics(0, 0.0, 0.0)), 40.0)
        self.assertEqual(ThroughputScorer.calculate(ExecutionStatistics(100, 1000, 1000.0, 0), TPSStatistics(0, 0.0, 0.0)), 20.0)
        
    def test_reliability_scorer(self):
        self.assertEqual(ReliabilityScorer.calculate(FailureStatistics(100, 0, 0, 0, 100.0, 0.0)), 100.0)
        self.assertEqual(ReliabilityScorer.calculate(FailureStatistics(99, 1, 0, 0, 99.0, 1.0)), 99.0)

    def _create_perfect_benchmark_result(self, correctness: float) -> BenchmarkResult:
        tel = TelemetryReport(
            framework_latency=LatencyStatistics(0, 0, 0, 0, 0, 0, 1.0, 1),
            framework_tps=TPSStatistics(100000, 1.0, 100000.0),
            sandbox_execution=ExecutionStatistics(100, 1000, 100000.0, 0)
        )
        return BenchmarkResult(
            scenario_id="s1",
            validation_result=ValidationResult(),
            correctness_score=correctness,
            reference_execution_time_ms=1.0,
            contestant_execution_time_ms=1.0,
            snapshot_count=1000,
            mismatch_count=0,
            telemetry_report=tel
        )

    def test_correctness_gate_penalizes_heavily(self):
        """Test Correctness Gate as requested."""
        # Scenario: Perfect latency, perfect throughput, perfect reliability, BUT correctness is 40.
        bench = self._create_perfect_benchmark_result(correctness=40.0)
        failures = FailureStatistics(1, 0, 0, 0, 100.0, 0.0)
        
        # If formula was naive: 0.7*40 + 0.15*100 + 0.1*100 + 0.05*100 = 28 + 15 + 10 + 5 = 58
        # But gate says: if correctness < 50, final_score = correctness (40)
        res = ScoreCalculator.calculate("c1", "s1", bench, failures)
        
        self.assertEqual(res.breakdown.correctness_score, 40.0)
        self.assertEqual(res.breakdown.latency_score, 100.0)
        self.assertEqual(res.breakdown.throughput_score, 100.0)
        self.assertEqual(res.breakdown.reliability_score, 100.0)
        
        # Final score heavily penalized
        self.assertEqual(res.breakdown.final_score, 40.0)
        
    def test_correctness_gate_medium_penalty(self):
        # Scenario: Correctness = 70.
        # Base: 0.7*70 (49) + 15 + 10 + 5 = 79
        # Gate: if < 80, final_score *= 0.75 => 79 * 0.75 = 59.25
        bench = self._create_perfect_benchmark_result(correctness=70.0)
        failures = FailureStatistics(1, 0, 0, 0, 100.0, 0.0)
        
        res = ScoreCalculator.calculate("c1", "s1", bench, failures)
        self.assertAlmostEqual(res.breakdown.final_score, 59.25)
        
    def test_perfect_score(self):
        bench = self._create_perfect_benchmark_result(correctness=100.0)
        failures = FailureStatistics(1, 0, 0, 0, 100.0, 0.0)
        
        res = ScoreCalculator.calculate("c1", "s1", bench, failures)
        self.assertEqual(res.breakdown.final_score, 100.0)

    def test_scoring_determinism(self):
        """Verify the exact same input produces the exact same score 100 times."""
        bench = self._create_perfect_benchmark_result(correctness=75.0)
        failures = FailureStatistics(1, 0, 0, 0, 100.0, 0.0)
        
        first_score = ScoreCalculator.calculate("c1", "s1", bench, failures).breakdown.final_score
        
        for _ in range(100):
            res = ScoreCalculator.calculate("c1", "s1", bench, failures)
            self.assertEqual(res.breakdown.final_score, first_score)

if __name__ == '__main__':
    unittest.main()
