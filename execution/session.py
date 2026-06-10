import time
from typing import Any, Dict, Optional
from execution.protocol import ExecutionRequest, ExecutionResponse


class ExecutionSession:
    """Wraps a contestant engine for event execution.

    Phase 4.4 architecture:
        Worker
          ↓
        ExecutionSession.execute()
          ↓
        EndpointRouter.resolve(submission_id)   ← NEW
          ↓
        ContainerInstance (RUNNING check)        ← NEW
          ↓
        Engine logic (currently stubbed)

    The router + container_manager are optional (None = legacy direct mode).
    When supplied, all execution is routed through the hosting layer.
    """

    def __init__(
        self,
        session_id:        str,
        submission_id:     str,
        engine:            Any,
        sandbox_config:    Dict,
        router=None,           # hosting.router.EndpointRouter | None
        container_manager=None # hosting.manager.ContainerManager | None
    ):
        self.session_id        = session_id
        self.submission_id     = submission_id
        self.engine            = engine
        self.sandbox_config    = sandbox_config
        self._router           = router
        self._container_manager = container_manager
        self._running          = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        pass

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Executes one trading event.

        When a router + container_manager are present:
          1. Resolve submission_id → RouteEntry
          2. Confirm the container is RUNNING
          3. Dispatch to engine (stub for Phase 4.4; real IPC in Phase 5+)

        Without router (legacy / test mode):
          Falls straight through to engine stub.
        """
        if not self._running:
            return ExecutionResponse(success=False, latency_ns=0, error="Session not running")

        start_ns = time.time_ns()

        try:
            # ── Hosting-layer routing (Phase 4.4+) ──────────────────────────
            if self._router is not None:
                route = self._router.resolve(self.submission_id)
                if route is None:
                    raise RuntimeError(
                        f"No route registered for submission '{self.submission_id}'"
                    )

                if self._container_manager is not None:
                    # Verify the container is actually alive
                    container = self._container_manager.get(route.container_id)
                    if container is None:
                        raise RuntimeError(
                            f"Container '{route.container_id}' not found in manager"
                        )
                    from hosting.container import ContainerState
                    if container.state != ContainerState.RUNNING:
                        raise RuntimeError(
                            f"Container '{route.container_id}' is {container.state.value}, "
                            f"expected RUNNING"
                        )
                    # endpoint available for Phase 5 IPC: route.endpoint

            # ── Engine dispatch (stub — real IPC in Phase 5+) ───────────────
            # self.engine.process(request.trading_event)
            latency_ns = time.time_ns() - start_ns
            return ExecutionResponse(success=True, latency_ns=latency_ns, error=None)

        except Exception as exc:
            latency_ns = time.time_ns() - start_ns
            return ExecutionResponse(success=False, latency_ns=latency_ns, error=str(exc))
