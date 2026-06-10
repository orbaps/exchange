import time
import unittest
from hosting.deployment import DeploymentRecord
from hosting.deployment_state import DeploymentState
from hosting.store import DeploymentStore


def _record(dep_id: str, sub_id: str, build_id: str, ctr_id: str) -> DeploymentRecord:
    return DeploymentRecord(
        deployment_id=dep_id,
        submission_id=sub_id,
        build_id=build_id,
        container_id=ctr_id,
        start_time=time.time_ns(),
        end_time=None,
        status=DeploymentState.PENDING,
    )


class TestDeploymentStore(unittest.TestCase):

    def test_save_and_get(self):
        store = DeploymentStore()
        rec   = _record("dep1", "sub_A", "bld1", "ctr1")
        store.save(rec)
        self.assertIs(store.get_deployment("dep1"), rec)

    def test_get_missing_returns_none(self):
        store = DeploymentStore()
        self.assertIsNone(store.get_deployment("ghost"))

    def test_update_status(self):
        store = DeploymentStore()
        rec   = _record("dep2", "sub_B", "bld2", "ctr2")
        store.save(rec)

        ok = store.update_status("dep2", DeploymentState.RUNNING)
        self.assertTrue(ok)
        self.assertEqual(store.get_deployment("dep2").status, DeploymentState.RUNNING)

    def test_update_with_end_time_and_error(self):
        store = DeploymentStore()
        rec   = _record("dep3", "sub_C", "bld3", "ctr3")
        store.save(rec)

        now = time.time_ns()
        store.update_status("dep3", DeploymentState.FAILED, end_time=now, error="OOM")
        r = store.get_deployment("dep3")
        self.assertEqual(r.status, DeploymentState.FAILED)
        self.assertEqual(r.error, "OOM")
        self.assertEqual(r.end_time, now)

    def test_list_deployments_all(self):
        store = DeploymentStore()
        for i in range(5):
            store.save(_record(f"dep{i}", f"sub_{i}", f"bld{i}", f"ctr{i}"))
        self.assertEqual(len(store.list_deployments()), 5)

    def test_list_deployments_filtered(self):
        store = DeploymentStore()
        store.save(_record("d1", "s1", "b1", "c1"))
        store.save(_record("d2", "s2", "b2", "c2"))
        store.update_status("d1", DeploymentState.RUNNING)
        running = store.list_deployments(status=DeploymentState.RUNNING)
        self.assertEqual(len(running), 1)
        self.assertEqual(running[0].deployment_id, "d1")

    def test_deployment_history_ordered(self):
        store = DeploymentStore()
        for i in range(3):
            store.save(_record(f"dep_{i}", "sub_shared", f"bld{i}", f"ctr{i}"))
        history = store.deployment_history("sub_shared")
        self.assertEqual(len(history), 3)
        self.assertEqual([r.deployment_id for r in history], ["dep_0", "dep_1", "dep_2"])

    def test_deployment_history_unknown_submission(self):
        store = DeploymentStore()
        self.assertEqual(store.deployment_history("ghost_sub"), [])


if __name__ == "__main__":
    unittest.main()
