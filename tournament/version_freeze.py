import json
from typing import List
from hosting.manifest import SubmissionManifest
from hosting.artifacts import ArtifactStore
from tournament.submission_lock import SubmissionLock

class VersionFreeze:
    """Freezes versions of all contestants at tournament start."""
    
    def __init__(self, submission_lock: SubmissionLock, artifact_store: ArtifactStore):
        self._lock = submission_lock
        self._store = artifact_store
        
    def freeze(self, tournament_id: str, manifests: List[SubmissionManifest]) -> None:
        """
        Locks the current state of all given manifests for the specified tournament.
        Even if the underlying storage updates these manifests to a higher version, 
        the tournament runner will use these locked snapshots.
        """
        frozen_data = []
        for manifest in manifests:
            self._lock.lock_submission(tournament_id, manifest)
            frozen_data.append({
                "submission_id": manifest.submission_id,
                "team_name": manifest.team_name,
                "version": manifest.version,
                "language": manifest.language.value,
                "entrypoint": manifest.entrypoint,
                "build_command": manifest.build_command,
                "run_command": manifest.run_command,
            })
            
        # Persist frozen_manifest.json per tournament using ArtifactStore
        # We treat tournament_id as the submission_id for storage routing, and version 1.
        self._store.write_json(
            submission_id=tournament_id,
            version=1,
            filename="frozen_manifest.json",
            data={"manifests": frozen_data},
            artifact_type="tournament_freeze"
        )
            
    def get_frozen_manifests(self, tournament_id: str, submission_ids: List[str]) -> List[SubmissionManifest]:
        return [self._lock.get_locked_manifest(tournament_id, sid) for sid in submission_ids]
