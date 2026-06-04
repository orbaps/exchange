from dataclasses import dataclass

@dataclass
class SubmissionMetadata:
    """Raw metadata parsed from metadata.json."""
    team_name: str
    version: str
    engine_class: str

@dataclass
class SubmissionManifest:
    """Canonical object stored by the SubmissionRegistry."""
    submission_id: str
    team_name: str
    version: str
    engine_class: str
    submission_path: str
    loaded_at: float
