import threading
import time
import uuid
from typing import Dict, List, Optional

from hosting.container import ContainerInstance, ContainerState
from hosting.deployment_registry import DeploymentRecord, DeploymentRegistry
from hosting.deployment_state import DeploymentState
from hosting.manifest import SubmissionManifest
from hosting.quota import ResourceQuotaManager
from hosting.router import EndpointRouter


class ContainerManager:
    """Central registry and lifecycle controller for all hosted containers.

    Phase 4.4.1 additions:
        - Accepts an optional DeploymentRegistry.
        - deploy() auto-registers a DeploymentRecord and transitions it through
          PENDING → DEPLOYING → RUNNING.
        - destroy() updates the record to TERMINATED.
        - fail_container() updates the record to FAILED.
    """

    def __init__(
        self,
        quota:               ResourceQuotaManager,
        router:              EndpointRouter,
        deployment_registry: Optional[DeploymentRegistry] = None,
    ):
        self._quota               = quota
        self._router              = router
        self._registry            = deployment_registry
        self._containers: Dict[str, ContainerInstance] = {}
        self._dep_by_ctr: Dict[str, str]               = {}   # container_id → deployment_id
        self._lock = threading.Lock()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_dep_status(self, container_id: str, status: DeploymentState, error: str = None) -> None:
        if self._registry is None:
            return
        dep_id = self._dep_by_ctr.get(container_id)
        if dep_id:
            self._registry.update_status(dep_id, status,
                                         end_time=time.time_ns() if status.is_terminal else None,
                                         error=error)

    # ── Deployment ────────────────────────────────────────────────────────────

    def deploy(self, manifest: SubmissionManifest, build_id: str = "") -> ContainerInstance:
        """Allocate quota, create instance, register endpoint, start container.

        Automatically creates a DeploymentRecord if a registry is present.
        State sequence: PENDING → DEPLOYING → RUNNING.
        """
        profile  = manifest.resource_profile
        cid      = f"ctr_{uuid.uuid4().hex[:8]}"
        dep_id   = f"dep_{uuid.uuid4().hex[:8]}"
        endpoint = f"local://submission/{manifest.submission_id}/v{manifest.version}"
        now      = time.time_ns()

        # Register deployment as PENDING
        if self._registry:
            rec = DeploymentRecord(
                deployment_id=dep_id,
                submission_id=manifest.submission_id,
                build_id=build_id,
                container_id=cid,
                status=DeploymentState.PENDING,
                created_at=now,
                updated_at=now,
            )
            self._registry.register(rec)
            self._registry.update_status(dep_id, DeploymentState.DEPLOYING)

        # Allocate quota — raises ValueError if over-capacity
        self._quota.allocate(cid, profile.cpu_limit, profile.memory_limit_mb, profile.disk_limit_mb)

        instance = ContainerInstance(
            container_id=cid,
            submission_id=manifest.submission_id,
            resource_profile=profile,
            endpoint=endpoint,
        )
        instance.start()

        with self._lock:
            self._containers[cid] = instance
            self._dep_by_ctr[cid] = dep_id

        self._router.register(manifest.submission_id, endpoint, cid)

        # Transition → RUNNING
        if self._registry:
            self._registry.update_status(dep_id, DeploymentState.RUNNING)

        return instance

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def stop(self, container_id: str) -> bool:
        with self._lock:
            c = self._containers.get(container_id)
        if c:
            return c.stop()
        return False

    def restart(self, container_id: str) -> bool:
        with self._lock:
            c = self._containers.get(container_id)
        if c:
            return c.restart()
        return False

    def fail_container(self, container_id: str, error: str = "") -> None:
        """Mark a container as failed and update the deployment registry."""
        with self._lock:
            c = self._containers.get(container_id)
        if c:
            c.fail(error)
            self._update_dep_status(container_id, DeploymentState.FAILED, error=error or None)

    def destroy(self, container_id: str) -> bool:
        with self._lock:
            c = self._containers.pop(container_id, None)
        if c is None:
            return False
        c.terminate()
        self._quota.release(container_id)
        self._router.remove(c.submission_id)
        self._update_dep_status(container_id, DeploymentState.TERMINATED)
        with self._lock:
            self._dep_by_ctr.pop(container_id, None)
        return True

    # ── Queries ───────────────────────────────────────────────────────────────

    def get(self, container_id: str) -> Optional[ContainerInstance]:
        with self._lock:
            return self._containers.get(container_id)

    def list_running(self) -> List[ContainerInstance]:
        with self._lock:
            return [c for c in self._containers.values() if c.state == ContainerState.RUNNING]

    def health_check(self) -> List[dict]:
        with self._lock:
            return [c.health() for c in self._containers.values()]
