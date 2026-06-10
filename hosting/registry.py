import threading
from typing import Dict, List, Optional, Tuple

from hosting.manifest import SubmissionManifest


class SubmissionRegistry:
    """Thread-safe registry supporting per-team version history.

    Internal index: { team_name: { version: SubmissionManifest } }
    Also maintains a flat id → manifest lookup for O(1) retrieval.
    """

    def __init__(self):
        self._by_team: Dict[str, Dict[int, SubmissionManifest]] = {}
        self._by_id:   Dict[str, SubmissionManifest]            = {}
        self._lock = threading.Lock()

    # ── Write ─────────────────────────────────────────────────────────────────

    def register(self, manifest: SubmissionManifest) -> None:
        """Add or overwrite a specific (team, version) entry."""
        with self._lock:
            if manifest.team_name not in self._by_team:
                self._by_team[manifest.team_name] = {}
            self._by_team[manifest.team_name][manifest.version] = manifest
            self._by_id[manifest.submission_id] = manifest

    def update(self, submission_id: str, **kwargs) -> Optional[SubmissionManifest]:
        """Patch arbitrary fields on an existing manifest (returns new object)."""
        with self._lock:
            m = self._by_id.get(submission_id)
            if m is None:
                return None
            import dataclasses
            updated = dataclasses.replace(m, **kwargs)
            self._by_team[updated.team_name][updated.version] = updated
            self._by_id[submission_id] = updated
            return updated

    def remove(self, submission_id: str) -> bool:
        with self._lock:
            m = self._by_id.pop(submission_id, None)
            if m is None:
                return False
            versions = self._by_team.get(m.team_name, {})
            versions.pop(m.version, None)
            return True

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, submission_id: str) -> Optional[SubmissionManifest]:
        return self._by_id.get(submission_id)

    def get_versions(self, team_name: str) -> List[SubmissionManifest]:
        """Return all versions for a team, sorted ascending by version number."""
        with self._lock:
            versions = self._by_team.get(team_name, {})
            return [versions[v] for v in sorted(versions)]

    def latest(self, team_name: str) -> Optional[SubmissionManifest]:
        """Return the highest-version manifest for a team."""
        with self._lock:
            versions = self._by_team.get(team_name, {})
            if not versions:
                return None
            return versions[max(versions)]

    def list_all(self) -> List[SubmissionManifest]:
        with self._lock:
            return list(self._by_id.values())
