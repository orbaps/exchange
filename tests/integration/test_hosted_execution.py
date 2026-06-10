import unittest

from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL

from execution.hosted_session import HostedExecutionSession
from execution.protocol import ExecutionRequest
from botfleet.events import TradingEvent, EventType


class TestHostedExecutionIntegration(unittest.TestCase):

    def test_hosted_execution_flow(self):
        # 1. Setup Hosting Layer
        quota = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        cm = ContainerManager(quota, router)

        manifest = SubmissionManifest(
            submission_id="sub_hosted",
            team_name="TeamHosted",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        )

        # 2. Deploy Container
        container = cm.deploy(manifest)

        # 3. Setup Execution Session matching the architecture
        session = HostedExecutionSession(
            session_id="sess_1",
            submission_id="sub_hosted",
            router=router,
            container_manager=cm,
        )
        session.start()

        # 4. Dispatch ExecutionRequest
        evt = TradingEvent(
            event_id="e1", 
            timestamp_ns=0, 
            bot_id="b1", 
            instrument="BTC-USD", 
            event_type=EventType.NEW_ORDER, 
            price=10, 
            quantity=100, 
            side="BUY", 
            order_id=None
        )
        req = ExecutionRequest(session_id="sess_1", trading_event=evt)

        # 5. Verify flow through ContainerInstance.execute()
        resp = session.execute(req)
        self.assertTrue(resp.success, resp.error)
        self.assertGreater(container.execution_count, 0, "Container execute() was not called")

        # 6. Teardown
        cm.destroy(container.container_id)

    def test_route_removed_during_execution(self):
        quota = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        cm = ContainerManager(quota, router)

        manifest = SubmissionManifest(
            submission_id="sub_route_drop",
            team_name="TeamA",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        )
        container = cm.deploy(manifest)

        session = HostedExecutionSession("sess_drop", "sub_route_drop", router, cm)
        session.start()

        # Remove route
        router.remove("sub_route_drop")

        evt = TradingEvent("e2", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)
        req = ExecutionRequest(session_id="sess_drop", trading_event=evt)
        resp = session.execute(req)

        self.assertFalse(resp.success)
        self.assertIn("no route for submission", resp.error)

    def test_container_restart_during_session(self):
        quota = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        cm = ContainerManager(quota, router)

        manifest = SubmissionManifest(
            submission_id="sub_restart",
            team_name="TeamB",
            version=1,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="echo skip",
            run_command="python main.py",
            resource_profile=SMALL,
        )
        container = cm.deploy(manifest)

        session = HostedExecutionSession("sess_restart", "sub_restart", router, cm)
        session.start()

        evt = TradingEvent("e3", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)
        req = ExecutionRequest(session_id="sess_restart", trading_event=evt)
        
        resp1 = session.execute(req)
        self.assertTrue(resp1.success)

        # Restart container
        cm.restart(container.container_id)

        resp2 = session.execute(req)
        self.assertTrue(resp2.success)
        self.assertEqual(container.restart_count, 1)

    def test_multiple_hosted_sessions(self):
        quota = ResourceQuotaManager(total_cpu=16, total_memory_mb=8192, total_disk_mb=32768)
        router = EndpointRouter()
        cm = ContainerManager(quota, router)

        teams = ["TeamC", "TeamD", "TeamE"]
        sessions = []
        containers = []

        for team in teams:
            manifest = SubmissionManifest(
                submission_id=f"sub_{team}",
                team_name=team,
                version=1,
                language=RuntimeType.PYTHON,
                entrypoint="main.py",
                build_command="echo skip",
                run_command="python main.py",
                resource_profile=SMALL,
            )
            ctr = cm.deploy(manifest)
            containers.append(ctr)

            sess = HostedExecutionSession(f"sess_{team}", f"sub_{team}", router, cm)
            sess.start()
            sessions.append(sess)

        # Execute requests for all
        evt = TradingEvent("e4", 0, "b1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)
        
        for sess, ctr in zip(sessions, containers):
            req = ExecutionRequest(session_id=sess.session_id, trading_event=evt)
            resp = sess.execute(req)
            self.assertTrue(resp.success)
            self.assertEqual(ctr.execution_count, 1)


if __name__ == "__main__":
    unittest.main()
