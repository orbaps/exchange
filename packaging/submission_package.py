"""Submission package generator for competition delivery.

Produces a deterministic final_submission_package manifest
with SHA-256 fingerprinting for bit-for-bit reproducibility.
"""

from federation.clock import DeterministicClock
from typing import Dict, Any, List
import hashlib
import json


class SubmissionPackage:
    """Generates a deterministic competition submission package.

    Args:
        clock: DeterministicClock instance for timestamping the package.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate(self, artifact_fingerprints: List[str]) -> Dict[str, Any]:
        """Generate the final submission package.

        Args:
            artifact_fingerprints: List of SHA-256 hashes of included artifacts.

        Returns:
            Dict with package_id, artifacts, artifact_count, timestamp,
            and a SHA-256 fingerprint of the entire package.
        """
        now = self.clock.now()
        # Sort to ensure deterministic ordering
        sorted_fps = sorted(artifact_fingerprints)
        result = {
            "package_id": f"submission_{now}",
            "artifacts": sorted_fps,
            "artifact_count": len(sorted_fps),
            "timestamp": now
        }
        result_str = json.dumps(result, sort_keys=True)
        result["fingerprint"] = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
        return result
