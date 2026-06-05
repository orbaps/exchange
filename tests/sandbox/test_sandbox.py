import unittest
import os
import sys
import tempfile
import json
import shutil

from submission.metadata import SubmissionManifest
from benchmarking.scenario import BenchmarkScenario, ScenarioEvent
from validation_engine.snapshots import EngineSnapshot, BookSnapshot
from sandbox.config import SandboxConfig
from sandbox.runner import SandboxRunner
from sandbox.adapter import SandboxedContestantAdapter

# Test Engines Code
NORMAL_ENGINE = """
from validation_engine.snapshots import EngineSnapshot, BookSnapshot

class ContestantMatchingEngine:
    def __init__(self):
        self.orders = []
    def submit_order(self, p):
        self.orders.append(p)
    def cancel_order(self, p):
        pass
    def replace_order(self, p):
        pass
    def snapshot(self):
        print("Standard output capture test")
        return EngineSnapshot({"TEST": BookSnapshot("TEST", 1, 2, 1, 10, 10, 0)}, {}, {})
    def reset(self):
        self.orders.clear()
"""

EXCEPTION_ENGINE = """
class ContestantMatchingEngine:
    def __init__(self):
        pass
    def submit_order(self, p):
        raise RuntimeError("Crash on submit")
    def cancel_order(self, p):
        pass
    def replace_order(self, p):
        pass
    def snapshot(self):
        pass
    def reset(self):
        pass
"""

TIMEOUT_ENGINE = """
import time
class ContestantMatchingEngine:
    def __init__(self):
        pass
    def submit_order(self, p):
        pass
    def cancel_order(self, p):
        pass
    def replace_order(self, p):
        pass
    def snapshot(self):
        while True:
            time.sleep(1)
    def reset(self):
        pass
"""

EXIT_CODE_ENGINE = """
import sys
class ContestantMatchingEngine:
    def __init__(self):
        pass
    def submit_order(self, p):
        sys.exit(1)
    def cancel_order(self, p):
        pass
    def replace_order(self, p):
        pass
    def snapshot(self):
        pass
    def reset(self):
        pass
"""

MEMORY_EXHAUSTION_ENGINE = """
class ContestantMatchingEngine:
    def __init__(self):
        pass
    def submit_order(self, p):
        self.x = []
        while True:
            self.x.append("A" * 1000000)
    def cancel_order(self, p):
        pass
    def replace_order(self, p):
        pass
    def snapshot(self):
        pass
    def reset(self):
        pass
"""

class TestSandboxExecution(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def create_submission(self, name: str, code: str) -> SubmissionManifest:
        sub_dir = os.path.join(self.temp_dir, name)
        os.makedirs(sub_dir)
        
        with open(os.path.join(sub_dir, "engine.py"), "w") as f:
            f.write(code)
            
        with open(os.path.join(sub_dir, "metadata.json"), "w") as f:
            json.dump({
                "team_name": "Test",
                "engine_class": "ContestantMatchingEngine",
                "version": "1.0"
            }, f)
            
        return SubmissionManifest(
            submission_id=name,
            team_name="Test",
            version="1.0",
            engine_class="ContestantMatchingEngine",
            submission_path=sub_dir,
            loaded_at=0.0
        )
        
    def get_test_scenario(self):
        return BenchmarkScenario(
            scenario_id="test",
            name="test",
            description="",
            seed=1,
            events=[ScenarioEvent(100, "NewOrderRequest", {"order_id": 1})]
        )

    def test_normal_submission(self):
        manifest = self.create_submission("normal", NORMAL_ENGINE)
        scenario = self.get_test_scenario()
        
        runner = SandboxRunner(SandboxConfig(timeout_seconds=5))
        result = runner.run_submission(manifest, scenario)
        
        self.assertTrue(result.success)
        self.assertFalse(result.crashed)
        self.assertFalse(result.timed_out)
        self.assertIn("Standard output capture test", result.stdout)
        
        # Test Adapter
        adapter = SandboxedContestantAdapter(manifest, SandboxConfig(timeout_seconds=5))
        adapter.submit_order({"order_id": 1})
        snap = adapter.snapshot()
        self.assertIsInstance(snap, EngineSnapshot)
        self.assertIn("TEST", snap.book_snapshots)

    def test_exception_submission(self):
        manifest = self.create_submission("exception", EXCEPTION_ENGINE)
        scenario = self.get_test_scenario()
        
        runner = SandboxRunner(SandboxConfig(timeout_seconds=5))
        result = runner.run_submission(manifest, scenario)
        
        self.assertFalse(result.success)
        self.assertTrue(result.crashed)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exception_type, "RuntimeError")
        self.assertIn("Crash on submit", result.exception_message)

    def test_timeout_submission(self):
        manifest = self.create_submission("timeout", TIMEOUT_ENGINE)
        scenario = self.get_test_scenario()
        
        runner = SandboxRunner(SandboxConfig(timeout_seconds=2))
        result = runner.run_submission(manifest, scenario)
        
        self.assertFalse(result.success)
        self.assertTrue(result.timed_out)

    def test_exit_code_failure(self):
        manifest = self.create_submission("exit", EXIT_CODE_ENGINE)
        scenario = self.get_test_scenario()
        
        runner = SandboxRunner(SandboxConfig(timeout_seconds=5))
        result = runner.run_submission(manifest, scenario)
        
        self.assertFalse(result.success)
        self.assertTrue(result.crashed)

    def test_memory_exhaustion(self):
        manifest = self.create_submission("memory", MEMORY_EXHAUSTION_ENGINE)
        scenario = self.get_test_scenario()
        
        # We only strictly assert failure if on linux where rlimit works.
        runner = SandboxRunner(SandboxConfig(timeout_seconds=5, memory_limit_mb=64))
        result = runner.run_submission(manifest, scenario)
        
        if sys.platform == "linux":
            self.assertFalse(result.success)
            self.assertTrue(result.crashed or result.timed_out)

if __name__ == '__main__':
    unittest.main()
