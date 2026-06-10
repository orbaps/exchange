import unittest
from execution.manager import ExecutionManager
from execution.protocol import ExecutionRequest
from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL
from botfleet.events import TradingEvent
from botfleet.events import EventType


def _manifest(sid: str, version: int = 1) -> SubmissionManifest:
    return SubmissionManifest(
        submission_id=sid,
        team_name="TestTeam",
        version=version,
        language=RuntimeType.PYTHON,
        entrypoint="main.py",
        build_command="echo ok",
        run_command="python main.py",
        resource_profile=SMALL,
    )


def _event(eid: str) -> TradingEvent:
    return TradingEvent(eid, 0, "bot1", "BTC-USD", EventType.NEW_ORDER, 10, 100, "BUY", None)


class TestExecutionSessionRouting(unittest.TestCase):
    """Verifies: Worker → ExecutionSession → EndpointRouter → ContainerInstance."""

    def setUp(self):
        self.router = EndpointRouter()
        self.quota  = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        self.cm     = ContainerManager(quota=self.quota, router=self.router)

        # Deploy a container into the hosting layer
        self.manifest  = _manifest("sub_routing_test")
        self.container = self.cm.deploy(self.manifest)

        # Build an ExecutionManager wired to the hosting layer
        self.exec_mgr = ExecutionManager(
            router=self.router,
            container_manager=self.cm,
        )
        self.session = self.exec_mgr.create_session(
            session_id="sess_rt1",
            submission_id="sub_routing_test",
            engine=None,
            sandbox_config={},
        )
        self.session.start()

    def tearDown(self):
        self.cm.destroy(self.container.container_id)

    def test_session_routes_through_running_container(self):
        event   = _event("evt_001")
        request = ExecutionRequest(session_id="sess_rt1", trading_event=event)
        resp    = self.session.execute(request)
        self.assertTrue(resp.success, f"Expected success but got error: {resp.error}")

    def test_session_fails_when_no_route_registered(self):
        # Session for a submission with no container deployed
        orphan = self.exec_mgr.create_session(
            session_id="sess_orphan",
            submission_id="sub_unknown",
            engine=None,
            sandbox_config={},
        )
        orphan.start()
        request = ExecutionRequest(session_id="sess_orphan", trading_event=_event("evt_002"))
        resp    = orphan.execute(request)
        self.assertFalse(resp.success)
        self.assertIn("No route", resp.error)

    def test_session_fails_when_container_stopped(self):
        self.container.stop()
        request = ExecutionRequest(session_id="sess_rt1", trading_event=_event("evt_003"))
        resp    = self.session.execute(request)
        self.assertFalse(resp.success)
        self.assertIn("STOPPED", resp.error)

    def test_legacy_mode_no_router(self):
        """Without a router, session runs in direct/legacy mode and succeeds."""
        legacy_mgr = ExecutionManager()   # no router, no container_manager
        s = legacy_mgr.create_session("sess_legacy", "sub_x", None, {})
        s.start()
        request = ExecutionRequest(session_id="sess_legacy", trading_event=_event("evt_004"))
        resp    = s.execute(request)
        self.assertTrue(resp.success)


if __name__ == "__main__":
    unittest.main()
