from dataclasses import dataclass, field
from typing import Optional, List, Any
from submission.metadata import SubmissionMetadata

@dataclass
class SubmissionLoadResult:
    """The result of attempting to validate and load a contestant submission."""
    success: bool
    metadata: Optional[SubmissionMetadata] = None
    errors: List[str] = field(default_factory=list)
    engine: Optional[Any] = None
