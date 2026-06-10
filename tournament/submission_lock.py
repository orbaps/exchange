from typing import Dict
import copy

from hosting.manifest import SubmissionManifest

class SubmissionLock:
    """Prevents contestants from changing submissions mid-tournament."""
    
    def __init__(self):
        self._locked_submissions: Dict[str, SubmissionManifest] = {}
        
    def lock_submission(self, tournament_id: str, manifest: SubmissionManifest) -> None:
        key = f"{tournament_id}:{manifest.submission_id}"
        # Store a deep copy so external mutations to the original object don't affect the lock
        self._locked_submissions[key] = copy.deepcopy(manifest)
        
    def unlock_submission(self, tournament_id: str, submission_id: str) -> None:
        key = f"{tournament_id}:{submission_id}"
        if key in self._locked_submissions:
            del self._locked_submissions[key]
            
    def get_locked_manifest(self, tournament_id: str, submission_id: str) -> SubmissionManifest:
        key = f"{tournament_id}:{submission_id}"
        if key not in self._locked_submissions:
            raise ValueError(f"Submission {submission_id} is not locked for tournament {tournament_id}")
        return copy.deepcopy(self._locked_submissions[key])
