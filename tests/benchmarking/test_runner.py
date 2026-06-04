import unittest
from typing import Dict, Any

from benchmarking.factory import EngineFactory
from benchmarking.scenarios.library import get_simple_fill_scenario, get_cancel_scenario
from benchmarking.runner import BenchmarkRunner
from benchmarking.reference_adapter import ReferenceEngineAdapter
from validation_engine.snapshots import EngineSnapshot

class BrokenAdapter(ReferenceEngineAdapter):
    """A mock contestant adapter that subtly breaks the engine logic."""
    def submit_order(self, payload: Dict[str, Any]) -> None:
        # Intentionally alter the quantity of all buy orders to simulate a bug
        payload = dict(payload)
        if payload['side'] == 'BUY':
            payload['quantity'] -= 10
        super().submit_order(payload)

class TestBenchmarkRunner(unittest.TestCase):

    def setUp(self):
        self.runner = BenchmarkRunner()

    def test_reference_vs_reference_yields_100_percent(self):
        # 1. Setup
        scenario = get_simple_fill_scenario()
        ref1 = EngineFactory.create_reference()
        ref2 = EngineFactory.create_reference()
        
        # 2. Execute
        result = self.runner.run(scenario, ref1, ref2)
        
        # 3. Assert
        self.assertEqual(result.correctness_score, 100.0)
        self.assertEqual(result.mismatch_count, 0)
        self.assertGreater(result.snapshot_count, 0)
        
    def test_reference_vs_broken_contestant_yields_less_than_100_percent(self):
        # 1. Setup
        scenario = get_simple_fill_scenario()
        ref = EngineFactory.create_reference()
        broken_con = BrokenAdapter()
        
        # 2. Execute
        result = self.runner.run(scenario, ref, broken_con)
        
        # 3. Assert
        self.assertLess(result.correctness_score, 100.0)
        self.assertGreater(result.mismatch_count, 0)
        
    def test_benchmark_result_metrics(self):
        scenario = get_cancel_scenario()
        ref = EngineFactory.create_reference()
        con = EngineFactory.create_contestant()
        
        result = self.runner.run(scenario, ref, con)
        
        self.assertEqual(result.correctness_score, 100.0)
        self.assertGreaterEqual(result.reference_execution_time_ms, 0.0)
        self.assertGreaterEqual(result.contestant_execution_time_ms, 0.0)
        self.assertEqual(result.scenario_id, "cancel_001")

if __name__ == '__main__':
    unittest.main()
