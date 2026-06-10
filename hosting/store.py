import threading
from typing import Dict, List, Optional

from hosting.deployment import DeploymentRecord
from hosting.deployment_state import DeploymentState


class DeploymentStore:
    """Persists and indexes DeploymentRecord objects in memory.

    Provides the full audit trail needed to answer:
        "What happened to submission sub_X3 on run #47?"

    Future: swap the in-memory dict for SQLite or JSONL-backed storage.
    """

    def __init__(self):
        self._records: Dict[str, DeploymentRecord] = {}   # deployment_id → record
        self._by_submission: Dict[str, List[str]]  = {}   # submission_id → [deployment_id]
        self._lock = threading.Lock()

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(self, record: DeploymentRecord) -> None:
        with self._lock:
            self._records[record.deployment_id] = record
            self._by_submission.setdefault(record.submission_id, [])
            if record.deployment_id not in self._by_submission[record.submission_id]:
                self._by_submission[record.submission_id].append(record.deployment_id)

    def update_status(self, deployment_id: str, status: DeploymentState,
                      end_time: Optional[int] = None, error: Optional[str] = None) -> bool:
        with self._lock:
            rec = self._records.get(deployment_id)
            if rec is None:
                return False
            rec.status = status
            if end_time is not None:
                rec.end_time = end_time
            if error is not None:
                rec.error = error
            return True

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentRecord]:
        with self._lock:
            return self._records.get(deployment_id)

    def list_deployments(self, status: Optional[DeploymentState] = None) -> List[DeploymentRecord]:
        """All deployments, optionally filtered by status."""
        with self._lock:
            records = list(self._records.values())
        if status is not None:
            records = [r for r in records if r.status == status]
        return records

    def deployment_history(self, submission_id: str) -> List[DeploymentRecord]:
        """Ordered deployment history for a single submission."""
        with self._lock:
            ids = self._by_submission.get(submission_id, [])
            return [self._records[d] for d in ids if d in self._records]

    def count(self) -> int:
        with self._lock:
            return len(self._records)
