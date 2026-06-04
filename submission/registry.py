import time
import uuid
from typing import Dict, List, Optional
from submission.metadata import SubmissionManifest

class SubmissionRegistry:
    """In-memory tracking of loaded submissions."""
    
    def __init__(self):
        self._submissions: Dict[str, SubmissionManifest] = {}
        
    def register(self, team_name: str, version: str, engine_class: str, submission_path: str) -> str:
        """Registers a submission and returns its unique ID."""
        submission_id = str(uuid.uuid4())
        manifest = SubmissionManifest(
            submission_id=submission_id,
            team_name=team_name,
            version=version,
            engine_class=engine_class,
            submission_path=submission_path,
            loaded_at=time.time()
        )
        self._submissions[submission_id] = manifest
        return submission_id
        
    def get(self, submission_id: str) -> Optional[SubmissionManifest]:
        """Retrieves a registered submission by ID."""
        return self._submissions.get(submission_id)
        
    def list(self) -> List[SubmissionManifest]:
        """Lists all registered submissions."""
        return list(self._submissions.values())
