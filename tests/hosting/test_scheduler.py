import unittest
from hosting.quota import ResourceQuotaManager
from hosting.resources import SMALL, MEDIUM
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.scheduler import DeploymentScheduler


def _manifest(sid: str, profile=SMALL) -> SubmissionManifest:
    return SubmissionManifest(
        submission_id=sid,
        team_name="T",
        version=1,
        language=RuntimeType.PYTHON,
        entrypoint="main.py",
        build_command="echo ok",
        run_command="python main.py",
        resource_profile=profile,
    )


class TestDeploymentScheduler(unittest.TestCase):

    def test_can_deploy_ok(self):
        quota     = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        scheduler = DeploymentScheduler(quota, max_active_containers=5)
        ok, reason = scheduler.can_deploy(_manifest("sub1", SMALL))   # needs 1 CPU
        self.assertTrue(ok)

    def test_max_active_containers_blocks(self):
        quota     = ResourceQuotaManager(total_cpu=100, total_memory_mb=102400, total_disk_mb=1024000)
        scheduler = DeploymentScheduler(quota, max_active_containers=2)
        scheduler.acquire_slot()
        scheduler.acquire_slot()
        ok, reason = scheduler.can_deploy(_manifest("sub_x"))
        self.assertFalse(ok)
        self.assertIn("Max active", reason)

    def test_slot_release(self):
        quota     = ResourceQuotaManager(total_cpu=100, total_memory_mb=102400, total_disk_mb=1024000)
        scheduler = DeploymentScheduler(quota, max_active_containers=1)
        ok1, _    = scheduler.can_deploy(_manifest("s1"))
        scheduler.acquire_slot()
        ok2, _    = scheduler.can_deploy(_manifest("s2"))
        self.assertFalse(ok2)
        scheduler.release_slot()
        ok3, _    = scheduler.can_deploy(_manifest("s3"))
        self.assertTrue(ok3)

    def test_active_count_property(self):
        quota     = ResourceQuotaManager(total_cpu=100, total_memory_mb=102400, total_disk_mb=1024000)
        scheduler = DeploymentScheduler(quota)
        self.assertEqual(scheduler.active_count, 0)
        scheduler.acquire_slot()
        scheduler.acquire_slot()
        self.assertEqual(scheduler.active_count, 2)


if __name__ == "__main__":
    unittest.main()
