"""hosting/health_monitor.py

HealthMonitor — background daemon that periodically probes every running
container and publishes DeploymentHealth snapshots.

Phase 4.4.1 probe logic:
    Read container.state directly (in-process state machine).

Phase 5+ upgrade:
    Send a real heartbeat RPC to the container process; if it times out,
    call container.fail() to trigger the FAILED callback chain.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from hosting.container import ContainerInstance, ContainerState
from hosting.health import DeploymentHealth


class HealthMonitor:
    """Periodically scans running containers; fires callbacks on state changes.

    Usage::

        monitor = HealthMonitor(interval_s=5.0)
        monitor.on_failed(lambda c: print(f"{c.container_id} FAILED"))
        monitor.start()
        ...
        monitor.stop()
        snap = monitor.snapshot()
    """

    def __init__(self, interval_s: float = 5.0):
        self.interval_s   = interval_s
        self._containers: Dict[str, ContainerInstance] = {}
        self._health_map: Dict[str, DeploymentHealth]  = {}
        self._lock        = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event  = threading.Event()
        self._on_failed:  List[Callable[[ContainerInstance], None]] = []
        self._on_healthy: List[Callable[[ContainerInstance], None]] = []

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, container: ContainerInstance) -> None:
        with self._lock:
            self._containers[container.container_id] = container

    def deregister(self, container_id: str) -> None:
        with self._lock:
            self._containers.pop(container_id, None)
            self._health_map.pop(container_id, None)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def on_failed(self,  callback: Callable[[ContainerInstance], None]) -> None:
        self._on_failed.append(callback)

    def on_healthy(self, callback: Callable[[ContainerInstance], None]) -> None:
        self._on_healthy.append(callback)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="HealthMonitor"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval_s + 1)

    # ── Public queries ────────────────────────────────────────────────────────

    def snapshot(self) -> List[DeploymentHealth]:
        """Return current DeploymentHealth for all monitored containers."""
        with self._lock:
            return list(self._health_map.values())

    def get_health(self, container_id: str) -> Optional[DeploymentHealth]:
        with self._lock:
            return self._health_map.get(container_id)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._scan()
            self._stop_event.wait(timeout=self.interval_s)

    def _scan(self) -> None:
        now = time.time_ns()

        with self._lock:
            containers = list(self._containers.values())

        for c in containers:
            uptime = (now - c.started_at) if c.started_at else 0
            health = DeploymentHealth(
                submission_id=c.submission_id,
                container_id=c.container_id,
                status=c.state.value,
                uptime_ns=uptime,
                restart_count=c.restart_count,
                failure_count=c.failure_count,
                last_heartbeat=now,
            )

            with self._lock:
                self._health_map[c.container_id] = health

            if c.state == ContainerState.FAILED:
                for cb in self._on_failed:
                    cb(c)
            elif c.state == ContainerState.RUNNING:
                for cb in self._on_healthy:
                    cb(c)
