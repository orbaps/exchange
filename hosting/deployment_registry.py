import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from hosting.deployment_state import DeploymentState


@dataclass
class DeploymentRecord:
    """Full audit trail linking build → container for one submission run.

    Chain:
        submission_id  ← SubmissionRegistry
        build_id       ← BuildManager
        container_id   ← ContainerManager
        deployment_id  ← synthetic unique key
    """
    deployment_id: str
    submission_id: str
    build_id:      str
    container_id:  str
    status:        DeploymentState
    created_at:    int                  # ns epoch
    updated_at:    int                  # ns epoch
    end_time:      Optional[int] = None
    error:         Optional[str] = None


class DeploymentRegistry:
    """Thread-safe, in-memory deployment registry.

    Supports:
        register()           — store a new DeploymentRecord
        get()                — retrieve by deployment_id
        list()               — all deployments, optionally filtered by status
        list_by_submission() — ordered history for one submission
        latest_deployment()  — most recent record for a submission
        update_status()      — FSM transition with timestamp

    Future: persist to JSONL / SQLite by subclassing or adding a flush() hook.
    """

    def __init__(self):
        self._records:        Dict[str, DeploymentRecord] = {}
        self._by_submission:  Dict[str, List[str]]        = {}   # sub_id → [dep_id ...]
        self._lock = threading.Lock()

    # ── Write ─────────────────────────────────────────────────────────────────

    def register(self, record: DeploymentRecord) -> None:
        with self._lock:
            self._records[record.deployment_id] = record
            self._by_submission.setdefault(record.submission_id, [])
            if record.deployment_id not in self._by_submission[record.submission_id]:
                self._by_submission[record.submission_id].append(record.deployment_id)

    def update_status(
        self,
        deployment_id: str,
        status:        DeploymentState,
        end_time:      Optional[int] = None,
        error:         Optional[str] = None,
    ) -> bool:
        now = time.time_ns()
        with self._lock:
            rec = self._records.get(deployment_id)
            if rec is None:
                return False
            rec.status     = status
            rec.updated_at = now
            if end_time is not None:
                rec.end_time = end_time
            if error is not None:
                rec.error = error
            return True

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, deployment_id: str) -> Optional[DeploymentRecord]:
        with self._lock:
            return self._records.get(deployment_id)

    def list(self, status: Optional[DeploymentState] = None) -> List[DeploymentRecord]:
        with self._lock:
            records = list(self._records.values())
        if status is not None:
            records = [r for r in records if r.status == status]
        return records

    def list_by_submission(self, submission_id: str) -> List[DeploymentRecord]:
        """Insertion-ordered history for a single submission."""
        with self._lock:
            ids = list(self._by_submission.get(submission_id, []))
            return [self._records[d] for d in ids if d in self._records]

    def latest_deployment(self, submission_id: str) -> Optional[DeploymentRecord]:
        """Most recently registered deployment for a submission."""
        history = self.list_by_submission(submission_id)
        return history[-1] if history else None

    def count(self) -> int:
        with self._lock:
            return len(self._records)
