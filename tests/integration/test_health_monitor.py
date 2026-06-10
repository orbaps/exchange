import time
import unittest

from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.health_monitor import HealthMonitor
from hosting.deployment_registry import DeploymentRegistry
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL
from hosting.deployment_state import DeploymentState


class TestHealthMonitorIntegration(unittest.TestCase):

    def test_health_monitor_detects_crash_and_updates_registry(self):
        # 1. Setup Hosting
        quota = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        registry = DeploymentRegistry()
        cm = ContainerManager(quota, router, registry)

        monitor = HealthMonitor(interval_s=0.1)

        manifest = SubmissionManifest(
            submission_id="sub_crash",
            team_name="CrashTeam",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        )

        # 2. Deploy Container
        container = cm.deploy(manifest)
        monitor.register(container)
        
        detected_failures = []
        monitor.on_failed(lambda c: detected_failures.append(c.container_id))

        monitor.start()

        # 3. Simulate a crash via ContainerManager
        cm.fail_container(container.container_id, error="OOM")

        # Give monitor a chance to scan
        time.sleep(0.3)
        monitor.stop()

        # 4. Verify monitor detected it
        self.assertIn(container.container_id, detected_failures)
        
        # 5. Verify registry was correctly updated
        latest = registry.latest_deployment("sub_crash")
        self.assertEqual(latest.status, DeploymentState.FAILED)
        self.assertEqual(latest.error, "OOM")

if __name__ == "__main__":
    unittest.main()
