from dataclasses import dataclass, field
from hosting.runtime import RuntimeType
from hosting.resources import ResourceProfile, MEDIUM


@dataclass
class SubmissionManifest:
    """Canonical descriptor for a contestant submission.

    Versioning is carried here; the registry indexes by (submission_id, version).
    """
    submission_id:    str
    team_name:        str
    version:          int              # monotonically increasing per team
    language:         RuntimeType
    entrypoint:       str
    build_command:    str
    run_command:      str
    resource_profile: ResourceProfile = field(default_factory=lambda: MEDIUM)
    source_path:      str = ""         # local directory containing source code
    notes:            str = ""
