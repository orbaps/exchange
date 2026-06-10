import threading
import time
from typing import Callable, Dict, List, Optional

from hosting.container import ContainerInstance, ContainerState


class HealthMonitor:
    """Periodically scans running containers and fires callbacks on state changes.

    Runs as a daemon thread — stops automatically when the main process exits.
    Phase 4.4: detects FAILED state by checking container.state directly.
    Phase 5+:  replace the health probe body with a real process liveness check
               (e.g. sending a heartbeat RPC to the hosted engine).

    Usage::

        monitor = HealthMonitor(interval_s=5.0)
        monitor.on_failed(lambda c: print(f"{c.container_id} is FAILED"))
        monitor.start()
        ...
        monitor.stop()
    """

    def __init__(self, interval_s: float = 5.0):
        self.interval_s   = interval_s
        self._containers: Dict[str, ContainerInstance] = {}
        self._lock        = threading.Lock()
        self._thread:     Optional[threading.Thread]   = None
        self._stop_event  = threading.Event()

        # Callbacks
        self._on_failed:  List[Callable[[ContainerInstance], None]] = []
        self._on_healthy: List[Callable[[ContainerInstance], None]] = []

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, container: ContainerInstance) -> None:
        with self._lock:
            self._containers[container.container_id] = container

    def deregister(self, container_id: str) -> None:
        with self._lock:
            self._containers.pop(container_id, None)

    def on_failed(self, callback: Callable[[ContainerInstance], None]) -> None:
        self._on_failed.append(callback)

    def on_healthy(self, callback: Callable[[ContainerInstance], None]) -> None:
        self._on_healthy.append(callback)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="HealthMonitor")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval_s + 1)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._scan()
            self._stop_event.wait(timeout=self.interval_s)

    def _scan(self) -> None:
        with self._lock:
            containers = list(self._containers.values())

        for c in containers:
            if c.state == ContainerState.FAILED:
                for cb in self._on_failed:
                    cb(c)
            elif c.state == ContainerState.RUNNING:
                for cb in self._on_healthy:
                    cb(c)

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> List[dict]:
        with self._lock:
            return [c.health() for c in self._containers.values()]
