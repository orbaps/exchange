import threading
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class QuotaAllocation:
    container_id: str
    cpu:       float
    memory_mb: float
    disk_mb:   float


class ResourceQuotaManager:
    """Tracks CPU / Memory / Disk consumption across all active containers.

    Thread-safe. Raises ValueError when an allocation would exceed cluster
    capacity, preventing resource exhaustion with 20+ concurrent submissions.
    """

    def __init__(self, total_cpu: float, total_memory_mb: float, total_disk_mb: float):
        self.total_cpu       = total_cpu
        self.total_memory_mb = total_memory_mb
        self.total_disk_mb   = total_disk_mb

        self._allocations: Dict[str, QuotaAllocation] = {}
        self._lock = threading.Lock()

    # ── Capacity queries ──────────────────────────────────────────────────────

    def used_cpu(self) -> float:
        with self._lock:
            return sum(a.cpu for a in self._allocations.values())

    def used_memory(self) -> float:
        with self._lock:
            return sum(a.memory_mb for a in self._allocations.values())

    def used_disk(self) -> float:
        with self._lock:
            return sum(a.disk_mb for a in self._allocations.values())

    def remaining_cpu(self) -> float:
        return self.total_cpu - self.used_cpu()

    def remaining_memory(self) -> float:
        return self.total_memory_mb - self.used_memory()

    def remaining_disk(self) -> float:
        return self.total_disk_mb - self.used_disk()

    # ── Allocation lifecycle ──────────────────────────────────────────────────

    def allocate(self, container_id: str, cpu: float, memory_mb: float, disk_mb: float) -> QuotaAllocation:
        """Reserve resources for a container. Raises ValueError if capacity exceeded."""
        with self._lock:
            if cpu > (self.total_cpu - sum(a.cpu for a in self._allocations.values())):
                raise ValueError(
                    f"Insufficient CPU: requested {cpu}, "
                    f"available {self.total_cpu - sum(a.cpu for a in self._allocations.values()):.2f}"
                )
            if memory_mb > (self.total_memory_mb - sum(a.memory_mb for a in self._allocations.values())):
                raise ValueError(
                    f"Insufficient memory: requested {memory_mb} MB, "
                    f"available {self.total_memory_mb - sum(a.memory_mb for a in self._allocations.values()):.0f} MB"
                )
            if disk_mb > (self.total_disk_mb - sum(a.disk_mb for a in self._allocations.values())):
                raise ValueError(
                    f"Insufficient disk: requested {disk_mb} MB, "
                    f"available {self.total_disk_mb - sum(a.disk_mb for a in self._allocations.values()):.0f} MB"
                )
            alloc = QuotaAllocation(container_id, cpu, memory_mb, disk_mb)
            self._allocations[container_id] = alloc
            return alloc

    def release(self, container_id: str) -> bool:
        """Free the resources reserved by a container."""
        with self._lock:
            return self._allocations.pop(container_id, None) is not None

    def snapshot(self) -> Dict[str, QuotaAllocation]:
        with self._lock:
            return dict(self._allocations)
