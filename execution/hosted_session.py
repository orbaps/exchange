"""execution/hosted_session.py

HostedExecutionSession — the canonical execution path for Phase 4.4.1+.

Full chain:
    BenchmarkWorker
        ↓
    HostedExecutionSession.execute(request)
        ↓
    EndpointRouter.resolve(submission_id)         → RouteEntry
        ↓
    ContainerManager.get(route.container_id)      → ContainerInstance
        ↓
    ContainerInstance.execute(request)            → ExecutionResponse

This replaces the direct SandboxedContestantAdapter path when the hosting
layer is present.
"""

import time
from typing import Optional

from execution.protocol import ExecutionRequest, ExecutionResponse
from hosting.router import EndpointRouter
from hosting.manager import ContainerManager
from hosting.container import ContainerState


class HostedExecutionSession:
    """Routes every execution request through the hosting layer.

    Unlike ExecutionSession (which accepts an engine object), this class
    holds no direct reference to contestant code.  It communicates purely
    through the EndpointRouter → ContainerManager → ContainerInstance chain.

    Args:
        session_id:        Unique ID for this session (used for tracing).
        submission_id:     The contestant's submission ID to route to.
        router:            EndpointRouter — maps submission_id → RouteEntry.
        container_manager: ContainerManager — fetches ContainerInstance by ID.
    """

    def __init__(
        self,
        session_id:        str,
        submission_id:     str,
        router:            EndpointRouter,
        container_manager: ContainerManager,
    ):
        self.session_id        = session_id
        self.submission_id     = submission_id
        self._router           = router
        self._container_manager = container_manager
        self._running          = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        """No-op for hosted sessions; state lives in the container."""
        pass

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Resolve submission → container → execute.

        Failure modes returned as ExecutionResponse(success=False):
          - Session not started
          - No route registered for submission_id
          - Container not found in manager
          - Container not in RUNNING state
          - Exception during container.execute()
        """
        if not self._running:
            return ExecutionResponse(success=False, latency_ns=0, error="Session not started")

        start_ns = time.time_ns()

        try:
            # Step 1 — resolve submission → endpoint
            route = self._router.resolve(self.submission_id)
            if route is None:
                raise RuntimeError(
                    f"EndpointRouter: no route for submission '{self.submission_id}'"
                )

            # Step 2 — get the live container
            container = self._container_manager.get(route.container_id)
            if container is None:
                raise RuntimeError(
                    f"ContainerManager: container '{route.container_id}' not found"
                )

            if container.state != ContainerState.RUNNING:
                raise RuntimeError(
                    f"Container '{route.container_id}' is {container.state.value}; expected RUNNING"
                )

            # Step 3 — delegate to container (IPC stub → real call in Phase 5+)
            return container.execute(request)

        except Exception as exc:
            latency_ns = time.time_ns() - start_ns
            return ExecutionResponse(success=False, latency_ns=latency_ns, error=str(exc))

    # ── ContestantEngine Duck-Typing (for BenchmarkRunner) ────────────────────

    def _dispatch_event(self, event_type_str: str, payload: dict) -> None:
        from botfleet.events import TradingEvent, EventType
        from execution.protocol import ExecutionRequest

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.NEW_ORDER

        event = TradingEvent(
            event_id=payload.get("order_id", "default_id"),
            timestamp_ns=time.time_ns(),
            bot_id=payload.get("bot_id", "unknown_bot"),
            instrument=payload.get("symbol", "UNKNOWN"),
            event_type=event_type,
            quantity=payload.get("quantity", 0),
            price=payload.get("price", 0),
            side=payload.get("side", "BUY"),
            order_id=payload.get("order_id")
        )
        req = ExecutionRequest(session_id=self.session_id, trading_event=event)
        
        # Dispatch through the hosted path
        resp = self.execute(req)
        if not resp.success:
            raise RuntimeError(f"Execution failed: {resp.error}")

    def submit_order(self, payload: dict) -> None:
        self._dispatch_event("NEW_ORDER", payload)

    def cancel_order(self, payload: dict) -> None:
        self._dispatch_event("CANCEL", payload)

    def replace_order(self, payload: dict) -> None:
        self._dispatch_event("REPLACE", payload)

    def snapshot(self):
        from validation_engine.snapshots import EngineSnapshot
        return EngineSnapshot(book_snapshots={}, order_snapshots={}, trade_snapshots={})
