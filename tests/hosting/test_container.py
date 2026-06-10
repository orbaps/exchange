import unittest
from hosting.container import ContainerInstance, ContainerState
from hosting.resources import SMALL


def _instance(cid: str = "ctr_test") -> ContainerInstance:
    return ContainerInstance(
        container_id=cid,
        submission_id="sub_xyz",
        resource_profile=SMALL,
        endpoint="local://submission/sub_xyz/v1",
    )


class TestContainerLifecycle(unittest.TestCase):

    def test_start(self):
        c = _instance()
        ok = c.start()
        self.assertTrue(ok)
        self.assertEqual(c.state, ContainerState.RUNNING)
        self.assertIsNotNone(c.started_at)

    def test_stop(self):
        c = _instance()
        c.start()
        ok = c.stop()
        self.assertTrue(ok)
        self.assertEqual(c.state, ContainerState.STOPPED)
        self.assertIsNotNone(c.stopped_at)

    def test_restart_increments_count(self):
        c = _instance()
        c.start()
        c.stop()
        ok = c.restart()
        self.assertTrue(ok)
        self.assertEqual(c.restart_count, 1)
        self.assertEqual(c.state, ContainerState.RUNNING)

    def test_crash_recovery_flow(self):
        """Container: RUNNING → FAILED → restart → RUNNING. restart_count increments."""
        c = _instance()
        c.start()
        self.assertEqual(c.state, ContainerState.RUNNING)

        c.fail("OOM")
        self.assertEqual(c.state, ContainerState.FAILED)
        self.assertEqual(c.failure_count, 1)

        ok = c.restart()
        self.assertTrue(ok)
        self.assertEqual(c.state, ContainerState.RUNNING)
        self.assertEqual(c.restart_count, 1)

    def test_multiple_crashes_accumulate(self):
        c = _instance()
        c.start()
        for i in range(3):
            c.fail()
            c.restart()
        self.assertEqual(c.failure_count, 3)
        self.assertEqual(c.restart_count, 3)

    def test_terminate(self):
        c = _instance()
        c.start()
        c.terminate()
        self.assertEqual(c.state, ContainerState.TERMINATED)

    def test_health_dict(self):
        c = _instance()
        c.start()
        h = c.health()
        self.assertEqual(h["state"], "RUNNING")
        self.assertIn("restart_count", h)
        self.assertIn("uptime_ns", h)


if __name__ == "__main__":
    unittest.main()
