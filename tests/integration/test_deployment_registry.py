import time
import unittest

from hosting.deployment_registry import DeploymentRegistry, DeploymentRecord
from hosting.deployment_state import DeploymentState


class TestDeploymentRegistryIntegration(unittest.TestCase):

    def test_register_and_history(self):
        registry = DeploymentRegistry()
        
        now = time.time_ns()
        r1 = DeploymentRecord(
            deployment_id="dep_1",
            submission_id="sub_test",
            build_id="bld_1",
            container_id="ctr_1",
            status=DeploymentState.RUNNING,
            created_at=now,
            updated_at=now
        )
        registry.register(r1)
        
        r2 = DeploymentRecord(
            deployment_id="dep_2",
            submission_id="sub_test",
            build_id="bld_2",
            container_id="ctr_2",
            status=DeploymentState.PENDING,
            created_at=now + 1000,
            updated_at=now + 1000
        )
        registry.register(r2)

        history = registry.list_by_submission("sub_test")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].deployment_id, "dep_1")
        self.assertEqual(history[1].deployment_id, "dep_2")

        latest = registry.latest_deployment("sub_test")
        self.assertEqual(latest.deployment_id, "dep_2")
        
        registry.update_status("dep_2", DeploymentState.RUNNING)
        self.assertEqual(registry.get("dep_2").status, DeploymentState.RUNNING)


if __name__ == "__main__":
    unittest.main()
