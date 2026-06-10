import threading
from typing import Tuple

from hosting.manifest import SubmissionManifest
from hosting.quota import ResourceQuotaManager


class DeploymentScheduler:
    """Gates concurrent deployments to prevent resource exhaustion.

    Enforces:
      max_active_containers — hard cap on simultaneous running containers
      Quota pre-flight check via ResourceQuotaManager.remaining_*()

    Callers enqueue() a manifest; the scheduler dequeues when a slot is free.
    """

    def __init__(
        self,
        quota: ResourceQuotaManager,
        max_active_containers: int = 10,
        max_concurrent_builds: int = 4,
    ):
        self._quota                 = quota
        self.max_active_containers  = max_active_containers
        self.max_concurrent_builds  = max_concurrent_builds
        self._active_count = 0
        self._build_count  = 0
        self._lock         = threading.Lock()

    def can_deploy(self, manifest: SubmissionManifest) -> Tuple[bool, str]:
        """Pre-flight: returns (ok, reason)."""
        profile = manifest.resource_profile
        with self._lock:
            if self._active_count >= self.max_active_containers:
                return False, f"Max active containers reached ({self.max_active_containers})"
            if self._quota.remaining_cpu() < profile.cpu_limit:
                return False, (f"Insufficient CPU: need {profile.cpu_limit}, "
                               f"remaining {self._quota.remaining_cpu():.2f}")
            if self._quota.remaining_memory() < profile.memory_limit_mb:
                return False, (f"Insufficient memory: need {profile.memory_limit_mb} MB, "
                               f"remaining {self._quota.remaining_memory():.0f} MB")
        return True, ""

    def acquire_slot(self) -> bool:
        with self._lock:
            if self._active_count >= self.max_active_containers:
                return False
            self._active_count += 1
            return True

    def release_slot(self) -> None:
        with self._lock:
            if self._active_count > 0:
                self._active_count -= 1

    def acquire_build_slot(self) -> bool:
        with self._lock:
            if self._build_count >= self.max_concurrent_builds:
                return False
            self._build_count += 1
            return True

    def release_build_slot(self) -> None:
        with self._lock:
            if self._build_count > 0:
                self._build_count -= 1

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._active_count
