import unittest
import os
import json
import tempfile
import shutil

from submission.validator import SubmissionValidator
from submission.loader import SubmissionLoader
from submission.registry import SubmissionRegistry
from submission.wrapper import ContestantSubmissionAdapter
from benchmarking.runner import BenchmarkRunner
from benchmarking.scenarios.library import get_simple_fill_scenario
from benchmarking.factory import EngineFactory

class TestSubmissionFramework(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.registry = SubmissionRegistry()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_mock_submission(self, metadata_content=None, engine_content=None, write_metadata=True, write_engine=True):
        sub_dir = os.path.join(self.test_dir, "mock_submission")
        os.makedirs(sub_dir, exist_ok=True)
        
        if write_metadata:
            if metadata_content is None:
                metadata_content = {
                    "team_name": "Test Team",
                    "engine_class": "TestEngine",
                    "version": "1.0"
                }
            if isinstance(metadata_content, dict):
                metadata_content = json.dumps(metadata_content)
                
            with open(os.path.join(sub_dir, "metadata.json"), "w") as f:
                f.write(metadata_content)
                
        if write_engine:
            if engine_content is None:
                engine_content = "class TestEngine:\n    pass\n"
            with open(os.path.join(sub_dir, "engine.py"), "w") as f:
                f.write(engine_content)
                
        return sub_dir

    def test_1_valid_submission(self):
        sub_dir = self._create_mock_submission()
        result = SubmissionValidator.validate(sub_dir)
        self.assertTrue(result.success)
        self.assertEqual(result.metadata.team_name, "Test Team")

    def test_2_missing_metadata(self):
        sub_dir = self._create_mock_submission(write_metadata=False)
        result = SubmissionValidator.validate(sub_dir)
        self.assertFalse(result.success)
        self.assertIn("Missing metadata.json", result.errors)

    def test_3_missing_engine_file(self):
        sub_dir = self._create_mock_submission(write_engine=False)
        result = SubmissionValidator.validate(sub_dir)
        self.assertFalse(result.success)
        self.assertIn("Missing engine.py", result.errors)

    def test_4_missing_engine_class(self):
        sub_dir = self._create_mock_submission(engine_content="class WrongEngine:\n    pass\n")
        result = SubmissionValidator.validate(sub_dir)
        self.assertFalse(result.success)
        self.assertTrue(any("not found in engine.py" in err for err in result.errors))

    def test_5_invalid_metadata(self):
        sub_dir = self._create_mock_submission(metadata_content='{"team_name": "OnlyName"}')
        result = SubmissionValidator.validate(sub_dir)
        self.assertFalse(result.success)
        self.assertTrue(any("missing 'engine_class'" in err for err in result.errors))

    def test_6_successful_dynamic_load(self):
        engine_content = '''
class TestEngine:
    def hello(self):
        return "world"
'''
        sub_dir = self._create_mock_submission(engine_content=engine_content)
        val_result = SubmissionValidator.validate(sub_dir)
        self.assertTrue(val_result.success)
        
        load_result = SubmissionLoader.load(sub_dir, val_result.metadata)
        self.assertTrue(load_result.success)
        self.assertEqual(load_result.engine.hello(), "world")

    def test_7_successful_registry_entry(self):
        sub_id = self.registry.register("Team A", "1.0", "Engine", "/path/to/sub")
        manifest = self.registry.get(sub_id)
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.team_name, "Team A")
        self.assertEqual(len(self.registry.list()), 1)

    def test_8_end_to_end_benchmark_runner_execution(self):
        # We point it to the actual examples/contestant_submission created in Task 4
        sub_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples", "contestant_submission")
        
        val_result = SubmissionValidator.validate(sub_dir)
        self.assertTrue(val_result.success, f"Failed validation: {val_result.errors}")
        
        load_result = SubmissionLoader.load(sub_dir, val_result.metadata)
        self.assertTrue(load_result.success, f"Failed loading: {load_result.errors}")
        adapter = ContestantSubmissionAdapter(load_result.engine)
        
        runner = BenchmarkRunner()
        scenario = get_simple_fill_scenario()
        ref = EngineFactory.create_reference()
        
        result = runner.run(scenario, ref, adapter)
        
        # It's a dummy engine, so it shouldn't get 100% since its snapshot is empty.
        self.assertIsNotNone(result)
        self.assertLess(result.correctness_score, 100.0)

    def test_9_broken_submission_wrong_class_ast_check(self):
        engine_content = "class WrongClass:\n    pass\n"
        metadata_content = {
          "team_name": "Test Team",
          "engine_class": "ContestantMatchingEngine",
          "version": "1.0"
        }
        sub_dir = self._create_mock_submission(metadata_content=metadata_content, engine_content=engine_content)
        result = SubmissionValidator.validate(sub_dir)
        
        self.assertFalse(result.success)
        self.assertTrue(any("not found in engine.py" in err for err in result.errors))

if __name__ == '__main__':
    unittest.main()
