import time
import threading
import unittest
from hosting.container import ContainerInstance, ContainerState
from hosting.monitor import HealthMonitor
from hosting.resources import SMALL


def _instance(cid: str) -> ContainerInstance:
    return ContainerInstance(
        container_id=cid,
        submission_id=f"sub_{cid}",
        resource_profile=SMALL,
        endpoint=f"local://submission/sub_{cid}/v1",
    )


class TestHealthMonitor(unittest.TestCase):

    def test_scan_detects_failed_container(self):
        monitor = HealthMonitor(interval_s=60)  # long interval — we call _scan() directly

        failed_callbacks = []
        monitor.on_failed(lambda c: failed_callbacks.append(c.container_id))

        c = _instance("ctr_x")
        c.start()
        c.fail("OOM")

        monitor.register(c)
        monitor._scan()

        self.assertIn("ctr_x", failed_callbacks)

    def test_scan_fires_healthy_callback(self):
        monitor = HealthMonitor(interval_s=60)

        healthy = []
        monitor.on_healthy(lambda c: healthy.append(c.container_id))

        c = _instance("ctr_y")
        c.start()
        monitor.register(c)
        monitor._scan()

        self.assertIn("ctr_y", healthy)

    def test_deregister_removes_from_scan(self):
        monitor = HealthMonitor(interval_s=60)
        callbacks = []
        monitor.on_failed(lambda c: callbacks.append(c.container_id))

        c = _instance("ctr_z")
        c.start()
        c.fail()
        monitor.register(c)
        monitor.deregister("ctr_z")
        monitor._scan()

        self.assertEqual(callbacks, [])

    def test_background_thread_starts_and_stops(self):
        monitor = HealthMonitor(interval_s=0.05)
        monitor.start()
        self.assertTrue(monitor._thread.is_alive())
        monitor.stop()
        self.assertFalse(monitor._thread.is_alive())

    def test_snapshot(self):
        monitor = HealthMonitor(interval_s=60)
        c = _instance("ctr_snap")
        c.start()
        monitor.register(c)
        snap = monitor.snapshot()
        self.assertEqual(len(snap), 1)
        self.assertEqual(snap[0]["container_id"], "ctr_snap")


if __name__ == "__main__":
    unittest.main()
