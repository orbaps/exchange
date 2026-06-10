import os
import unittest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL
from hosting.manifest import SubmissionManifest
from hosting.artifacts import ArtifactStore
from hosting.build import BuildManager, BuildStatus


def _manifest(sid: str, cmd: str = "echo build_ok") -> SubmissionManifest:
    return SubmissionManifest(
        submission_id=sid,
        team_name="TeamX",
        version=1,
        language=RuntimeType.PYTHON,
        entrypoint="main.py",
        build_command=cmd,
        run_command="python main.py",
        resource_profile=SMALL,
        source_path=".",
    )


class TestBuildManager(unittest.TestCase):

    def setUp(self):
        self.store   = ArtifactStore(root="test_artifacts_build")
        self.manager = BuildManager(self.store)

    def tearDown(self):
        import shutil
        if os.path.isdir("test_artifacts_build"):
            shutil.rmtree("test_artifacts_build")

    def test_successful_build(self):
        m      = _manifest("sub_build_ok")
        result = self.manager.build(m)
        self.assertEqual(result.status, BuildStatus.SUCCESS)
        self.assertGreater(result.duration_ms, 0)
        self.assertTrue(os.path.exists(result.artifact_path))

    def test_failed_build(self):
        # command that exits non-zero
        m      = _manifest("sub_build_fail", cmd="exit 1")
        result = self.manager.build(m)
        self.assertEqual(result.status, BuildStatus.FAILED)
        self.assertIsNotNone(result.error)

    def test_build_history(self):
        m1 = _manifest("sub_hist1")
        m2 = _manifest("sub_hist2")
        r1 = self.manager.build(m1)
        r2 = self.manager.build(m2)
        all_r = self.manager.all_results()
        self.assertEqual(len(all_r), 2)
        self.assertIsNotNone(self.manager.get_result(r1.build_id))
        self.assertIsNotNone(self.manager.get_result(r2.build_id))

    def test_executor_split(self):
        """Verify BuildExecutor is separate from BuildManager."""
        from hosting.build import BuildExecutor
        self.assertIsInstance(self.manager._executor, BuildExecutor)


if __name__ == "__main__":
    unittest.main()
