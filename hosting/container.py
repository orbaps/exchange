import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from hosting.resources import ResourceProfile


class ContainerState(Enum):
    CREATED    = "CREATED"
    STARTING   = "STARTING"
    RUNNING    = "RUNNING"
    STOPPED    = "STOPPED"
    FAILED     = "FAILED"
    TERMINATED = "TERMINATED"

    @property
    def is_alive(self) -> bool:
        return self in (ContainerState.STARTING, ContainerState.RUNNING)


@dataclass
class ContainerInstance:
    """Represents a single hosted engine process.

    Phase 4.4: lifecycle managed via state machine + mock process handle.
    Phase 5+:  replace _process_handle with Firecracker MicroVM reference.
    """
    container_id:     str
    submission_id:    str
    resource_profile: ResourceProfile
    endpoint:         str           # e.g. local://submission/sub_abc123
    state:            ContainerState = ContainerState.CREATED

    # Operational counters — tracked by ContainerManager
    restart_count:    int = 0
    failure_count:    int = 0
    execution_count:  int = 0
    started_at:       Optional[int] = None     # ns epoch
    stopped_at:       Optional[int] = None

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def start(self) -> bool:
        with self._lock:
            if self.state not in (ContainerState.CREATED, ContainerState.STOPPED):
                return False
            # CREATED/STOPPED → STARTING → RUNNING
            self.state      = ContainerState.STARTING
            self.started_at = time.time_ns()
            self.stopped_at = None
            # Transition immediately to RUNNING (subprocess starts synchronously in Phase 4.4)
            # In Phase 5+ a real process spawn would pause here until health probe passes.
            self.state = ContainerState.RUNNING
            return True

    def stop(self) -> bool:
        with self._lock:
            if self.state != ContainerState.RUNNING:
                return False
            self.state      = ContainerState.STOPPED
            self.stopped_at = time.time_ns()
            return True

    def restart(self) -> bool:
        with self._lock:
            if self.state not in (ContainerState.RUNNING, ContainerState.STOPPED, ContainerState.FAILED):
                return False
            self.state         = ContainerState.RUNNING
            self.started_at    = time.time_ns()
            self.stopped_at    = None
            self.restart_count += 1
            return True

    def fail(self, reason: str = "") -> None:
        with self._lock:
            self.state         = ContainerState.FAILED
            self.stopped_at    = time.time_ns()
            self.failure_count += 1

    def terminate(self) -> None:
        with self._lock:
            self.state      = ContainerState.TERMINATED
            self.stopped_at = time.time_ns()

    def health(self) -> dict:
        return {
            "container_id":  self.container_id,
            "submission_id": self.submission_id,
            "state":         self.state.value,
            "restart_count": self.restart_count,
            "failure_count": self.failure_count,
            "uptime_ns":     (time.time_ns() - self.started_at) if self.started_at else 0,
        }

    def execute(self, request) -> "ExecutionResponse":  # noqa: F821  (forward ref)
        """Dispatch one execution request to the hosted contestant engine.

        Phase 4.4.1:
            - Returns success if the container is RUNNING.
            - Returns failure if the container is in any other state.
            - Real IPC to the contestant process is introduced in Phase 5+.
              At that point replace the body with a socket/pipe call using
              self.endpoint as the address.

        Args:
            request: execution.protocol.ExecutionRequest

        Returns:
            execution.protocol.ExecutionResponse
        """
        from execution.protocol import ExecutionResponse

        if self.state != ContainerState.RUNNING:
            return ExecutionResponse(
                success=False,
                latency_ns=0,
                error=f"Container {self.container_id} is {self.state.value}; expected RUNNING",
            )

        start_ns = time.time_ns()
        try:
            # ── Phase 5+ hook ─────────────────────────────────────────────────
            # Replace the following stub with actual IPC:
            #   result = self._ipc_client.submit(request.trading_event)
            # ──────────────────────────────────────────────────────────────────
            with self._lock:
                self.execution_count += 1
            latency_ns = time.time_ns() - start_ns
            return ExecutionResponse(success=True, latency_ns=latency_ns, error=None)
        except Exception as exc:
            latency_ns = time.time_ns() - start_ns
            return ExecutionResponse(success=False, latency_ns=latency_ns, error=str(exc))
